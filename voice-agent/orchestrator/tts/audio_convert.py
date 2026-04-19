import subprocess
import logging
import audioop

from config import INTERNAL_SAMPLE_RATE

logger = logging.getLogger(__name__)

# Edge TTS (current edge-tts) uses this MP3 format from Microsoft.
_EDGE_TTS_MP3_SAMPLE_RATE = 24000


def _mp3_to_pcm16k_miniaudio(mp3_data: bytes) -> bytes:
    """Decode MP3 to PCM16 mono using miniaudio (no ffmpeg). Edge TTS uses 24 kHz MP3."""
    import miniaudio

    dec = miniaudio.decode(
        mp3_data,
        miniaudio.SampleFormat.SIGNED16,
        1,
        _EDGE_TTS_MP3_SAMPLE_RATE,
    )
    pcm = dec.samples.tobytes()
    if dec.sample_rate == INTERNAL_SAMPLE_RATE:
        return pcm
    return audioop.ratecv(pcm, 2, 1, dec.sample_rate, INTERNAL_SAMPLE_RATE, None)[0]


def mp3_to_pcm16k(mp3_data: bytes) -> bytes:
    """Convert MP3 audio to PCM16 at 16 kHz mono. Prefers ffmpeg; falls back to miniaudio."""
    if not mp3_data:
        return b""
    try:
        process = subprocess.Popen(
            [
                "ffmpeg",
                "-i",
                "pipe:0",
                "-f",
                "s16le",
                "-acodec",
                "pcm_s16le",
                "-ar",
                str(INTERNAL_SAMPLE_RATE),
                "-ac",
                "1",
                "-",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        stdout, _ = process.communicate(input=mp3_data, timeout=10)
        if stdout:
            return stdout
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg timed out")
        process.kill()
    except Exception as e:
        logger.warning(f"ffmpeg MP3 conversion failed: {e}")

    try:
        return _mp3_to_pcm16k_miniaudio(mp3_data)
    except ImportError:
        logger.error(
            "Neither ffmpeg nor miniaudio could convert Edge TTS MP3. "
            "Install ffmpeg on PATH, or: pip install miniaudio"
        )
        return b""
    except Exception as e:
        logger.error(f"miniaudio MP3 conversion error: {e}")
        return b""


def wav_to_pcm16k(wav_data: bytes) -> bytes:
    """Convert WAV audio data to PCM16 at 16kHz using ffmpeg."""
    return mp3_to_pcm16k(wav_data)  # Same conversion works for WAV