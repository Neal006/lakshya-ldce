import base64
import audioop
import numpy as np
from config import AUDIO_SAMPLE_RATE, INTERNAL_SAMPLE_RATE


def mulaw_bytes_to_pcm16(mulaw_bytes: bytes) -> bytes:
    """Convert mu-law encoded bytes to PCM16 (linear) bytes."""
    return audioop.ulaw2lin(mulaw_bytes, 2)


def pcm16_to_mulaw_bytes(pcm16_bytes: bytes) -> bytes:
    """Convert PCM16 (linear) bytes to mu-law encoded bytes."""
    return audioop.lin2ulaw(pcm16_bytes, 2)


def pcm16_to_float32(pcm16_bytes: bytes) -> np.ndarray:
    """Convert PCM16 bytes to float32 numpy array [-1.0, 1.0]."""
    return np.frombuffer(pcm16_bytes, dtype=np.int16).astype(np.float32) / 32768.0


def float32_to_pcm16(audio: np.ndarray) -> bytes:
    """Convert float32 numpy array to PCM16 bytes."""
    audio = np.clip(audio * 32768.0, -32768, 32767).astype(np.int16)
    return audio.tobytes()


def resample_8k_to_16k(pcm16_bytes: bytes) -> bytes:
    """Resample PCM16 audio from 8kHz to 16kHz."""
    return audioop.ratecv(pcm16_bytes, 2, 1, AUDIO_SAMPLE_RATE, INTERNAL_SAMPLE_RATE, None)[0]


def resample_16k_to_8k(pcm16_bytes: bytes) -> bytes:
    """Resample PCM16 audio from 16kHz to 8kHz."""
    return audioop.ratecv(pcm16_bytes, 2, 1, INTERNAL_SAMPLE_RATE, AUDIO_SAMPLE_RATE, None)[0]


def decode_twilio_audio(base64_media: str) -> bytes:
    """Decode a Twilio media payload (base64 mu-law) to PCM16 at 16kHz."""
    mulaw_bytes = base64.b64decode(base64_media)
    pcm16_bytes = mulaw_bytes_to_pcm16(mulaw_bytes)
    pcm16_16k = resample_8k_to_16k(pcm16_bytes)
    return pcm16_16k


def encode_twilio_audio(pcm16_16k: bytes) -> str:
    """Encode PCM16 at 16kHz to a Twilio media payload (base64 mu-law at 8kHz)."""
    pcm16_8k = resample_16k_to_8k(pcm16_16k)
    mulaw_bytes = pcm16_to_mulaw_bytes(pcm16_8k)
    return base64.b64encode(mulaw_bytes).decode("utf-8")