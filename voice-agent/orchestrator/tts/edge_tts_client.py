import edge_tts
import logging
from config import TTS_VOICE, EDGE_TTS_VOICE_MAP

logger = logging.getLogger(__name__)


async def synthesize(text: str, voice: str = None) -> bytes:
    """Synthesize text using Edge TTS (Microsoft, cloud). Returns MP3 bytes."""
    voice = voice or TTS_VOICE
    voice_name = EDGE_TTS_VOICE_MAP.get(voice, "en-IN-NeerjaNeural")

    try:
        communicator = edge_tts.Communicate(text, voice_name)
        audio_buffer = bytearray()
        async for chunk in communicator.stream():
            if chunk["type"] == edge_tts.AudioChunk:
                audio_buffer.extend(chunk["data"])
        return bytes(audio_buffer)
    except Exception as e:
        logger.error(f"Edge TTS error: {e}")
        return b""