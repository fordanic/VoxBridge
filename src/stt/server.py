from typing import Any, Dict, Optional, Tuple

import numpy as np

from src.common.base_service import BaseService


class BaseSTT(BaseService):
    def __init__(self):
        super().__init__("stt")
        # Get AGC settings from config
        self.agc_enabled = self.config.get("stt", {}).get(
            "agc", {}).get("enabled", False)
        self.target_level = self.config.get("stt", {}).get(
            "agc", {}).get("target_level", -23)
        self.max_gain = self.config.get("stt", {}).get(
            "agc", {}).get("max_gain", 30)
        self.min_gain = self.config.get("stt", {}).get(
            "agc", {}).get("min_gain", -10)

        # Get dictionary settings from config
        dict_config = self.config.get("stt", {}).get("dictionary", {})
        self.dict_enabled = dict_config.get("enabled", False)
        self.custom_words = dict_config.get("custom_words", [])
        self.word_boost = dict_config.get("word_boost", 1)
        self.case_sensitive = dict_config.get("case_sensitive", False)

        if self.dict_enabled:
            self.logger.info(
                "Custom dictionary enabled with %d words (boost: %d, case_sensitive: %s)",
                len(self.custom_words), self.word_boost, self.case_sensitive
            )

    def apply_agc(self, audio_chunk: np.ndarray) -> np.ndarray:
        """
        Apply Automatic Gain Control to the audio chunk.

        Args:
            audio_chunk: A numpy array containing audio data in PCM format

        Returns:
            np.ndarray: The audio chunk with adjusted gain
        """
        if not self.agc_enabled:
            return audio_chunk

        # Convert to float32 for processing
        audio_float = audio_chunk.astype(np.float32)

        # Calculate current RMS level in dB
        rms = np.sqrt(np.mean(np.square(audio_float)))
        current_level = 20 * np.log10(rms) if rms > 0 else -120

        # Calculate required gain
        required_gain = self.target_level - current_level
        required_gain = max(min(required_gain, self.max_gain), self.min_gain)

        # Apply gain
        gain_factor = np.power(10, required_gain / 20)
        audio_adjusted = audio_float * gain_factor

        # Clip to prevent overflow
        audio_adjusted = np.clip(audio_adjusted, -1.0, 1.0)

        self.logger.debug(
            "AGC: current_level=%.2f dB, applied_gain=%.2f dB",
            current_level, required_gain
        )

        # Convert back to original dtype
        return (audio_adjusted * np.iinfo(audio_chunk.dtype).max).astype(audio_chunk.dtype)

    def transcribe(self, audio_chunk: np.ndarray) -> str:
        """
        Transcribe an audio chunk to text.

        Args:
            audio_chunk: A numpy array containing audio data in PCM format

        Returns:
            str: The transcribed text

        Raises:
            NotImplementedError: This is a base class method that should be overridden
        """
        # Apply AGC if enabled before transcription
        if self.agc_enabled:
            audio_chunk = self.apply_agc(audio_chunk)
        raise NotImplementedError("Subclasses must implement transcribe()")

    def cleanup(self) -> None:
        """Cleanup resources used by the STT service"""
        self.logger.info("Cleaning up STT service")

    def health_check(self) -> Dict[str, Any]:
        """Check the health of the STT service"""
        return {
            "status": "healthy" if self.running else "unhealthy",
            "service": self.service_name,
            "details": {
                "running": self.running,
                "agc_enabled": self.agc_enabled,
                "dictionary_enabled": self.dict_enabled,
                "dictionary_words": len(self.custom_words) if self.dict_enabled else 0
            }
        }

    def get_dictionary_words(self) -> list[str]:
        """
        Get the list of custom dictionary words.

        Returns:
            list[str]: List of custom words, normalized according to case sensitivity settings
        """
        if not self.dict_enabled:
            return []

        if self.case_sensitive:
            return self.custom_words
        return [word.lower() for word in self.custom_words]

    def apply_dictionary(self, text: str) -> str:
        """
        Apply dictionary-based corrections to the transcribed text.
        This is a base implementation that corrects word casing based on the dictionary.
        Subclasses may override this to implement more sophisticated dictionary usage.

        Args:
            text: The text to process

        Returns:
            str: The processed text with dictionary corrections applied
        """
        if not self.dict_enabled or not text:
            return text

        # In base implementation, just fix casing of known words
        result = text
        for word in self.custom_words:
            if not self.case_sensitive:
                pattern = fr'\b{word.lower()}\b'
                result = result.replace(word.lower(), word)
            else:
                result = result.replace(word.lower(), word)

        return result

    def _run_service_loop(self) -> None:
        """Main service loop - in STT this is handled by transcribe() calls"""
        pass


class DummySTT(BaseSTT):
    """
    A dummy STT implementation that returns a hardcoded string.
    Used for testing the STT pipeline without actual speech recognition.
    """

    def transcribe(self, audio_chunk: np.ndarray) -> str:
        """
        Return a hardcoded string regardless of input audio.

        Args:
            audio_chunk: A numpy array containing audio data in PCM format

        Returns:
            str: A hardcoded test string
        """
        if self.agc_enabled:
            audio_chunk = self.apply_agc(audio_chunk)

        self.logger.debug(
            "DummySTT received audio chunk of shape: %s", audio_chunk.shape)

        # Return a test string that includes some dictionary words in wrong case
        test_text = "this is a test transcription with amen and hallelujah from DummySTT."

        # Apply dictionary-based corrections if enabled
        if self.dict_enabled:
            test_text = self.apply_dictionary(test_text)
            self.logger.debug("Applied dictionary corrections: %s", test_text)

        return test_text
