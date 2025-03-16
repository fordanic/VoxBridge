# VoxBridge - Code Generation Prompts

## Prompt 1: Create the Project Skeleton
```text
You are building a Docker-based Python project called "VoxBridge" to provide real-time speech translation.
1. Create a Python package structure with these empty directories: stt, translation, tts, streaming, admin.
2. Create a `requirements.txt` with placeholders for common libraries (ffmpeg-python, pyyaml, etc.).
3. Create a `docker-compose.yml` with separate services for STT, translation, TTS, streaming, and admin (empty placeholders, no real commands yet).
4. Create a `config.yaml` that will store settings for stt, translation, tts, admin credentials, and streaming. For now, just include placeholders.
5. Print or echo any instructions for how to build or run the empty containers.

Write all necessary Dockerfiles, a minimal `main.py` that prints “VoxBridge is starting”, and ensure everything can be built and run without errors, even though each service is just a placeholder.
```

## Prompt 2: Implement a Dummy STT Module
```text
We now have a skeleton for VoxBridge.
1. Implement a base STT interface (`BaseSTT`) in `stt/base_stt.py` with a method `transcribe(audio_chunk) -> str`.
2. Implement a `DummySTT(BaseSTT)` in `stt/dummy_stt.py` that always returns the string “Dummy transcription” for any audio chunk.
3. Update `main.py` to load the configuration from `config.yaml` and instantiate either DummySTT or print a warning if no STT is specified.
4. Show how to run a quick test by passing a small array of bytes to `DummySTT.transcribe` and print the returned text.
```

## Prompt 3: RTMP Audio Reader + Dummy STT Integration
```text
Next, we want real-time audio ingestion from an RTMP source:
1. Create a module `audio_in/rtmp_reader.py` that uses ffmpeg (via ffmpeg-python) to read from an RTMP URL and yield small PCM chunks.
2. In `main.py`, read from the RTMP stream and feed the chunks to `DummySTT` for transcription. Print the transcriptions to the console.
3. Add basic error handling and logging. If the RTMP stream stops, log a warning but keep the application running.
4. Show how to configure the RTMP URL in `config.yaml`.
```

## Prompt 4: Implement Real STT (e.g. Google STT)
```text
Now we want to integrate Google Cloud STT:
1. Add a `GoogleSTT(BaseSTT)` class in `stt/google_stt.py` that implements `transcribe(audio_chunk) -> str`, using google-cloud-speech.
2. In `main.py`, detect if `config.yaml` sets `stt.engine: "google"`. If so, initialize `GoogleSTT`. Otherwise, use the DummySTT.
3. Ensure you handle chunked audio properly: either buffer enough to send to Google in short streams, or use Google’s streaming recognition if feasible.
4. Update any Dockerfiles or requirements with the necessary Google libraries (google-cloud-speech).
5. Provide instructions for setting Google credentials in a secure place (e.g., an environment variable).
```

## Prompt 5: Implement a Dummy Translator + Integration
```text
We now have STT. Next is translation.
1. Create a translation interface `BaseTranslator` in `translation/base_translator.py` with `translate_text(text, source_lang, target_lang) -> str`.
2. Implement `DummyTranslator` in `translation/dummy_translator.py` that simply returns the original text plus “ (translated)”.
3. In `main.py`, read config to instantiate `DummyTranslator`. Pass the STT output to the translator. Print the results.
4. Confirm everything runs in Docker, and we see translations in the console.
```

## Prompt 6: Real Translation Integration (e.g. Google Translate)
```text
We need a real translator now:
1. Implement `GoogleTranslate(BaseTranslator)` in `translation/google_translate.py` using google-cloud-translate or REST API calls if needed.
2. In `main.py`, wire up the choice of `DummyTranslator` or `GoogleTranslate` from `config.yaml`.
3. Add logging to each translation call. Add error handling for timeouts or invalid responses.
4. Explain how to supply Google Translate credentials or use an API key.
5. Test end-to-end: RTMP -> Google STT -> Google Translate -> console output.
```

## Prompt 7: Implement a Dummy TTS + Basic Audio Output
```text
Now we add TTS:
1. Create `BaseTTS` in `tts/base_tts.py` with `synthesize_speech(text, language) -> binary audio`.
2. Implement `DummyTTS` in `tts/dummy_tts.py` that returns a short generated WAV/Opus buffer of silence.
3. Wire it into `main.py`: after we get translated text, pass it to DummyTTS, then just write the audio to disk as an output file (e.g., out.opus).
4. Confirm the system runs with the entire pipeline (STT->Translator->TTS) but TTS just saves a silent file.
5. Add any needed Dockerfile updates.
```

---

## Prompt 8: Real TTS Integration (e.g. AWS Polly or Coqui)
```text
Time for a real TTS:
1. Implement `PollyTTS` in `tts/polly_tts.py`, using boto3 or AWS SDK.
2. In `main.py`, if `config.yaml` has `tts.engine: "polly"`, use `PollyTTS`. Otherwise, use `DummyTTS`.
3. Implement buffering or streaming so we can handle partial TTS outputs as they become available.
4. Update Dockerfiles or requirements for AWS libraries.
5. Confirm that the end-to-end pipeline can produce real spoken output for short test phrases.
```

---

## Prompt 9: Real-Time Streaming & Captions
```text
We need to serve the audio and text in real time:
1. Choose WebRTC or LL-DASH. Implement a minimal server in `streaming/stream_server.py` that can push or serve low-latency audio.
2. In `main.py`, after TTS produces audio, send the audio chunks to the stream server.
3. Create a minimal web client (HTML/JS) that connects and plays the audio in near real-time.
4. Add a basic data channel or WebSocket to send text captions. Display them under the audio player.
5. Demonstrate a quick local test with Docker Compose to confirm the user can hear TTS output and see the text simultaneously.
```

## Prompt 10: Admin Panel
```text
Add an admin panel for configuration and monitoring:
1. Create a small Flask or Node.js server in `admin/server.py`.
2. Secure it with a single admin password from `config.yaml`.
3. Provide routes to get/set the current STT, translation, TTS engine, and languages.
4. Show a status page that pings each service.
5. Provide a “Restart” button or endpoint that triggers a container restart or process restart.
6. Include a minimal log viewer that reads a local log file and displays the last 100 lines.
```

## Prompt 11: Integration Testing + Final Checks
```text
We need final integration testing to ensure correctness and performance:
1. Write a set of automated unit tests (using pytest or similar) for STT, translation, and TTS.
2. Write an end-to-end test that sends an audio clip of Swedish into the pipeline and checks if the final TTS audio is in English or French.
3. Measure latency: log timestamps at each stage (STT, translation, TTS) to ensure ~1-3 seconds.
4. Test concurrency: run multiple streams with different target languages, confirm they do not interfere.
5. Provide scripts or instructions to run all these tests in Docker Compose.
```
