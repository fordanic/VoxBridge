import pytest
import os
import threading
import time

import pyaudio as pa
import numpy as np

from src.common.rtmp_reader import RTMPReader
from scripts.rtmp_sender import RTMPSender


def get_sample_audio_file():
    # Use the provided sample_sermon.wav in the data directory
    sample_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../data/sample_sermon.wav")
    )
    if not os.path.exists(sample_path):
        pytest.skip("Sample audio file not found: {}".format(sample_path))
    return sample_path


def test_rtmp_send_and_receive(
    rtmp_url="rtmp://localhost/live/test", audio_playback=True, max_duration=10
):
    """
    Integration test: send audio to RTMP server and receive it back.
    Requires a running local RTMP server at rtmp://localhost/live/test.
    """
    sample_rate = 16000
    chunk_size = 0.5
    audio_file = get_sample_audio_file()

    # Start sender in a background thread
    print(f"Starting RTMP sender to {rtmp_url} with audio file {audio_file}")
    if not os.path.exists(audio_file):
        pytest.skip(f"Audio file does not exist: {audio_file}")

    # Create RTMP sender instance
    sender = RTMPSender(rtmp_url, sample_rate=sample_rate)
    sender_thread = threading.Thread(
        target=sender.stream_audio_file,
        args=(audio_file,),
        kwargs={"loop": False},
        daemon=True,
    )
    sender_thread.start()
    print("RTMP sender thread started")

    # Wait for the sender to start
    if not sender_thread.is_alive():
        pytest.fail("RTMP sender thread did not start successfully")

    print("RTMP sender is running, waiting for stream to stabilize...")

    # Wait a moment for the stream to start
    time.sleep(2)

    # Check if sender encountered a "Already publishing" error
    if hasattr(sender, "last_error") and sender.last_error is not None:
        if "Already publishing" in str(sender.last_error):
            print(
                "WARNING: RTMP server reports 'Already publishing'. "
                "There may already be an active stream on this key. "
                "Test will continue, but results may be unreliable."
            )

    # Start RTMP reader
    print(f"Starting RTMP reader for URL: {rtmp_url}")
    # Create RTMP reader instance
    reader = RTMPReader(rtmp_url, sample_rate=sample_rate, chunk_size=chunk_size)
    # Run the reader for 20 seconds while simultaneously receiving audio
    # and playing it back
    try:
        reader.start()
        received_chunks = []
        start_time = time.time()
        p = None
        stream = None
        if audio_playback:
            # Initialize PyAudio for playback
            print("Initializing PyAudio for audio playback")
            p = pa.PyAudio()
            stream = p.open(
                format=pa.paFloat32, channels=1, rate=sample_rate, output=True
            )
        for chunk in reader.read_chunks():
            received_chunks.append(chunk)
            if audio_playback and stream:
                stream.write(chunk.astype(np.float32).tobytes())
            if time.time() - start_time >= max_duration:
                print("Max duration reached, stopping reader")
                break
        # Check that we received audio data
        assert len(received_chunks) > 0
        for chunk in received_chunks:
            # Ensure each chunk is a numpy array with audio data
            print("Checking received audio chunk")
            assert isinstance(chunk, np.ndarray)
            assert chunk.size > 0
            # Check that the chunk is not all zeros (should contain audio)
            assert np.any(chunk != 0)
    finally:
        if stream:
            stream.close()
        if p:
            p.terminate()
        reader.stop()
        sender.stop()
        sender_thread.join(timeout=2)
    print("RTMP send and receive test completed successfully")
