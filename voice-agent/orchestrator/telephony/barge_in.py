import numpy as np
from config import INTERNAL_SAMPLE_RATE

ENERGY_THRESHOLD = 0.02
MIN_SPEECH_DURATION_MS = 300
SILENCE_DURATION_MS = 500


def detect_speech_in_chunk(audio_float: np.ndarray, threshold: float = ENERGY_THRESHOLD) -> bool:
    """Check if an audio chunk contains speech based on energy."""
    if len(audio_float) == 0:
        return False
    energy = np.sqrt(np.mean(audio_float ** 2))
    return energy > threshold


def should_interrupt(inbound_audio: np.ndarray, is_playing_tts: bool) -> bool:
    """
    Determine if the user is barging in (speaking during TTS playback).
    Returns True if speech is detected and TTS is playing.
    """
    if not is_playing_tts:
        return False
    return detect_speech_in_chunk(inbound_audio)


class BargeInDetector:
    def __init__(self, energy_threshold: float = ENERGY_THRESHOLD):
        self.energy_threshold = energy_threshold
        self.is_playing_tts = False

    def set_tts_playing(self, playing: bool):
        self.is_playing_tts = playing

    def process_inbound(self, audio_float: np.ndarray) -> bool:
        """Process inbound audio chunk. Returns True if barge-in detected."""
        if not self.is_playing_tts:
            return False
        return detect_speech_in_chunk(audio_float, self.energy_threshold)