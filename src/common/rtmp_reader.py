#!/usr/bin/env python3

import logging
import time
from typing import Generator, Optional

import ffmpeg
import numpy as np

logger = logging.getLogger("voxbridge.rtmp_reader")


class RTMPDisconnectedError(Exception):
    """Raised when RTMP stream is disconnected."""
    pass


class RTMPReader:
    """
    A utility class for reading audio from RTMP streams and converting it to PCM chunks.
    This class is designed to be used by services that need to process audio from RTMP streams.
    """

    def __init__(self, rtmp_url: str, sample_rate: int = 16000, chunk_size: float = 0.5,
                 reconnect_delay: float = 5.0, max_retries: int = 3):
        """
        Initialize the RTMP reader.

        Args:
            rtmp_url: URL of the RTMP stream
            sample_rate: Target sample rate in Hz (default: 16kHz for most STT engines)
            chunk_size: Size of audio chunks in seconds (default: 0.5 seconds)
        """
        self.rtmp_url = rtmp_url
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.process: Optional[ffmpeg.Stream] = None
        self.reconnect_delay = reconnect_delay
        self.max_retries = max_retries
        self.current_retries = 0

    def start(self, retry: bool = False) -> None:
        """Start reading from the RTMP stream."""
        if retry:
            if self.current_retries >= self.max_retries:
                raise RTMPDisconnectedError(
                    f"Failed to reconnect after {self.max_retries} attempts")
            self.current_retries += 1
            logger.info(
                f"Attempting reconnection ({self.current_retries}/{self.max_retries})")
            time.sleep(self.reconnect_delay)
        else:
            self.current_retries = 0

        try:
            if self.process:
                self.stop()

            # Set up ffmpeg stream with network-related options
            stream = ffmpeg.input(
                self.rtmp_url,
                # Reduced timeout for faster disconnect detection
                timeout=5000000,  # 5 seconds in microseconds
                # Allow reconnecting on connection loss
                reconnect=1,
                reconnect_at_eof=1,
                reconnect_streamed=1
            )

            # Convert to PCM format with specified sample rate
            stream = ffmpeg.output(
                stream,
                'pipe:',
                format='f32le',  # 32-bit float PCM
                acodec='pcm_f32le',
                ac=1,  # mono
                ar=self.sample_rate,
                # Include warning logs for better debugging
                loglevel='warning',
                # Additional options for better network handling
                fflags='nobuffer',  # Reduce buffering
                flags='low_delay'   # Minimize latency
            )

            # Start the process
            self.process = stream.run_async(pipe_stdout=True)
            logger.info(
                f"Successfully connected to RTMP stream: {self.rtmp_url}")

        except ffmpeg.Error as e:
            error_msg = f"Failed to start RTMP stream: {str(e)}"
            logger.error(error_msg)
            if retry:
                # If this was a retry attempt, try again
                self.start(retry=True)
            else:
                raise RTMPDisconnectedError(error_msg)

    def read_chunks(self) -> Generator[np.ndarray, None, None]:
        """
        Read audio chunks from the RTMP stream.

        Yields:
            numpy.ndarray: Audio chunk as float32 PCM data
        """
        if not self.process:
            raise RuntimeError("Stream not started. Call start() first.")

        # Calculate chunk size in bytes
        # 4 bytes per float32
        chunk_bytes = int(self.sample_rate * self.chunk_size * 4)

        try:
            while True:
                # Read chunk of raw bytes
                try:
                    raw_chunk = self.process.stdout.read(chunk_bytes)
                    if not raw_chunk:
                        raise RTMPDisconnectedError(
                            "Stream ended unexpectedly")
                except (IOError, OSError) as e:
                    raise RTMPDisconnectedError(f"Stream read error: {str(e)}")

                # Convert to numpy array of float32
                chunk = np.frombuffer(raw_chunk, dtype=np.float32)
                yield chunk

        except RTMPDisconnectedError as e:
            logger.warning(f"RTMP stream disconnected: {str(e)}")
            # Attempt to reconnect
            self.start(retry=True)
            # Start yielding chunks from the new connection
            yield from self.read_chunks()
        except Exception as e:
            logger.error(f"Error reading from stream: {str(e)}")
            self.stop()
            raise

    def stop(self) -> None:
        """Stop reading from the RTMP stream and clean up resources."""
        if self.process:
            try:
                self.process.stdin.close()
                self.process.stdout.close()
                self.process.wait()
                logger.info("RTMP stream closed successfully")
            except Exception as e:
                logger.error(f"Error closing stream: {str(e)}")
            finally:
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
