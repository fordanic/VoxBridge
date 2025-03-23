#!/usr/bin/env python3

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Union

import ffmpeg
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

logger = logging.getLogger("voxbridge.download_audio")


class AudioDownloader:
    """
    A utility class for downloading audio from web sources and converting
    it to a format suitable for the RTMP sender.
    """

    def __init__(self, output_dir: Optional[Union[str, Path]] = None,
                 sample_rate: int = 16000):
        """
        Initialize the audio downloader.

        Args:
            output_dir: Directory to save downloaded files (default: system temp dir)
            sample_rate: Target sample rate in Hz (default: 16kHz for STT)
        """
        self.output_dir = Path(output_dir) if output_dir else Path(
            tempfile.gettempdir())
        self.sample_rate = sample_rate
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download(self, url: str, output_name: Optional[str] = None) -> str:
        """
        Download audio from a URL and convert it to WAV format.

        Args:
            url: URL of the audio source
            output_name: Optional name for the output file (without extension)

        Returns:
            str: Path to the downloaded and converted audio file
        """
        try:
            # First download the audio in best quality
            with tempfile.NamedTemporaryFile(suffix=".%(ext)s", delete=False) as tf:
                temp_path = tf.name

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_path,
                'quiet': True,
                'no_warnings': True,
                'extract_audio': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }],
            }

            with YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Downloading audio from: {url}")
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'downloaded_audio').replace(' ', '_')

            # The actual downloaded file path (with proper extension)
            downloaded_file = temp_path.replace("%(ext)s", "wav")

            # Determine output path
            if output_name:
                output_file = self.output_dir / f"{output_name}.wav"
            else:
                output_file = self.output_dir / f"{title}.wav"

            # Convert to proper format using ffmpeg
            stream = ffmpeg.input(downloaded_file)
            stream = ffmpeg.output(
                stream,
                str(output_file),
                acodec='pcm_s16le',  # 16-bit PCM
                ac=1,                # mono
                ar=self.sample_rate,  # target sample rate
                loglevel='warning'
            )

            logger.info(f"Converting audio to {self.sample_rate}Hz mono WAV")
            ffmpeg.run(stream, overwrite_output=True)

            # Clean up temporary file
            os.unlink(downloaded_file)

            logger.info(f"Audio saved to: {output_file}")
            return str(output_file)

        except DownloadError as e:
            logger.error(f"Failed to download audio: {str(e)}")
            raise
        except ffmpeg.Error as e:
            logger.error(
                f"Failed to convert audio: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise


def download_audio(url: str, output_dir: Optional[str] = None,
                   output_name: Optional[str] = None,
                   sample_rate: int = 16000) -> str:
    """
    Convenience function to download audio from a URL.

    Args:
        url: URL of the audio source
        output_dir: Optional directory to save the file
        output_name: Optional name for the output file (without extension)
        sample_rate: Target sample rate in Hz (default: 16kHz)

    Returns:
        str: Path to the downloaded and converted audio file
    """
    downloader = AudioDownloader(output_dir, sample_rate)
    return downloader.download(url, output_name)


if __name__ == "__main__":
    import argparse

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Download audio from a web source and convert for RTMP streaming"
    )
    parser.add_argument("url", help="URL of the audio source")
    parser.add_argument(
        "--output-dir", help="Directory to save the downloaded file")
    parser.add_argument(
        "--output-name", help="Name for the output file (without extension)")
    parser.add_argument("--sample-rate", type=int, default=16000,
                        help="Target sample rate in Hz")

    args = parser.parse_args()

    try:
        output_file = download_audio(
            args.url,
            output_dir=args.output_dir,
            output_name=args.output_name,
            sample_rate=args.sample_rate
        )
        print(f"Successfully downloaded and converted: {output_file}")
    except Exception as e:
        logger.error(str(e))
        exit(1)
