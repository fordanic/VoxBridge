#!/usr/bin/env python3
"""
Download and prepare test audio for STT testing
"""
from scripts.download_audio import download_audio
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

# Add scripts to Python path
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))


def prepare_test_audio():
    """
    Download test audio and convert to correct format for STT testing.
    Uses Swedish audio content by default.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Create test_data directory
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)

    # Source URL for Swedish speech sample
    # This is a Creative Commons licensed Swedish speech sample
    url = "https://commons.wikimedia.org/wiki/File:Sv-välkommen.ogg"
    output_wav = test_data_dir / "test.wav"

    try:
        # Download audio
        logger.info(f"Downloading audio from {url}")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "original.wav"
            download_audio(url, output_dir=str(
                temp_dir), output_name="original")

            # Convert to correct format for STT
            logger.info("Converting to WAV format")
            subprocess.run([
                "ffmpeg", "-y",
                "-i", str(temp_path),
                "-ar", "16000",  # 16kHz sample rate
                "-ac", "1",      # mono
                "-acodec", "pcm_s16le",  # 16-bit PCM
                str(output_wav)
            ], check=True)

        logger.info(f"Test audio prepared: {output_wav}")
        logger.info(
            "You can now use this file with the test_google_stt.py script")
        return True

    except Exception as e:
        logger.error(f"Failed to prepare test audio: {str(e)}")
        return False


if __name__ == "__main__":
    success = prepare_test_audio()
    sys.exit(0 if success else 1)
