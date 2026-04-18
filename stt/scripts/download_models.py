import logging
import os
from pathlib import Path
import torch
import whisper

logger = logging.getLogger(__name__)


def download_whisper_tiny(output_dir: str = "models"):
    logger.info("Downloading Whisper-tiny model")
    os.makedirs(output_dir, exist_ok=True)

    model = whisper.load_model("tiny")
    output_path = os.path.join(output_dir, "whisper_tiny.pt")
    torch.save(model.state_dict(), output_path)
    logger.info(f"Whisper-tiny saved to {output_path}")
    return output_path


def download_silero_vad(output_dir: str = "models"):
    logger.info("Downloading Silero VAD model")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "silero_vad.onnx")
    if not os.path.exists(output_path):
        import urllib.request
        url = "https://github.com/snakers4/silero-vad/raw/master/files/silero_vad.onnx"
        logger.info(f"Downloading from {url}")
        urllib.request.urlretrieve(url, output_path)

    logger.info(f"Silero VAD saved to {output_path}")
    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    models_dir = str(Path(__file__).parent.parent / "models")

    download_whisper_tiny(models_dir)
    download_silero_vad(models_dir)

    logger.info("All models downloaded successfully")
