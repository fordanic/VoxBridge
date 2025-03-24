#!/usr/bin/env python3

import logging
import time
from pathlib import Path
from typing import Optional

import ffmpeg

logger = logging.getLogger("voxbridge.rtmp_sender")


class RTMPSender:
    """
    A utility class for sending audio files to an RTMP server.
    This class is designed for testing purposes, allowing you to simulate
    a live audio stream using a pre-recorded audio file.
    """

    def __init__(self, rtmp_url: str, sample_rate: int = 16000):
        """
        Initialize the RTMP sender.

        Args:
            rtmp_url: URL of the RTMP stream to publish to
            sample_rate: Target sample rate in Hz (default: 16kHz to match STT requirements)
        """
        self.rtmp_url = rtmp_url
        self.sample_rate = sample_rate
        self.process: Optional[ffmpeg.Stream] = None

    def stream_audio_file(self, audio_file: str, loop: bool = False) -> None:
        """
        Stream an audio file to the RTMP server.

        Args:
            audio_file: Path to the audio file to stream
            loop: Whether to loop the audio file continuously (default: False)
        """
        if not Path(audio_file).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        try:
            # Input configuration
            input_stream = ffmpeg.input(
                audio_file,
                stream_loop=-1 if loop else 0  # -1 means infinite loop
            )

            # Output configuration for RTMP
            stream = ffmpeg.output(
                input_stream,
                self.rtmp_url,
                format="flv",        # RTMP requires FLV format
                acodec="aac",        # AAC audio codec
                ar=self.sample_rate,  # Resample to target rate
                ac=1,               # Convert to mono
                ab="64k",           # Lower audio bitrate
                bufsize="64k",      # Buffer size matching bitrate
                frame_size=1024,    # Smaller frame size for AAC
                strict="-2",        # Allow experimental encoders
                flvflags="no_duration_filesize",  # Skip duration/filesize headers
                loglevel="warning"
            )

            # Start streaming
            logger.info(f"Starting to stream {audio_file} to {self.rtmp_url}")
            self.process = stream.run_async(pipe_stdout=False)

            # Keep the stream running
            while self.process and self.process.poll() is None:
                time.sleep(0.1)

        except ffmpeg.Error as e:
            logger.error(
                f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error streaming audio: {str(e)}")
            raise
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop streaming and clean up resources."""
        if self.process:
            try:
                self.process.kill()
                self.process.wait()
                logger.info("RTMP stream stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping stream: {str(e)}")
            finally:
                self.process = None


def stream_file(audio_file: str, rtmp_url: str = "rtmp://localhost/live/test",
                sample_rate: int = 16000, loop: bool = False) -> None:
    """
    Convenience function to stream an audio file to an RTMP server.

    Args:
        audio_file: Path to the audio file to stream
        rtmp_url: URL of the RTMP server (default: rtmp://localhost/live/test)
        sample_rate: Target sample rate in Hz (default: 16kHz)
        loop: Whether to loop the audio file continuously (default: False)
    """
    sender = RTMPSender(rtmp_url, sample_rate)
    try:
        sender.stream_audio_file(audio_file, loop)
    except KeyboardInterrupt:
        logger.info("Streaming interrupted by user")
    finally:
        sender.stop()


if __name__ == "__main__":
    import argparse

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Stream audio file to RTMP server")
    parser.add_argument("audio_file", help="Path to the audio file to stream")
    parser.add_argument("--rtmp-url", default="rtmp://localhost/live/test",
                        help="RTMP URL to stream to")
    parser.add_argument("--sample-rate", type=int, default=16000,
                        help="Target sample rate in Hz")
    parser.add_argument("--loop", action="store_true",
                        help="Loop the audio file continuously")

    args = parser.parse_args()

    # Start streaming
    stream_file(
        args.audio_file,
        rtmp_url=args.rtmp_url,
        sample_rate=args.sample_rate,
        loop=args.loop
    )
