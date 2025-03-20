# VoxBridge TODO

## 1. Project Skeleton & Configuration
- [x] 1. Create Dockerfiles for each major service (STT, Translation, TTS, Streaming, Admin).
- [x] 2. Create a docker-compose.yml file for orchestrating all services.
- [x] 3. Create a config.yaml file (initially placeholders):
   - admin credentials
   - STT, translation, TTS engine settings
   - logging level
   - streaming settings (RTMP URL, streaming protocol)
   - language pairs configuration (Swedish → English, Swedish → French, etc.)
   - branding customization settings (logo, colors)
- [x] 4. Create a basic Python (or Node.js) skeleton to load config.yaml and print a startup message.

## 2. STT Integration
### 2.1 Base STT Interface
- [ ] 1. Create a `BaseSTT` interface/class with a method `transcribe(audio_chunk) -> str`.
- [ ] 2. Implement a `DummySTT` returning a hardcoded string for testing.
- [ ] 3. Update the main application flow to:
   - Read config.yaml
   - Instantiate the chosen STT engine
   - Fall back to DummySTT if none is set
- [ ] 4. Implement automatic gain control (AGC) if supported by the STT engine
- [ ] 5. Add support for custom dictionaries configuration

### 2.2 RTMP Reader
- [ ] 1. Create `audio_in/rtmp_reader.py` that uses ffmpeg (via ffmpeg-python) or GStreamer to read from the RTMP URL and produce small PCM chunks.
- [ ] 2. Integrate the reader with `DummySTT` to prove the pipeline works (print transcribed text).
- [ ] 3. Handle stream interruptions gracefully, logging a warning on disconnect.
- [ ] 4. Implement automatic reconnection to RTMP stream if disconnected.

### 2.3 Real STT Engines
- [ ] 1. Implement `GoogleSTT(BaseSTT)` using google-cloud-speech.
- [ ] 2. Implement `VoskSTT(BaseSTT)` for on-premise speech recognition.
- [ ] 3. Implement `WhisperSTT(BaseSTT)` for on-premise speech recognition.
- [ ] 4. Provide chunked or streaming transcription logic.
- [ ] 5. Configure environment variables for cloud service credentials.
- [ ] 6. Update Docker configurations/requirements accordingly.
- [ ] 7. Confirm end-to-end functionality:
   - RTMP → STT Engine → console output

## 3. Translation Integration
### 3.1 Base Translator Interface
- [ ] 1. Create a `BaseTranslator` interface/class with `translate_text(text, source_lang, target_lang) -> str`.
- [ ] 2. Implement a `DummyTranslator` that echoes or appends "(translated)".
- [ ] 3. Integrate translator calls in the main flow (STT → Translator), printing translated results.
- [ ] 4. Add support for custom translation rules configuration

### 3.2 Cloud Translation Engines
- [ ] 1. Implement `GoogleTranslate(BaseTranslator)` using google-cloud-translate.
- [ ] 2. Implement `AWSTranslate(BaseTranslator)` using AWS Translate.
- [ ] 3. Implement `MicrosoftTranslate(BaseTranslator)` using Azure Translator.
- [ ] 4. Add error handling for timeouts or invalid responses.
- [ ] 5. Update Docker and config.yaml to allow selection of translator type.
- [ ] 6. Test that final console output is translated text.

### 3.3 On-Premise Translation Engines
- [ ] 1. Implement `MarianMT(BaseTranslator)` for on-premise translation.
- [ ] 2. Implement `OpenNMT(BaseTranslator)` for on-premise translation.
- [ ] 3. Update Docker and config.yaml for on-premise translation options.
- [ ] 4. Test on-premise translation functionality with various language pairs.

## 4. TTS Integration
### 4.1 Base TTS Interface
- [ ] 1. Create a `BaseTTS` interface/class with `synthesize_speech(text, language) -> binary audio`.
- [ ] 2. Implement a `DummyTTS` returning silent or beep audio for testing.
- [ ] 3. Integrate into the main pipeline so that after translation, TTS is invoked, and the resulting audio is saved to a file (e.g., out.opus).

### 4.2 Cloud TTS Engines
- [ ] 1. Implement `GoogleTTS(BaseTTS)` using Google Text-to-Speech.
- [ ] 2. Implement `PollyTTS(BaseTTS)` using AWS Polly.
- [ ] 3. Implement `AzureTTS(BaseTTS)` using Microsoft Azure TTS.
- [ ] 4. Support streaming or chunked TTS output if possible.
- [ ] 5. Update Docker and config.yaml for TTS engine selection.
- [ ] 6. Configure audio quality settings via YAML.
- [ ] 7. Confirm end-to-end pipeline:
   - RTMP → STT → Translator → TTS → Audio file

### 4.3 On-Premise TTS Engines
- [ ] 1. Implement `CoquiTTS(BaseTTS)` for on-premise TTS.
- [ ] 2. Implement `PiperTTS(BaseTTS)` for on-premise TTS.
- [ ] 3. Update Docker and config.yaml for on-premise TTS options.

## 5. Real-Time Streaming & Captions
- [ ] 1. Decide on WebRTC or Low-Latency DASH for delivering near-real-time audio.
- [ ] 2. Implement a minimal streaming server (`streaming/stream_server.py`).
- [ ] 3. Create a simple web client (HTML/JS) that connects to the stream:
   - Plays audio in near real-time.
   - Displays text captions (via WebSocket or data channel).
   - Allows users to select their preferred language.
   - Provides a toggle for enabling/disabling captions.
- [ ] 4. Integrate TTS output so that each chunk is pushed to the streaming server along with the translated text.
- [ ] 5. Test multiple concurrent translations (Swedish → English, Swedish → French).

## 6. Admin Panel
- [ ] 1. Set up a small Flask or Node.js server in `admin/server.py`.
- [ ] 2. Secure with a single admin password from config.yaml (basic session handling).
- [ ] 3. Provide routes to:
   - Display and change engine selections (STT/TTS/Translator)
   - Show system health
   - Manual restart of containers or processes
   - Display logs (read from local log file)
- [ ] 4. Ensure brand customization (logo/colors) can be set in config.yaml.

## 7. Error Handling & Logging
- [ ] 1. Implement basic error logging stored locally.
- [ ] 2. Create error handling for service failures.
- [ ] 3. Set up logging rotation to prevent disk space issues.
- [ ] 4. Ensure logs are accessible through the admin panel.

## 8. Integration & Testing
- [ ] 1. Write unit tests for STT, Translation, TTS modules (e.g., pytest).
- [ ] 2. Implement end-to-end tests that feed in sample audio and expect correct translated speech out.
- [ ] 3. Measure and log latency to confirm ~1–3 seconds.
- [ ] 4. Test concurrency for multiple simultaneous translations (e.g., Swedish→English, Swedish→French).
- [ ] 5. Test failure scenarios (RTMP stream interruption, service crashes, incorrect configs).
- [ ] 6. Final performance tests, error handling tests, and cleanup.

## 9. Deployment & Documentation
- [ ] 1. Finalize Docker orchestration with docker-compose.
- [ ] 2. Create setup documentation for on-premise deployment.
- [ ] 3. Create user guide for admin panel and web client.
- [ ] 4. Document manual update procedure.
- [ ] 5. Create configuration reference guide for YAML settings.
