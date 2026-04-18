import json
import logging
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from src.audio.preprocessor import AudioPreprocessor, StreamingChunker
from src.pipeline.orchestrator import STTPipeline

logger = logging.getLogger(__name__)


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"WebSocket connected: {websocket.client}")

    chunker = StreamingChunker()
    pipeline: STTPipeline = websocket.app.state.pipeline

    try:
        while True:
            data = await websocket.receive_bytes()

            if len(data) == 0:
                continue

            audio = AudioPreprocessor.decode_pcm16(data)
            chunk = chunker.add_chunk(audio)

            if chunk is not None and np.max(np.abs(chunk)) > 0.001:
                result = pipeline.transcribe_audio_array(chunk)
                if result.text.strip():
                    response = {
                        "text": result.text,
                        "confidence": result.confidence,
                        "latency_ms": result.latency_ms,
                        "model_used": "whisper-tiny",
                        "is_final": False,
                    }
                    await websocket.send_text(json.dumps(response))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except Exception:
            pass
    finally:
        final_chunk = chunker.flush()
        if final_chunk is not None and np.max(np.abs(final_chunk)) > 0.001:
            result = pipeline.transcribe_audio_array(final_chunk)
            if result.text.strip():
                response = {
                    "text": result.text,
                    "confidence": result.confidence,
                    "latency_ms": result.latency_ms,
                    "model_used": "whisper-tiny",
                    "is_final": True,
                }
                await websocket.send_text(json.dumps(response))
        chunker.reset()
        logger.info(f"WebSocket session ended: {websocket.client}")
