import json
import logging
import asyncio
import time
import numpy as np
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, PUBLIC_HOST, SESSION_TIMEOUT
from pipeline.session import SessionManager, CallSession, SessionState
from pipeline.coordinator import PipelineCoordinator
from telephony.barge_in import BargeInDetector

logger = logging.getLogger(__name__)

router = APIRouter()
session_manager = SessionManager()
coordinator = PipelineCoordinator(session_manager)


@router.post("/voice")
async def twilio_voice_webhook(request: Request):
    """
    Twilio calls this when a call comes in. Returns TwiML to connect media stream.
    Extracts caller info from Twilio's POST form data and passes it as custom
    parameters to the media stream WebSocket.
    """
    host = PUBLIC_HOST

    # Extract caller info from Twilio's POST form data
    form = await request.form()
    from_number = form.get("From", "")
    to_number = form.get("To", "")
    caller_name = form.get("CallerName", "")
    caller_city = form.get("CallerCity", "")
    caller_state = form.get("CallerState", "")
    caller_country = form.get("CallerCountry", "")
    call_sid = form.get("CallSid", "")

    logger.info(f"Incoming call: from={from_number} to={to_number} "
                f"caller_name='{caller_name}' city={caller_city} "
                f"state={caller_state} country={caller_country} sid={call_sid}")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi">Welcome to the complaint helpline. Please describe your issue after the beep.</Say>
    <Connect>
        <Stream url="wss://{host}/twilio/media">
            <Parameter name="callerNumber" value="{from_number}"/>
            <Parameter name="callerName" value="{caller_name}"/>
            <Parameter name="callerCity" value="{caller_city}"/>
            <Parameter name="callerState" value="{caller_state}"/>
            <Parameter name="callerCountry" value="{caller_country}"/>
        </Stream>
    </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.websocket("/media")
async def twilio_media_stream(websocket: WebSocket):
    """Bidirectional media stream: receive caller audio, send TTS audio back."""
    await websocket.accept()
    call_sid = None
    stream_sid = None
    session = None
    audio_buffer = bytearray()
    barge_in = BargeInDetector()
    is_sending_tts = False

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)

            if data["event"] == "connected":
                logger.info("Twilio media stream connected")

            elif data["event"] == "start":
                call_sid = data["start"]["callSid"]
                stream_sid = data["start"].get("streamSid")
                session = session_manager.create_session(call_sid)

                # Extract caller info from custom parameters
                custom_params = data["start"].get("customParameters", {})
                session.caller_phone = custom_params.get("callerNumber", "")
                session.caller_name = custom_params.get("callerName", "")
                session.caller_city = custom_params.get("callerCity", "")
                session.caller_state = custom_params.get("callerState", "")
                session.caller_country = custom_params.get("callerCountry", "")

                logger.info(f"[{call_sid}] Call started | stream={stream_sid} "
                            f"phone={session.caller_phone} name='{session.caller_name}' "
                            f"location={session.caller_city},{session.caller_state},{session.caller_country}")

            elif data["event"] == "media":
                if not session:
                    continue

                from telephony.audio_utils import decode_twilio_audio, encode_twilio_audio, pcm16_to_float32

                inbound_audio = decode_twilio_audio(data["media"]["payload"])
                inbound_float = pcm16_to_float32(inbound_audio)

                # Check for barge-in: user speaking while TTS is playing
                barge_in.set_tts_playing(is_sending_tts)
                if barge_in.process_inbound(inbound_float):
                    logger.info(f"[{call_sid}] Barge-in detected")
                    is_sending_tts = False
                    audio_buffer.clear()
                    continue

                audio_buffer.extend(inbound_audio)

                # Accumulate ~2 seconds of audio before processing
                if len(audio_buffer) >= 64000:  # ~2 seconds at 16kHz * 2 bytes
                    chunk_start = time.time()
                    audio_float = pcm16_to_float32(bytes(audio_buffer))

                    try:
                        from agents.stt_client import transcribe_audio
                        stt_result = await transcribe_audio(audio_float)
                    except Exception as e:
                        logger.error(f"[{call_sid}] STT error: {e}", exc_info=True)
                        audio_buffer.clear()
                        continue

                    if stt_result and stt_result.get("text", "").strip():
                        text = stt_result["text"].strip()
                        confidence = stt_result.get("confidence", 0)
                        stt_ms = round((time.time() - chunk_start) * 1000)
                        logger.info(f"[{call_sid}] STT: '{text}' confidence={confidence:.2f} ({stt_ms}ms)")

                        process_start = time.time()
                        result = await coordinator.process_text(text, session)
                        process_ms = round((time.time() - process_start) * 1000)
                        logger.info(f"[{call_sid}] Pipeline: state={result.get('state')} ({process_ms}ms)")

                        if result and result.get("tts_text"):
                            try:
                                from tts import synthesize_speech
                                tts_start = time.time()
                                tts_text = result["tts_text"]
                                logger.info(f"[{call_sid}] TTS text: '{tts_text[:100]}...'")
                                audio_pcm = await synthesize_speech(tts_text)
                                tts_ms = round((time.time() - tts_start) * 1000)

                                if audio_pcm:
                                    is_sending_tts = True
                                    twilio_payload = encode_twilio_audio(audio_pcm)
                                    if not stream_sid:
                                        logger.error(f"[{call_sid}] Missing streamSid, cannot send audio")
                                        is_sending_tts = False
                                        audio_buffer.clear()
                                        continue
                                    await websocket.send_text(json.dumps({
                                        "event": "media",
                                        "streamSid": stream_sid,
                                        "media": {"payload": twilio_payload}
                                    }))
                                    total_ms = round((time.time() - chunk_start) * 1000)
                                    logger.info(f"[{call_sid}] Sent TTS {len(audio_pcm)}B ({tts_ms}ms) | total_latency={total_ms}ms")
                                    is_sending_tts = False
                                else:
                                    logger.warning(f"[{call_sid}] TTS returned empty audio")
                            except Exception as e:
                                logger.error(f"[{call_sid}] TTS error: {e}", exc_info=True)
                                is_sending_tts = False

                    audio_buffer.clear()

            elif data["event"] == "stop":
                logger.info(f"[{call_sid}] Call ended | "
                            f"turns={session.turn_count if session else '?'} "
                            f"state={session.state.value if session else '?'} "
                            f"duration={round(time.time()-session.created_at) if session else '?'}s "
                            f"ticket={session.ticket_id if session else '?'}")
                if session:
                    session_manager.close_session(call_sid)
                break

    except WebSocketDisconnect:
        logger.info(f"[{call_sid}] WebSocket disconnected")
        if session and call_sid:
            session_manager.close_session(call_sid)
    except Exception as e:
        logger.error(f"[{call_sid}] Media stream error: {e}", exc_info=True)
        if session and call_sid:
            session_manager.close_session(call_sid)
