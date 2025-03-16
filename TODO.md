# VoxBridge TODO

## 1. Project Skeleton & Configuration
1. Initialize a version-controlled repository (Git).
2. Create Dockerfiles for each major service (STT, Translation, TTS, Streaming, Admin).
3. Create a docker-compose.yml file for orchestrating all services.
4. Create a config.yaml file (initially placeholders):
   - admin credentials
   - STT, translation, TTS engine settings
   - logging level
   - streaming settings (RTMP URL, streaming protocol)
5. Create a basic Python (or Node.js) skeleton to load config.yaml and print a startup message.

## 2. STT Integration
### 2.1 Base STT Interface
1. Create a `BaseSTT` interface/class with a method `transcribe(audio_chunk) -> str`.
2. Implement a `DummySTT` returning a hardcoded string for testing.
3. Update the main application flow to:
   - Read config.yaml
   - Instantiate the chosen STT engine
   - Fall back to DummySTT if none is set

### 2.2 RTMP Reader
1. Create `audio_in/rtmp_reader.py` that uses ffmpeg (via ffmpeg-python) or GStreamer to read from the RTMP URL and produce small PCM chunks.
2. Integrate the reader with `DummySTT` to prove the pipeline works (print transcribed text).
3. Handle stream interruptions gracefully, logging a warning on disconnect.

### 2.3 Real STT (e.g., Google STT)
1. Implement `GoogleSTT(BaseSTT)` using google-cloud-speech.
2. Provide chunked or streaming transcription logic.
3. Configure environment variables for Google credentials.
4. Update Docker configurations/requirements accordingly.
5. Confirm end-to-end functionality:
   - RTMP → GoogleSTT → console output

## 3. Translation Integration
### 3.1 Base Translator Interface
1. Create a `BaseTranslator` interface/class with `translate_text(text, source_lang, target_lang) -> str`.
2. Implement a `DummyTranslator` that echoes or appends “(translated)”.
3. Integrate translator calls in the main flow (STT → Translator), printing translated results.

### 3.2 Real Translator (e.g., Google Translate)
1. Implement `GoogleTranslate(BaseTranslator)` using google-cloud-translate or REST APIs.
2. Add error handling for timeouts or invalid responses.
3. Update Docker and config.yaml to allow selection of translator type (dummy or Google).
4. Test that final console output is translated text.

## 4. TTS Integration
### 4.1 Base TTS Interface
1. Create a `BaseTTS` interface/class with `synthesize_speech(text, language) -> binary audio`.
2. Implement a `DummyTTS` returning silent or beep audio for testing.
3. Integrate into the main pipeline so that after translation, TTS is invoked, and the resulting audio is saved to a file (e.g., out.opus).

### 4.2 Real TTS (e.g., AWS Polly or Coqui)
1. Implement `PollyTTS(BaseTTS)` using AWS SDK/boto3.
2. Support streaming or chunked TTS output if possible.
3. Update Docker and config.yaml for TTS engine selection.
4. Confirm end-to-end pipeline:
   - RTMP → STT → Translator → TTS → Audio file

## 5. Real-Time Streaming & Captions
1. Decide on WebRTC or Low-Latency DASH for delivering near-real-time audio.
2. Implement a minimal streaming server (`streaming/stream_server.py`).
3. Create a simple web client (HTML/JS) that connects to the stream:
   - Plays audio in near real-time.
   - Displays text captions (via WebSocket or data channel).
4. Integrate TTS output so that each chunk is pushed to the streaming server along with the translated text.

## 6. Admin Panel
1. Set up a small Flask or Node.js server in `admin/server.py`.
2. Secure with a single admin password from config.yaml (basic session handling).
3. Provide routes to:
   - Display and change engine selections (STT/TTS/Translator)
   - Show system health
   - Manual restart of containers or processes
   - Display logs (read from local log file)
4. Ensure brand customization (logo/colors) can be set in config.yaml.

## 7. Integration & Testing
1. Write unit tests for STT, Translation, TTS modules (e.g., pytest).
2. Implement end-to-end tests that feed in sample audio and expect correct translated speech out.
3. Measure and log latency to confirm ~1–3 seconds.
4. Test concurrency for multiple simultaneous translations (e.g., Swedish→English, Swedish→French).
5. Final performance tests, error handling tests, and cleanup.
