import edge_tts
import logging
from config import TTS_VOICE, EDGE_TTS_VOICE_MAP

logger = logging.getLogger(__name__)


async def synthesize(text: str, voice: str = None) -> bytes:
    """
    Synthesize text using Edge TTS (Microsoft, cloud).
    Older edge-tts can return raw PCM16 at 16 kHz. Current edge-tts (6.2+) streams
    MP3 (audio-24khz-48kbitrate-mono-mp3); that must be decoded to PCM16 16 kHz
    before Twilio encoding — otherwise the call hears noise.
    """
    voice = voice or TTS_VOICE
    voice_name = EDGE_TTS_VOICE_MAP.get(voice, "en-IN-NeerjaNeural")

    try:
        # edge-tts changed its API over time. Some versions accept `codec=...`,
        # others don't. Prefer raw PCM when available; otherwise we get MP3 bytes.
        used_raw_pcm_codec = False
        try:
            communicator = edge_tts.Communicate(
                text,
                voice_name,
                codec="raw-16khz-16bit-mono-pcm",
            )
            used_raw_pcm_codec = True
        except TypeError as te:
            if "codec" not in str(te):
                raise
            communicator = edge_tts.Communicate(text, voice_name)
        audio_buffer = bytearray()
        async for chunk in communicator.stream():
            if chunk["type"] == "audio":
                audio_buffer.extend(chunk["data"])
        raw = bytes(audio_buffer)
        if not raw:
            return b""

        if used_raw_pcm_codec:
            return raw

        from tts.audio_convert import mp3_to_pcm16k

        pcm = mp3_to_pcm16k(raw)
        if not pcm:
            logger.error(
                "Edge TTS returned MP3 but conversion to PCM failed. "
                "Install ffmpeg on PATH, or: pip install miniaudio"
            )
            return b""
        return pcm
    except Exception as e:
        logger.error(f"Edge TTS error: {e}")
        return b""
