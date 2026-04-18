import subprocess
import logging

logger = logging.getLogger(__name__)


def mp3_to_pcm16k(mp3_data: bytes) -> bytes:
    """Convert MP3 audio data to PCM16 at 16kHz using ffmpeg."""
    try:
        process = subprocess.Popen(
            [
                "ffmpeg", "-i", "pipe:0",
                "-f", "s16le",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        stdout, _ = process.communicate(input=mp3_data, timeout=10)
        return stdout
    except FileNotFoundError:
        logger.error("ffmpeg not found - cannot convert MP3 audio")
        return b""
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg timed out")
        process.kill()
        return b""
    except Exception as e:
        logger.error(f"Audio conversion error: {e}")
        return b""


def wav_to_pcm16k(wav_data: bytes) -> bytes:
    """Convert WAV audio data to PCM16 at 16kHz using ffmpeg."""
    return mp3_to_pcm16k(wav_data)  # Same conversion works for WAV