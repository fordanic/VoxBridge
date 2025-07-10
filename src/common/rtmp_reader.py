#!/usr/bin/env python3

import logging
import select
import subprocess
import threading
import time
from typing import Generator, Optional

import numpy as np

logger = logging.getLogger("voxbridge.rtmp_reader")


class RTMPDisconnectedError(Exception):
    """Raised when RTMP stream is disconnected."""
    pass


class RTMPReader:
    """
    A utility class for reading audio from RTMP streams and converting it to PCM chunks.
    This class is designed to be used by services that need to process audio from RTMP streams.
    Thread-safe for process management.
    """

    def __init__(self, rtmp_url: str, sample_rate: int = 16000, chunk_size: float = 0.5,
                 reconnect_delay: float = 5.0, max_retries: int = 3, read_timeout: float = 1.0):
        """
        Initialize the RTMP reader.

        Args:
            rtmp_url: URL of the RTMP stream
            sample_rate: Target sample rate in Hz (default: 16kHz for most STT engines)
            chunk_size: Size of audio chunks in seconds (default: 0.5 seconds)
            reconnect_delay: Delay between reconnection attempts in seconds
            max_retries: Maximum number of reconnection attempts
            read_timeout: Timeout for reading audio chunks in seconds
        """
        self.rtmp_url = rtmp_url
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.process: Optional[subprocess.Popen] = None
        self.reconnect_delay = reconnect_delay
        self.max_retries = max_retries
        self.current_retries = 0
        self.read_timeout = read_timeout
        self._error_thread: Optional[threading.Thread] = None
        self._stop_error_thread = False
        self._lock = threading.Lock()
        self._last_error = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __del__(self):
        self.stop()

    def _log_stderr(self, process):
        """Log FFmpeg error output in a separate thread"""
        while not self._stop_error_thread:
            try:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    logger.debug(
                        f"FFmpeg [{self.rtmp_url}]: {line.decode().strip()}")
            except Exception:
                break

    def start(self, retry: bool = False) -> None:
        """Start reading from the RTMP stream. Thread-safe. Retries on failure up to max_retries."""
        with self._lock:
            attempts = 0
            while True:
                if attempts > 0:
                    if attempts > self.max_retries:
                        logger.error(
                            f"Failed to reconnect after {self.max_retries} attempts. Last error: {self._last_error}")
                        raise RTMPDisconnectedError(
                            f"Failed to reconnect after {self.max_retries} attempts. Last error: {self._last_error}")
                    logger.info(
                        f"Attempting reconnection ({attempts}/{self.max_retries}) to {self.rtmp_url}")
                    # Exponential backoff
                    time.sleep(self.reconnect_delay * (2 ** (attempts - 1)))
                else:
                    self.current_retries = 0

                try:
                    if self.process:
                        self.stop()

                    # Build ffmpeg command similar to the working test implementation
                    command = [
                        'ffmpeg',
                        '-hide_banner',          # Hide FFmpeg compilation info
                        '-loglevel', 'warning',  # Show only warnings and errors
                        '-thread_queue_size', '4096',  # Increase thread queue size
                        '-re',                   # Read input at native frame rate
                        '-i', self.rtmp_url,
                        '-fflags', 'nobuffer',   # Reduce input buffering
                        '-f', 's16le',           # Use 16-bit PCM format
                        '-acodec', 'pcm_s16le',  # Use 16-bit PCM codec
                        '-ar', str(self.sample_rate),
                        '-ac', '1',              # Mono audio
                        '-'                      # Output to stdout
                    ]

                    logger.debug(f"FFmpeg command: {' '.join(command)}")

                    # Start the process with large buffer
                    self.process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        bufsize=10**8
                    )

                    # Wait briefly to check for immediate failure
                    time.sleep(0.1)
                    if self.process.poll() is not None and self.process.stderr is not None:
                        stderr = self.process.stderr.read().decode()
                        self._last_error = stderr
                        raise RTMPDisconnectedError(
                            f"FFmpeg failed to start: {stderr}")

                    # Start error logging thread
                    self._stop_error_thread = False
                    self._error_thread = threading.Thread(
                        target=self._log_stderr,
                        args=(self.process,),
                        daemon=True
                    )
                    self._error_thread.start()

                    logger.info(
                        f"Successfully connected to RTMP stream: {self.rtmp_url}")
                    break  # Success

                except Exception as e:
                    error_msg = f"Failed to start RTMP stream: {str(e)}"
                    self._last_error = error_msg
                    logger.error(error_msg)
                    attempts += 1
                    continue

    def read_chunks(self) -> Generator[np.ndarray, None, None]:
        """
        Read audio chunks from the RTMP stream.

        Yields:
            numpy.ndarray: Audio chunk as float32 PCM data
        """
        if not self.process:
            raise RuntimeError("Stream not started. Call start() first.")

        chunk_bytes = int(self.sample_rate * self.chunk_size * 2)

        try:
            while True:
                logger.debug(
                    f"Waiting for audio chunk from {self.rtmp_url}...")

                ready = select.select(
                    [self.process.stdout], [], [], self.read_timeout)
                if not ready[0]:
                    logger.debug(
                        f"No audio data available (timeout) for {self.rtmp_url}")
                    if self.process.poll() is not None and self.process.stderr is not None:
                        logger.error(
                            f"FFmpeg process ended unexpectedly for {self.rtmp_url}")
                        try:
                            stderr = self.process.stderr.read()
                            if stderr:
                                logger.error(
                                    f"FFmpeg error output: {stderr.decode()}")
                        except Exception:
                            pass
                        raise RTMPDisconnectedError(
                            f"FFmpeg process ended unexpectedly for {self.rtmp_url}")
                    continue

                try:
                    if self.process.stdout is None:
                        raise RuntimeError("Stream output is not available")

                    logger.debug(
                        f"Reading {chunk_bytes} bytes of audio data from {self.rtmp_url}")
                    raw_chunk = self.process.stdout.read(chunk_bytes)
                    if not raw_chunk:
                        raise RTMPDisconnectedError(
                            f"Stream ended unexpectedly for {self.rtmp_url}")

                    logger.debug(
                        f"Read {len(raw_chunk)} bytes of audio data from {self.rtmp_url}")

                    chunk = np.frombuffer(raw_chunk, dtype=np.int16).astype(
                        np.float32) / 32768.0
                    yield chunk

                except (IOError, OSError) as e:
                    raise RTMPDisconnectedError(f"Stream read error: {str(e)}")

        except RTMPDisconnectedError as e:
            logger.warning(f"RTMP stream disconnected: {str(e)}")
            self.stop()
            self.start(retry=True)
            yield from self.read_chunks()
        except Exception as e:
            logger.error(f"Error reading from stream: {str(e)}")
            self.stop()
            raise

    def stop(self) -> None:
        """Stop reading from the RTMP stream and clean up resources. Thread-safe."""
        with self._lock:
            self._stop_error_thread = True
            if self._error_thread:
                self._error_thread.join(timeout=1)
                self._error_thread = None

            if self.process:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=2)
                    logger.info(
                        f"RTMP stream closed successfully for {self.rtmp_url}")
                except Exception as e:
                    logger.error(f"Error closing stream: {str(e)}")
                    try:
                        self.process.kill()
                    except Exception:
                        pass
                finally:
                    if self.process.stdout:
                        self.process.stdout.close()
                    if self.process.stderr:
                        self.process.stderr.close()
                    self.process = None


def create_reader(rtmp_url: str, reconnect_delay: float = 5.0,
                  max_retries: int = 3, **kwargs) -> RTMPReader:
    """
    Factory function to create and start an RTMPReader.

    Args:
        rtmp_url: URL of the RTMP stream
        **kwargs: Additional arguments to pass to RTMPReader

    Returns:
        RTMPReader: Started RTMP reader instance
    """
    reader = RTMPReader(
        rtmp_url,
        reconnect_delay=reconnect_delay,
        max_retries=max_retries,
        **kwargs
    )
    reader.start()
    return reader
