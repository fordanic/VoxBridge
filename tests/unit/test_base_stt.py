import pytest
import numpy as np

from src.stt.base_stt import BaseSTT


class DummySTT(BaseSTT):
    # Allow passing config overrides for testing
    def __init__(self, config_override=None):
        super().__init__()
        if config_override:
            # Patch config and re-initialize relevant attributes
            self.config = config_override
            # Re-apply config-dependent attributes
            rtmp_config = self.config.get("stt", {}).get("rtmp", {})
            self.rtmp_url = rtmp_config.get("url")
            self.sample_rate = rtmp_config.get("sample_rate", 16000)
            self.chunk_size = rtmp_config.get("chunk_size", 0.5)
            agc_config = self.config.get("stt", {}).get("agc", {})
            self.agc_enabled = agc_config.get("enabled", False)
            self.target_level = agc_config.get("target_level", -23)
            self.max_gain = agc_config.get("max_gain", 30)
            self.min_gain = agc_config.get("min_gain", -10)
            dict_config = self.config.get("stt", {}).get("dictionary", {})
            self.dict_enabled = dict_config.get("enabled", False)
            self.custom_words = dict_config.get("custom_words", [])
            self.word_boost = dict_config.get("word_boost", 1)
            self.case_sensitive = dict_config.get("case_sensitive", False)
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


class TestDummySTT:
    """Test suite for DummySTT and BaseSTT behavior."""

    @pytest.fixture
    def dummy(self):
        # Provide a config with AGC and dictionary enabled for coverage
        config = {
            "stt": {
                "agc": {"enabled": True, "target_level": -20, "max_gain": 10, "min_gain": -5},
                "dictionary": {"enabled": True, "custom_words": ["Amen", "Hallelujah"], "case_sensitive": False},
            }
        }
        return DummySTT(config_override=config)

    @pytest.fixture
    def audio_chunk(self):
        # Return a simple int16 numpy array simulating PCM audio
        return (np.random.rand(16000) * 32767).astype(np.int16)

    def test_transcribe_returns_hardcoded_string(self, dummy, audio_chunk):
        # Arrange done by fixtures
        # Act
        result = dummy.transcribe(audio_chunk)
        # Assert
        assert isinstance(result, str)
        assert "test transcription" in result
        assert "DummySTT" in result

    def test_transcribe_applies_dictionary(self, dummy, audio_chunk):
        # Act
        result = dummy.transcribe(audio_chunk)
        # Assert dictionary words are corrected to custom casing
        assert "Amen" in result
        assert "Hallelujah" in result

    def test_agc_is_applied(self, dummy, audio_chunk, monkeypatch):
        # Arrange: Patch apply_agc to check it is called
        called = {}
        orig_apply_agc = dummy.apply_agc

        def fake_apply_agc(chunk):
            called['yes'] = True
            return orig_apply_agc(chunk)
        monkeypatch.setattr(dummy, "apply_agc", fake_apply_agc)
        # Act
        dummy.transcribe(audio_chunk)
        # Assert
        assert called.get('yes') is True

    def test_base_stt_apply_agc(self, audio_chunk):
        # Arrange: Use BaseSTT directly with AGC enabled
        config = {"stt": {"agc": {"enabled": True,
                                  "target_level": -10, "max_gain": 5, "min_gain": -5}}}
        base = BaseSTT()
        base.config = config
        base.agc_enabled = True
        base.target_level = -10
        base.max_gain = 5
        base.min_gain = -5
        # Act
        processed = base.apply_agc(audio_chunk)
        # Assert
        assert processed.shape == audio_chunk.shape
        assert processed.dtype == audio_chunk.dtype

    def test_base_stt_apply_dictionary(self):
        # Arrange
        config = {"stt": {"dictionary": {"enabled": True,
                                         "custom_words": ["Amen"], "case_sensitive": False}}}
        base = BaseSTT()
        base.config = config
        base.dict_enabled = True
        base.custom_words = ["Amen"]
        base.case_sensitive = False
        text = "amen and Amen and AMEN"
        # Act
        result = base.apply_dictionary(text)
        # Assert
        assert "Amen" in result
        assert result.count("Amen") >= 1

    def test_base_stt_transcribe_not_implemented(self, audio_chunk):
        # Arrange
        base = BaseSTT()
        # Act & Assert
        with pytest.raises(NotImplementedError):
            base.transcribe(audio_chunk)
