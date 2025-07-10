import numpy as np
from google.cloud import speech

from src.stt.base_stt import BaseSTT


class GoogleSTT(BaseSTT):
    """
    Google Cloud Speech-to-Text implementation.
    Requires GOOGLE_APPLICATION_CREDENTIALS environment variable set to the path of
    service account key file.
    """

    def __init__(self):
        super().__init__()
        self.client = speech.SpeechClient()

        # Get Google-specific settings from config
        google_config = self.config.get("stt", {}).get("google", {})
        self.language_code = google_config.get("language_code", "sv-SE")
        self.model = google_config.get("model", "default")
        self.use_enhanced = google_config.get("use_enhanced", True)

        # Configure recognition settings
        self.recognition_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.sample_rate,
            language_code=self.language_code,
            model=self.model,
            use_enhanced=self.use_enhanced
        )

        # Add custom dictionary if enabled
        if self.dict_enabled:
            speech_context = speech.SpeechContext(
                phrases=self.get_dictionary_words(),
                boost=self.word_boost
            )
            self.recognition_config.speech_contexts.append(speech_context)
            self.logger.info(
                f"Added {len(self.get_dictionary_words())} words to speech context"
            )

        # Configure streaming settings
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.recognition_config,
            interim_results=False
        )

    def streaming_transcribe(self, audio_chunks):
        """
        Transcribe a stream of audio chunks using Google Cloud Speech-to-Text streaming API.
        Args:
            audio_chunks: Iterable of numpy arrays containing audio data in PCM int16 format
        Yields:
            str: The transcribed text for each final result
        """
        try:
            def request_generator():
                for chunk in audio_chunks:
                    if chunk is None or chunk.size == 0:
                        continue
                    # Ensure int16 PCM, mono
                    if chunk.dtype != np.int16:
                        self.logger.debug("Converting audio chunk to int16 PCM format")
                        chunk = (chunk * 32767.0).clip(-32768, 32767).astype(np.int16)
                    yield speech.StreamingRecognizeRequest(audio_content=chunk.tobytes())

            self.logger.debug("Starting streaming transcription for audio chunks")
            responses = self.client.streaming_recognize(
                self.streaming_config,
                request_generator()
            )
            for response in responses:
                for result in response.results:
                    if result.is_final:
                        transcript = result.alternatives[0].transcript
                        yield self.apply_dictionary(transcript) if self.dict_enabled else transcript
        except Exception as e:
            self.logger.error(f"Streaming transcription error: {str(e)}")
            return

    def transcribe(self, audio_chunk: np.ndarray) -> str:
        """
        Buffer audio chunks and send them as a stream to Google STT for transcription.
        """
        # Buffer for streaming
        if not hasattr(self, '_stream_buffer'):
            self._stream_buffer = []
        # Only buffer valid chunks
        if audio_chunk is not None and audio_chunk.size > 0:
            # Ensure mono, int16
            if audio_chunk.dtype != np.int16:
                audio_chunk = (audio_chunk * 32767.0).clip(-32768, 32767).astype(np.int16)
            self._stream_buffer.append(audio_chunk)

        # If buffer is large enough, send to Google STT
        # (e.g., every 1 second worth of audio)
        min_buffer_size = int(self.sample_rate * 1.0)  # 1 second
        total_samples = sum(chunk.shape[0] for chunk in self._stream_buffer)
        if total_samples < min_buffer_size:
            return ""  # Not enough audio yet

        # Concatenate all buffered chunks
        buffered_audio = np.concatenate(self._stream_buffer, axis=0)
        # Split into 1s chunks for streaming
        chunk_size = min_buffer_size
        audio_chunks = [buffered_audio[i:i+chunk_size] for i in range(0, len(buffered_audio), chunk_size)]
        self._stream_buffer = []  # Clear buffer after sending

        # Use streaming_transcribe generator
        results = list(self.streaming_transcribe(audio_chunks))
        if results:
            return results[-1]  # Return the last transcript
        return ""

    def stop(self) -> None:
        """Stop the STT service."""
        if self.running:
            self.logger.info("Stopping Google STT service")
            self.running = False
