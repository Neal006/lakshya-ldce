import json
import logging
import asyncio
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
    """Twilio calls this when a call comes in. Returns TwiML to connect media stream."""
    host = PUBLIC_HOST
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi">Welcome to the complaint helpline. Please describe your issue after the beep.</Say>
    <Connect>
        <Stream url="wss://{host}/twilio/media" />
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
                logger.info(f"Call started: {call_sid}, stream: {stream_sid}")

            elif data["event"] == "media":
                if not session:
                    continue

                from telephony.audio_utils import decode_twilio_audio, encode_twilio_audio, pcm16_to_float32

                inbound_audio = decode_twilio_audio(data["media"]["payload"])
                inbound_float = pcm16_to_float32(inbound_audio)

                # Check for barge-in: user speaking while TTS is playing
                barge_in.set_tts_playing(is_sending_tts)
                if barge_in.process_inbound(inbound_float):
                    logger.info(f"Barge-in detected for {call_sid}")
                    is_sending_tts = False
                    audio_buffer.clear()
                    # Don't process the interrupted audio — wait for next chunk
                    continue

                audio_buffer.extend(inbound_audio)

                # Accumulate ~2 seconds of audio before processing
                if len(audio_buffer) >= 64000:  # ~2 seconds at 16kHz * 2 bytes
                    audio_float = pcm16_to_float32(bytes(audio_buffer))

                    try:
                        from agents.stt_client import transcribe_audio
                        stt_result = await transcribe_audio(audio_float)
                    except Exception as e:
                        logger.error(f"STT error: {e}")
                        audio_buffer.clear()
                        continue

                    if stt_result and stt_result.get("text", "").strip():
                        text = stt_result["text"].strip()
                        logger.info(f"STT: {text} (confidence: {stt_result.get('confidence', 0):.2f})")

                        result = await coordinator.process_text(text, session)

                        if result and result.get("tts_text"):
                            try:
                                from tts import synthesize_speech
                                logger.info(f"TTS text for {call_sid}: {result['tts_text']}")
                                audio_pcm = await synthesize_speech(result["tts_text"])
                                if audio_pcm:
                                    is_sending_tts = True
                                    twilio_payload = encode_twilio_audio(audio_pcm)
                                    if not stream_sid:
                                        logger.error(f"Missing streamSid for {call_sid}; cannot send audio back to Twilio")
                                        is_sending_tts = False
                                        audio_buffer.clear()
                                        continue
                                    await websocket.send_text(json.dumps({
                                        "event": "media",
                                        "streamSid": stream_sid,
                                        "media": {"payload": twilio_payload}
                                    }))
                                    logger.info(f"Sent {len(audio_pcm)} bytes of TTS audio to Twilio for {call_sid}")
                                    is_sending_tts = False
                                else:
                                    logger.warning(f"TTS synthesis returned empty audio for {call_sid}")
                            except Exception as e:
                                logger.error(f"TTS error: {e}")
                                is_sending_tts = False

                    audio_buffer.clear()

            elif data["event"] == "stop":
                logger.info(f"Call ended: {call_sid}")
                if session:
                    session_manager.close_session(call_sid)
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {call_sid}")
        if session and call_sid:
            session_manager.close_session(call_sid)
    except Exception as e:
        logger.error(f"Media stream error: {e}")
        if session and call_sid:
            session_manager.close_session(call_sid)
