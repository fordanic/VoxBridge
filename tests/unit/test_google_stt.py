import pytest
import numpy as np

from src.stt.google_stt import GoogleSTT


from unittest import mock


class TestGoogleSTT:
    """
    Unit tests for GoogleSTT class.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        # Patch Google Cloud Speech client
        self.speech_client_patch = mock.patch(
            'src.stt.google_stt.speech.SpeechClient')
        self.mock_client = self.speech_client_patch.start()()

        # Patch BaseSTT.__init__ to set up required instance attributes
        def fake_init(self):
            self.config = {
                "stt": {
                    "google": {
                        "language_code": "en-US",
                        "model": "default",
                        "use_enhanced": True
                    }
                }
            }
            self.logger = mock.Mock()
            self.sample_rate = 16000
            self.dict_enabled = False
            self.agc_enabled = False
            self.word_boost = 10.0
            self.running = True
        self.base_init_patch = mock.patch(
            'src.stt.base_stt.BaseSTT.__init__', fake_init)
        self.base_init_patch.start()

        # Patch get_dictionary_words and apply_dictionary
        self.get_dict_patch = mock.patch(
            'src.stt.base_stt.BaseSTT.get_dictionary_words', return_value=["foo", "bar"])
        self.get_dict_patch.start()
        self.apply_dict_patch = mock.patch(
            'src.stt.base_stt.BaseSTT.apply_dictionary', side_effect=lambda x: x)
        self.apply_dict_patch.start()
        # Patch apply_agc
        self.apply_agc_patch = mock.patch(
            'src.stt.base_stt.BaseSTT.apply_agc', side_effect=lambda x: x)
        self.apply_agc_patch.start()
        yield
        mock.patch.stopall()

    def test_init_sets_config_and_client(self):
        stt = GoogleSTT()
        assert stt.language_code == "en-US"
        assert stt.model == "default"
        assert stt.use_enhanced is True
        assert hasattr(stt, "client")
        assert hasattr(stt, "recognition_config")
        assert hasattr(stt, "streaming_config")

    def test_transcribe_returns_transcript(self):
        stt = GoogleSTT()
        dummy_audio = np.zeros(16000, dtype=np.int16)
        # Mock response from streaming_recognize
        mock_alt = mock.Mock(transcript="hello world")
        mock_result = mock.Mock(is_final=True, alternatives=[mock_alt])
        mock_response = mock.Mock(results=[mock_result])
        stt.client.streaming_recognize.return_value = [mock_response]
        transcript = stt.transcribe(dummy_audio)
        assert transcript == "hello world"
        stt.client.streaming_recognize.assert_called()

    def test_transcribe_returns_empty_on_no_final_result(self):
        stt = GoogleSTT()
        dummy_audio = np.zeros(16000, dtype=np.int16)
        # No final result
        mock_result = mock.Mock(is_final=False, alternatives=[])
        mock_response = mock.Mock(results=[mock_result])
        stt.client.streaming_recognize.return_value = [mock_response]
        transcript = stt.transcribe(dummy_audio)
        assert transcript == ""

    def test_transcribe_returns_empty_on_exception(self):
        stt = GoogleSTT()
        dummy_audio = np.zeros(16000, dtype=np.int16)
        stt.client.streaming_recognize.side_effect = Exception("fail")
        transcript = stt.transcribe(dummy_audio)
        assert transcript == ""
        stt.logger.error.assert_called()

    def test_transcribe_applies_agc_if_enabled(self):
        stt = GoogleSTT()
        stt.agc_enabled = True
        dummy_audio = np.zeros(16000, dtype=np.int16)
        mock_alt = mock.Mock(transcript="foo")
        mock_result = mock.Mock(is_final=True, alternatives=[mock_alt])
        mock_response = mock.Mock(results=[mock_result])
        stt.client.streaming_recognize.return_value = [mock_response]
        with mock.patch.object(stt, 'apply_agc', wraps=stt.apply_agc) as agc_method:
            stt.transcribe(dummy_audio)
            agc_method.assert_called()

    def test_transcribe_applies_dictionary_if_enabled(self):
        stt = GoogleSTT()
        stt.dict_enabled = True
        dummy_audio = np.zeros(16000, dtype=np.int16)
        mock_alt = mock.Mock(transcript="foo")
        mock_result = mock.Mock(is_final=True, alternatives=[mock_alt])
        mock_response = mock.Mock(results=[mock_result])
        stt.client.streaming_recognize.return_value = [mock_response]
        with mock.patch.object(stt, 'apply_dictionary', wraps=stt.apply_dictionary) as dict_method:
            stt.transcribe(dummy_audio)
            dict_method.assert_called()

    def test_stop_sets_running_false_and_logs(self):
        stt = GoogleSTT()
        stt.running = True
        stt.logger = mock.Mock()
        stt.stop()
        assert stt.running is False
        stt.logger.info.assert_called_with("Stopping Google STT service")
