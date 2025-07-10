import logging
import os
import time

import pytest

from src.stt.google_stt import GoogleSTT


def test_google_stt():
    """
    Integration test: Google STT with RTMP stream.

    Requirements:
    1. GOOGLE_APPLICATION_CREDENTIALS environment variable set
    2. Running RTMP server (can use tests/rtmp_server)
    3. Active RTMP stream to process

    Example setup:
    1. Start RTMP server:
       cd tests/rtmp_server && docker-compose up -d

    2. Stream test audio to RTMP:
       ffmpeg -re -i data/sample_sermon.wav -ar 44100 -ac 2 -c:a aac -b:a 128k -f flv rtmp://localhost/live/test
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )
    logger = logging.getLogger(__name__)

    logger.info("Starting Google STT integration test")

    # Verify credentials
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path or not os.path.exists(creds_path):
        pytest.skip(
            "GOOGLE_APPLICATION_CREDENTIALS not set or file doesn't exist")

    logger.info(f"Using Google credentials from: {creds_path}")

    try:
        # Initialize STT
        stt = GoogleSTT()
        logger.info("Initialized Google STT")

        # Start processing for a configurable duration
        run_time = int(os.getenv("GOOGLE_STT_TEST_RUNTIME", "15"))
        logger.info(f"Running GoogleSTT for {run_time} seconds...")
        stt.start()
        logger.info("Started STT service")

        transcriptions = []
        start_time = time.time()
        while time.time() - start_time < run_time:
            if hasattr(stt, "get_transcriptions"):
                new_trans = stt.get_transcriptions()
                if new_trans:
                    logger.info(f"Received transcriptions: {new_trans}")
                    transcriptions.extend(new_trans)
            time.sleep(1)

        # Stop gracefully
        stt.stop()
        logger.info("Stopped STT service")

        # Assert that at least one transcription was received
        assert transcriptions, "No transcriptions were received from GoogleSTT."
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        assert False, f"Google STT integration test failed: {str(e)}"
