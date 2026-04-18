import logging
import io
import numpy as np
import librosa
import soundfile as sf
from typing import Optional

from src.config import Config

logger = logging.getLogger(__name__)


class AudioPreprocessor:
    def __init__(self, vad_model=None):
        self.target_sr = Config.SAMPLE_RATE
        self.vad = vad_model

    def load_audio(self, file_path: str) -> np.ndarray:
        audio, sr = librosa.load(file_path, sr=None, mono=True)
        return self.resample(audio, sr)

    def load_audio_bytes(self, audio_bytes: bytes, format: str = "wav") -> np.ndarray:
        if format.lower() in ("wav", "flac", "ogg"):
            audio, sr = sf.read(io.BytesIO(audio_bytes))
            audio = audio.astype(np.float32)
            if sr != self.target_sr:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.target_sr)
            return audio
        else:
            import pydub

            seg = pydub.AudioSegment.from_file(io.BytesIO(audio_bytes), format=format)
            seg = seg.set_channels(1).set_frame_rate(self.target_sr)
            samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
            samples /= np.iinfo(seg.array_type).max
            return samples

    def resample(self, audio: np.ndarray, orig_sr: int) -> np.ndarray:
        if orig_sr == self.target_sr:
            return audio
        return librosa.resample(audio, orig_sr=orig_sr, target_sr=self.target_sr)

    def normalize(self, audio: np.ndarray, target_db: float = -3.0) -> np.ndarray:
        peak = np.max(np.abs(audio))
        if peak == 0:
            return audio
        gain = 10 ** (target_db / 20) / peak
        return audio * gain

    def preprocess(self, audio: np.ndarray) -> np.ndarray:
        if len(audio) == 0:
            return audio

        if self.vad is not None:
            audio = self.vad.remove_silence(audio)

        if len(audio) == 0:
            return audio

        audio = self.normalize(audio)
        return audio

    @staticmethod
    def decode_pcm16(raw_bytes: bytes) -> np.ndarray:
        samples = np.frombuffer(raw_bytes, dtype=np.int16)
        return samples.astype(np.float32) / 32768.0


class StreamingChunker:
    def __init__(
        self,
        window_sec: float = Config.CHUNK_WINDOW_SEC,
        overlap_sec: float = Config.CHUNK_OVERLAP_SEC,
        sample_rate: int = Config.SAMPLE_RATE,
    ):
        self.window_samples = int(window_sec * sample_rate)
        self.overlap_samples = int(overlap_sec * sample_rate)
        self.buffer = np.array([], dtype=np.float32)

    def reset(self):
        self.buffer = np.array([], dtype=np.float32)

    def add_chunk(self, audio: np.ndarray) -> Optional[np.ndarray]:
        self.buffer = np.concatenate([self.buffer, audio])
        if len(self.buffer) >= self.window_samples:
            chunk = self.buffer[: self.window_samples]
            self.buffer = self.buffer[
                self.window_samples - self.overlap_samples :
            ]
            return chunk
        return None

    def flush(self) -> Optional[np.ndarray]:
        if len(self.buffer) > 0:
            if len(self.buffer) < self.window_samples:
                chunk = np.pad(
                    self.buffer,
                    (0, self.window_samples - len(self.buffer)),
                )
            else:
                chunk = self.buffer[: self.window_samples]
            self.buffer = np.array([], dtype=np.float32)
            return chunk
        return None
