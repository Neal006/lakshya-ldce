import logging
from config import PRIMARY_TTS, NETWORK_MODE

logger = logging.getLogger(__name__)


async def synthesize_speech(text: str, voice: str = None) -> bytes:
    """
    Synthesize speech. Returns PCM16 audio at 16kHz.
    Routes to Piper (local) or Edge TTS (cloud) based on configuration.
    """
    internet_available = True

    if NETWORK_MODE == "offline":
        internet_available = False
    elif NETWORK_MODE == "auto":
        try:
            from config import is_internet_available
            internet_available = await is_internet_available()
        except Exception:
            internet_available = False

    # Try cloud TTS first if preferred and available
    if PRIMARY_TTS in ("auto", "edge_tts") and internet_available:
        try:
            from tts.edge_tts_client import synthesize as edge_synthesize
            from tts.audio_convert import mp3_to_pcm16k
            mp3_data = await edge_synthesize(text, voice)
            if mp3_data:
                pcm16_data = mp3_to_pcm16k(mp3_data)
                if pcm16_data:
                    logger.info("Used Edge TTS (cloud)")
                    return pcm16_data
        except Exception as e:
            logger.warning(f"Edge TTS failed, falling back to Piper: {e}")

    # Fall back to local Piper TTS
    try:
        from tts.piper_tts import synthesize_to_16k_pcm
        pcm16_data = synthesize_to_16k_pcm(text, voice)
        if pcm16_data:
            logger.info("Used Piper TTS (local)")
            return pcm16_data
    except Exception as e:
        logger.error(f"Piper TTS also failed: {e}")

    # Last resort: return empty audio (caller should handle this)
    logger.error("All TTS methods failed")
    return b""