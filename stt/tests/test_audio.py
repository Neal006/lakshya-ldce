import logging
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from src.audio.preprocessor import AudioPreprocessor, StreamingChunker
from src.pipeline.postprocessor import PostProcessor
from src.pipeline.formatter import ResponseFormatter, APIResponse

logger = logging.getLogger(__name__)


class TestAudioPreprocessor:
    def test_decode_pcm16(self):
        raw = b"\x00\x00\x00\x7f\xff\x7f\x00\x80\xff\xff"
        samples = AudioPreprocessor.decode_pcm16(raw)
        assert samples.dtype == np.float32
        assert len(samples) == 5

    def test_normalize(self):
        preprocessor = AudioPreprocessor()
        audio = np.array([0.1, -0.2, 0.3, -0.4, 0.5])
        normalized = preprocessor.normalize(audio)
        assert np.max(np.abs(normalized)) <= 1.0

    def test_normalize_empty(self):
        preprocessor = AudioPreprocessor()
        audio = np.array([])
        result = preprocessor.normalize(audio)
        assert len(result) == 0

    def test_resample_same_rate(self):
        preprocessor = AudioPreprocessor()
        audio = np.array([0.1, 0.2, 0.3])
        result = preprocessor.resample(audio, 16000)
        np.testing.assert_array_equal(result, audio)


class TestStreamingChunker:
    def test_chunk_creation(self):
        chunker = StreamingChunker(window_sec=1.0, overlap_sec=0.0, sample_rate=16000)
        audio = np.zeros(16000, dtype=np.float32)
        result = chunker.add_chunk(audio)
        assert result is not None
        assert len(result) == 16000

    def test_chunk_overlap(self):
        chunker = StreamingChunker(window_sec=1.0, overlap_sec=0.5, sample_rate=16000)
        audio1 = np.zeros(16000, dtype=np.float32)
        result1 = chunker.add_chunk(audio1)
        assert result1 is not None
        assert len(chunker.buffer) == 8000

    def test_flush(self):
        chunker = StreamingChunker(window_sec=1.0, overlap_sec=0.0, sample_rate=16000)
        audio = np.zeros(8000, dtype=np.float32)
        chunker.add_chunk(audio)
        result = chunker.flush()
        assert result is not None
        assert len(result) == 16000

    def test_flush_empty(self):
        chunker = StreamingChunker()
        result = chunker.flush()
        assert result is None

    def test_reset(self):
        chunker = StreamingChunker()
        chunker.buffer = np.zeros(1000, dtype=np.float32)
        chunker.reset()
        assert len(chunker.buffer) == 0


class TestPostProcessor:
    def test_punctuation_restoration(self):
        pp = PostProcessor()
        result = pp._restore_punctuation("hello world")
        assert result.endswith(".")

    def test_casing(self):
        pp = PostProcessor()
        result = pp._apply_casing("hello world.")
        assert result[0].isupper()

    def test_filler_removal(self):
        pp = PostProcessor()
        result = pp._remove_fillers("um hello uh world")
        assert "um" not in result
        assert "uh" not in result

    def test_full_process(self):
        pp = PostProcessor()
        result = pp.process("hello world", 0.95, 200.0)
        assert result.text
        assert result.confidence == 0.95
        assert result.latency_ms == 200.0


class TestResponseFormatter:
    def test_format_response(self):
        formatter = ResponseFormatter(model_name="whisper-tiny")
        response = formatter.format("hello", 0.9, 100.0)
        assert response.text == "hello"
        assert response.confidence == 0.9
        assert response.model_used == "whisper-tiny"

    def test_to_dict(self):
        formatter = ResponseFormatter()
        response = formatter.format("test", 0.8, 50.0)
        d = response.to_dict()
        assert "text" in d
        assert "confidence" in d
        assert "latency_ms" in d
        assert "model_used" in d

    def test_streaming_dict(self):
        formatter = ResponseFormatter()
        response = formatter.format("test", 0.8, 50.0)
        d = response.to_streaming_dict(is_final=True)
        assert d["is_final"] is True
