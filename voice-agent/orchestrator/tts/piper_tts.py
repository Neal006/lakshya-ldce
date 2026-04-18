import subprocess
import logging
from pathlib import Path
from config import PIPER_BINARY, PIPER_VOICES_DIR, TTS_VOICE, Piper_VOICE_FILES

logger = logging.getLogger(__name__)


def synthesize(text: str, voice: str = None) -> bytes:
    """
    Synthesize text using Piper TTS.
    Returns PCM16 audio at 22050Hz (Piper default).
    """
    voice = voice or TTS_VOICE
    model_name = Piper_VOICE_FILES.get(voice, "en_IN-nepm-medium.onnx")
    model_path = Path(PIPER_VOICES_DIR) / model_name

    if not model_path.exists():
        # Try .onnx.json voice config exists
        onnx_path = model_path
        json_path = Path(str(model_path).replace(".onnx", ".onnx.json"))

        # Try alternative: some Piper distributions use different naming
        alt_names = [model_name, model_name.replace("nepm", "medium"), "en_US-lessac-medium.onnx"]
        for alt in alt_names:
            alt_path = Path(PIPER_VOICES_DIR) / alt
            if alt_path.exists():
                model_path = alt_path
                break
        else:
            logger.warning(f"Piper voice model not found: {model_path}. Falling back.")
            return b""

    try:
        process = subprocess.Popen(
            [str(PIPER_BINARY), "--model", str(model_path), "--output_raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        stdout, _ = process.communicate(input=text.encode("utf-8"), timeout=10)
        return stdout
    except FileNotFoundError:
        logger.error(f"Piper binary not found at: {PIPER_BINARY}")
        return b""
    except subprocess.TimeoutExpired:
        logger.error("Piper TTS timed out")
        process.kill()
        return b""
    except Exception as e:
        logger.error(f"Piper TTS error: {e}")
        return b""


def synthesize_to_16k_pcm(text: str, voice: str = None) -> bytes:
    """
    Synthesize text and return PCM16 audio at 16kHz.
    Piper outputs at 22050Hz, so we resample.
    """
    import audioop

    pcm_22k = synthesize(text, voice)
    if not pcm_22k:
        return b""

    try:
        pcm_16k, _ = audioop.ratecv(pcm_22k, 2, 1, 22050, 16000, None)
        return pcm_16k
    except Exception as e:
        logger.error(f"Audio resampling error: {e}")
        return pcm_22k  # Return original as fallback