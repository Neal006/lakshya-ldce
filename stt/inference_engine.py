"""
inference_engine.py — Consolidated STT inference engine.

Combines faster-whisper (CTranslate2) transcription, Silero VAD
silence removal, and text post-processing into a single engine.
"""

import io
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_RATE: int = 16_000
VAD_WINDOW_SAMPLES: int = 512
WHISPER_MODEL_SIZE: str = "tiny"

BASE_DIR: Path = Path(__file__).resolve().parent
MODELS_DIR: Path = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

VAD_URL: str = (
    "https://raw.githubusercontent.com/snakers4/silero-vad/v4.0/files/silero_vad.onnx"
)
VAD_PATH: Path = MODELS_DIR / "silero_vad.onnx"

FILLER_WORDS: frozenset[str] = frozenset({"um", "uh", "uhh", "umm", "er", "ah"})

NUMBER_WORDS: dict[str, str] = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20",
}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class TranscriptionResult:
    text: str
    confidence: float
    latency_ms: float
    model_used: str

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "model_used": self.model_used,
        }


# ---------------------------------------------------------------------------
# Streaming Chunker
# ---------------------------------------------------------------------------

class StreamingChunker:
    """Fixed-window chunker with overlap for WebSocket streaming."""

    def __init__(self, window_ms: int = 4000, overlap_ms: int = 450,
                 sample_rate: int = SAMPLE_RATE):
        self.window_samples = int(window_ms * sample_rate / 1000)
        self.overlap_samples = int(overlap_ms * sample_rate / 1000)
        self.sample_rate = sample_rate
        self.buffer: np.ndarray = np.array([], dtype=np.float32)

    def add(self, audio: np.ndarray) -> list[np.ndarray]:
        self.buffer = np.concatenate([self.buffer, audio])
        chunks: list[np.ndarray] = []
        while len(self.buffer) >= self.window_samples:
            chunk = self.buffer[: self.window_samples]
            chunks.append(chunk)
            self.buffer = self.buffer[self.window_samples - self.overlap_samples:]
        return chunks

    def flush(self) -> np.ndarray | None:
        if len(self.buffer) > 0:
            remaining = self.buffer.copy()
            self.buffer = np.array([], dtype=np.float32)
            return remaining
        return None

    def reset(self) -> None:
        self.buffer = np.array([], dtype=np.float32)


# ---------------------------------------------------------------------------
# Post-processor
# ---------------------------------------------------------------------------

class _PostProcessor:
    @staticmethod
    def remove_fillers(text: str) -> str:
        words = text.split()
        words = [w for w in words if w.lower().rstrip(".,!?;:") not in FILLER_WORDS]
        return " ".join(words)

    @staticmethod
    def normalize_numbers(text: str) -> str:
        words = text.split()
        result: list[str] = []
        for w in words:
            lower = w.lower().rstrip(".,!?;:")
            if lower in NUMBER_WORDS:
                suffix = w[len(lower):] if len(w) > len(lower) else ""
                result.append(NUMBER_WORDS[lower] + suffix)
            else:
                result.append(w)
        return " ".join(result)

    @staticmethod
    def sentence_case(text: str) -> str:
        if not text:
            return text
        return text[0].upper() + text[1:]

    @staticmethod
    def fix_punctuation(text: str) -> str:
        text = text.strip()
        if text and text[-1] not in ".!?":
            text += "."
        return text

    @staticmethod
    def cleanup_whitespace(text: str) -> str:
        return " ".join(text.split())

    def process(self, text: str) -> str:
        text = self.remove_fillers(text)
        text = self.normalize_numbers(text)
        text = self.sentence_case(text)
        text = self.fix_punctuation(text)
        text = self.cleanup_whitespace(text)
        return text


# ---------------------------------------------------------------------------
# STT Engine
# ---------------------------------------------------------------------------

class STTEngine:
    def __init__(self, model_size: str = WHISPER_MODEL_SIZE,
                 device: str | None = None,
                 compute_type: str | None = None):
        if device is None:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        if compute_type is None:
            compute_type = "int8_float16" if self.device == "cuda" else "int8"
        self.compute_type = compute_type

        from faster_whisper import WhisperModel
        self._model = WhisperModel(
            model_size, device=self.device, compute_type=self.compute_type
        )
        self.model_name = f"faster-whisper-{model_size}"

        self._vad = self._load_vad()
        self._post = _PostProcessor()

    # ---- VAD -------------------------------------------------------

    def _load_vad(self):
        import onnxruntime as ort
        if not VAD_PATH.exists():
            print(f"Downloading Silero VAD model to {VAD_PATH} ...")
            urllib.request.urlretrieve(VAD_URL, str(VAD_PATH))
        session = ort.InferenceSession(str(VAD_PATH))
        return session

    def _vad_detect_speech(self, audio: np.ndarray,
                           threshold: float = 0.5) -> list[tuple[int, int]]:
        h = np.zeros((2, 1, 64), dtype=np.float32)
        c = np.zeros((2, 1, 64), dtype=np.float32)
        sr_tensor = np.array(SAMPLE_RATE, dtype=np.int64)

        def _run(chunk: np.ndarray, h: np.ndarray, c: np.ndarray):
            inp = chunk[np.newaxis, :].astype(np.float32)
            out = self._vad.run(
                None,
                {"input": inp, "sr": sr_tensor, "h": h, "c": c},
            )
            prob = out[0][0, 0].item()
            h_new = out[1]
            c_new = out[2]
            return prob, h_new, c_new

        if len(audio) < VAD_WINDOW_SAMPLES:
            if len(audio) == 0:
                return []
            chunk = np.pad(audio, (0, VAD_WINDOW_SAMPLES - len(audio)))
            prob, h, c = _run(chunk, h, c)
            if prob >= threshold:
                return [(0, len(audio))]
            return []

        speeches: list[tuple[int, int]] = []
        in_speech = False
        start = 0
        for i in range(0, len(audio) - VAD_WINDOW_SAMPLES + 1, VAD_WINDOW_SAMPLES):
            chunk = audio[i: i + VAD_WINDOW_SAMPLES]
            prob, h, c = _run(chunk, h, c)
            if prob >= threshold and not in_speech:
                start = i
                in_speech = True
            elif prob < threshold and in_speech:
                speeches.append((start, i + VAD_WINDOW_SAMPLES))
                in_speech = False
        if in_speech:
            speeches.append((start, len(audio)))
        return speeches

    def _remove_silence(self, audio: np.ndarray,
                        threshold: float = 0.5) -> np.ndarray:
        speeches = self._vad_detect_speech(audio, threshold)
        if not speeches:
            return audio
        return np.concatenate([audio[s:e] for s, e in speeches])

    # ---- Audio preprocessing ----------------------------------------

    @staticmethod
    def decode_pcm16(raw_bytes: bytes) -> np.ndarray:
        pcm = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32)
        pcm /= 32768.0
        return pcm

    def _load_audio_bytes(self, audio_bytes: bytes,
                          fmt: str = "wav") -> tuple[np.ndarray, int]:
        import soundfile as sf
        audio, sr = sf.read(io.BytesIO(audio_bytes))
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        audio = audio.astype(np.float32)
        return audio, sr

    def _normalize(self, audio: np.ndarray) -> np.ndarray:
        peak = np.abs(audio).max()
        if peak > 0:
            audio = audio / peak
        return audio

    def _resample(self, audio: np.ndarray, orig_sr: int) -> np.ndarray:
        if orig_sr == SAMPLE_RATE:
            return audio
        import librosa
        audio = librosa.resample(audio, orig_sr=orig_sr, target_sr=SAMPLE_RATE)
        return audio.astype(np.float32)

    def _preprocess(self, audio: np.ndarray, orig_sr: int) -> np.ndarray:
        audio = self._resample(audio, orig_sr)
        audio = self._normalize(audio)
        audio = self._remove_silence(audio)
        return audio

    # ---- Transcription ----------------------------------------------

    def _transcribe_array(self, audio: np.ndarray) -> tuple[str, float]:
        segments, info = self._model.transcribe(audio, beam_size=1)
        text_parts: list[str] = []
        total_conf: float = 0.0
        count: int = 0
        for seg in segments:
            text_parts.append(seg.text.strip())
            total_conf += seg.avg_probability if hasattr(seg, "avg_probability") else seg.probability if hasattr(seg, "probability") else getattr(seg, "no_speech_prob", 0.0)
            count += 1
        text = " ".join(text_parts)
        avg_conf = total_conf / count if count > 0 else 0.0
        return text, avg_conf

    def _postprocess_text(self, text: str) -> str:
        return self._post.process(text)

    # ---- Public API -------------------------------------------------

    def transcribe(self, audio_bytes: bytes,
                   fmt: str = "wav") -> TranscriptionResult:
        t0 = time.perf_counter()
        audio, sr = self._load_audio_bytes(audio_bytes, fmt)
        audio = self._preprocess(audio, sr)
        if len(audio) == 0:
            return TranscriptionResult(
                text="", confidence=0.0, latency_ms=0.0, model_used=self.model_name
            )
        raw_text, conf = self._transcribe_array(audio)
        text = self._postprocess_text(raw_text)
        latency = (time.perf_counter() - t0) * 1000
        return TranscriptionResult(
            text=text, confidence=conf,
            latency_ms=round(latency, 1), model_used=self.model_name,
        )

    def transcribe_raw(self, audio_array: np.ndarray,
                       sample_rate: int = SAMPLE_RATE) -> TranscriptionResult:
        t0 = time.perf_counter()
        audio = self._resample(audio_array, sample_rate)
        audio = self._normalize(audio)
        audio = self._remove_silence(audio)
        if len(audio) == 0:
            return TranscriptionResult(
                text="", confidence=0.0, latency_ms=0.0, model_used=self.model_name
            )
        raw_text, conf = self._transcribe_array(audio)
        text = self._postprocess_text(raw_text)
        latency = (time.perf_counter() - t0) * 1000
        return TranscriptionResult(
            text=text, confidence=conf,
            latency_ms=round(latency, 1), model_used=self.model_name,
        )

    def transcribe_chunk(self, audio_array: np.ndarray) -> TranscriptionResult:
        t0 = time.perf_counter()
        if len(audio_array) == 0:
            return TranscriptionResult(
                text="", confidence=0.0, latency_ms=0.0, model_used=self.model_name
            )
        raw_text, conf = self._transcribe_array(audio_array)
        text = self._postprocess_text(raw_text)
        latency = (time.perf_counter() - t0) * 1000
        return TranscriptionResult(
            text=text, confidence=conf,
            latency_ms=round(latency, 1), model_used=self.model_name,
        )


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Initialising STT Engine for self-test ...")
    engine = STTEngine()
    print(f"  device={engine.device}  compute_type={engine.compute_type}")

    silence = np.zeros(SAMPLE_RATE, dtype=np.float32)
    r = engine.transcribe_raw(silence)
    print(f"  Silence -> \"{r.text}\"  conf={r.confidence:.2f}  {r.latency_ms:.0f}ms")

    t = np.sin(2 * np.pi * 440 * np.linspace(0, 1, SAMPLE_RATE)).astype(np.float32)
    r = engine.transcribe_raw(t)
    print(f"  Tone   -> \"{r.text}\"  conf={r.confidence:.2f}  {r.latency_ms:.0f}ms")

    print("Self-test done.")
