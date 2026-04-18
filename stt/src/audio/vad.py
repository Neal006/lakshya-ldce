import logging
import numpy as np
import onnxruntime as ort
from typing import List, Tuple

logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    def __init__(self, model_path: str):
        self.session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
        )
        self._h = np.zeros((2, 1, 64)).astype("float32")
        self._c = np.zeros((2, 1, 64)).astype("float32")
        self.sample_rate = 16000
        self.window_size_samples = int(self.sample_rate * 0.032)

    def reset_states(self):
        self._h = np.zeros((2, 1, 64)).astype("float32")
        self._c = np.zeros((2, 1, 64)).astype("float32")

    def __call__(self, audio_chunk: np.ndarray) -> float:
        audio_chunk = audio_chunk.astype(np.float32)
        if len(audio_chunk) != self.window_size_samples:
            audio_chunk = np.pad(
                audio_chunk,
                (0, max(0, self.window_size_samples - len(audio_chunk))),
            )[: self.window_size_samples]

        ort_inputs = {
            "input": audio_chunk[np.newaxis, :],
            "h": self._h,
            "c": self._c,
            "sr": np.array(self.sample_rate, dtype=np.int64),
        }
        ort_outs = self.session.run(None, ort_inputs)
        out, self._h, self._c = ort_outs
        self._h = np.array(self._h)
        self._c = np.array(self._c)
        return float(out[0][0])

    def detect_speech_segments(
        self, audio: np.ndarray, threshold: float = 0.5
    ) -> List[Tuple[int, int]]:
        self.reset_states()
        segments = []
        in_speech = False
        start_sample = 0

        for i in range(0, len(audio), self.window_size_samples):
            chunk = audio[i : i + self.window_size_samples]
            if len(chunk) == 0:
                break
            prob = self(chunk)
            is_speech = prob > threshold

            if is_speech and not in_speech:
                in_speech = True
                start_sample = i
            elif not is_speech and in_speech:
                in_speech = False
                segments.append((start_sample, i))

        if in_speech:
            segments.append((start_sample, len(audio)))

        self.reset_states()
        return segments

    def remove_silence(
        self, audio: np.ndarray, threshold: float = 0.5
    ) -> np.ndarray:
        segments = self.detect_speech_segments(audio, threshold)
        if not segments:
            return np.array([], dtype=np.float32)

        parts = []
        for start, end in segments:
            parts.append(audio[start:end])
        return np.concatenate(parts)
