import logging
import time
import numpy as np
from typing import Optional

from src.config import Config
from src.audio.preprocessor import AudioPreprocessor, StreamingChunker
from src.audio.vad import VoiceActivityDetector
from src.models.whisper import WhisperTiny
from src.pipeline.postprocessor import PostProcessor
from src.pipeline.formatter import ResponseFormatter, APIResponse

logger = logging.getLogger(__name__)


class STTPipeline:
    def __init__(self):
        logger.info("Initializing STT pipeline")

        self.vad: Optional[VoiceActivityDetector] = None
        try:
            self.vad = VoiceActivityDetector(Config.VAD_MODEL_PATH)
            logger.info("VAD model loaded")
        except Exception as e:
            logger.warning(f"VAD model not loaded, proceeding without silence removal: {e}")

        self.preprocessor = AudioPreprocessor(vad_model=self.vad)
        self.whisper = WhisperTiny()
        self.postprocessor = PostProcessor()
        self.formatter = ResponseFormatter(model_name="whisper-tiny")

        logger.info("STT pipeline ready")

    def transcribe_file(self, file_path: str) -> APIResponse:
        logger.info(f"Transcribing file: {file_path}")
        audio = self.preprocessor.load_audio(file_path)
        return self._process_audio(audio)

    def transcribe_bytes(self, audio_bytes: bytes, format: str = "wav") -> APIResponse:
        audio = self.preprocessor.load_audio_bytes(audio_bytes, format)
        return self._process_audio(audio)

    def transcribe_audio_array(self, audio: np.ndarray) -> APIResponse:
        return self._process_audio(audio)

    def _process_audio(self, audio: np.ndarray) -> APIResponse:
        if len(audio) == 0:
            return self.formatter.format(
                text="",
                confidence=0.0,
                latency_ms=0.0,
            )

        start = time.perf_counter()

        audio = self.preprocessor.preprocess(audio)

        if len(audio) == 0:
            return self.formatter.format(
                text="",
                confidence=0.0,
                latency_ms=(time.perf_counter() - start) * 1000,
            )

        result = self.whisper.transcribe(audio)

        processed = self.postprocessor.process(
            text=result.text,
            confidence=result.confidence,
            latency_ms=result.latency_ms,
        )

        total_latency = (time.perf_counter() - start) * 1000

        return self.formatter.format(
            text=processed.text,
            confidence=processed.confidence,
            latency_ms=total_latency,
        )


class StreamingSTTPipeline:
    def __init__(self, stt_pipeline: STTPipeline):
        self.pipeline = stt_pipeline
        self.chunker = StreamingChunker()

    def reset(self):
        self.chunker.reset()

    def process_chunk(self, audio_bytes: bytes) -> list[APIResponse]:
        audio = AudioPreprocessor.decode_pcm16(audio_bytes)
        chunk = self.chunker.add_chunk(audio)

        if chunk is not None and np.max(np.abs(chunk)) > 0.001:
            result = self.pipeline.transcribe_audio_array(chunk)
            if result.text.strip():
                return [result]
        return []

    def flush(self) -> list[APIResponse]:
        chunk = self.chunker.flush()
        if chunk is not None and np.max(np.abs(chunk)) > 0.001:
            result = self.pipeline.transcribe_audio_array(chunk)
            if result.text.strip():
                return [result]
        return []
