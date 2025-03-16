# VoxBridge - Specification
## 1. Overview
This system provides real-time speech-to-speech translation for live church services, primarily translating Swedish to English and French while supporting additional languages via configuration. It uses an RTMP audio input, processes speech via speech-to-text (STT), translates it, and converts it back to speech using text-to-speech (TTS). Translated audio is streamed to users via a web app, where they can select their preferred language.

## 2. Core Features
### 2.1 Audio Input
- Source: Single RTMP audio stream from the church’s sound system.
- Fixed stream URL: Changing the source requires a system restart.
### 2.2 Speech-to-Text (STT)
- Support for both cloud-based and on-premise STT engines (e.g., Google Speech-to-Text, Vosk, Whisper).
- Low-latency processing (1-3 seconds delay max).
- Custom dictionaries supported if the STT engine allows it.
- No multi-speaker recognition; treats all speech as a single source.
- Automatic gain control (AGC) enabled if supported.
- No text pre-processing.
### 2.3 Translation
- Supports both cloud-based (Google Translate, AWS, Microsoft) and on-premise (MarianMT, OpenNMT) translation engines.
- Primary translations: Swedish → English, Swedish → French.
- Fully configurable language pairs via YAML.
- Custom translation rules supported if the translation engine allows it.
- No caching of translations.
### 2.4 Text-to-Speech (TTS)
- Supports both cloud-based (Google TTS, AWS Polly, Azure) and on-premise (Coqui TTS, Piper) solutions.
- Uses standard voices (no custom voice models).
- Single fixed audio format (Opus).
- Configurable audio quality settings via YAML.
### 2.5 Audio Streaming to Users
- Live streaming via a web app.
- Uses WebRTC or Low-Latency DASH for real-time delivery.
- Multiple concurrent translations supported, allowing users to select their preferred language.
- No playback controls (play/pause/volume) for users.
- Automatic reconnection if the RTMP stream is lost.
### 2.6 Captions
- Real-time translated text displayed as captions.
- Optional toggle for users to enable/disable captions.
### 2.7 Admin Panel
- Minimal UI with a single admin account (password stored in YAML).
- Status page displaying the health of key services (STT, translation, TTS, streaming).
- Controls for modifying language settings and selecting STT/TTS engines.
- Manual restart button for system services.
- Basic error logging (stored locally).
- No notifications or alerts for service failures.
- Basic branding customization (logo, colors).
- No localization (admin panel in English only).

## 3. Deployment and Architecture
### 3.1 Deployment
- On-premise deployment using Linux with Docker.
- Manual software updates (no automatic updates).
- YAML configuration for system settings.
### 3.2 System Architecture
- Audio Ingestion: RTMP audio input from the church’s sound system.
- STT Processing: Convert speech to text using configured STT engine.
- Translation Processing: Translate text using the configured translation engine.
- TTS Processing: Convert translated text into speech using TTS engine.
- Audio Streaming: Deliver translated speech via WebRTC or Low-Latency DASH.
- Admin Panel: UI for managing settings, monitoring system status, and restarting services.

## 4. Data Handling
- No data storage beyond logs.
- Error and performance logs stored locally.
- No recording or caching of audio, translations, or user interactions.
- No API integrations (standalone system).
- No automatic backups of logs or configurations.

## 5. Error Handling
- Basic error logging stored locally.
- No real-time notifications for failures.
- No automatic fallback mechanisms if a service (STT/TTS/translation) fails.
- No automatic reconnection to RTMP stream if disconnected.

## 6. Security
- Simple password authentication for the admin panel.
- No role-based access control (single admin user).
- No remote access (admin panel accessible only on-site).
- No session timeouts (admin stays logged in indefinitely).
- Password changes must be done via YAML file.

## 7. Testing Plan
### 7.1 Unit Tests
- STT Engine Integration: Ensure speech is accurately transcribed.
- Translation Engine: Validate correctness of translations.
- TTS Output: Verify that translated text is correctly synthesized.
- RTMP Input Handling: Ensure stable audio ingestion.
### 7.2 System Tests
- End-to-End Speech Translation Pipeline: Verify the full workflow from RTMP input to translated speech output.
- Latency Check: Ensure end-to-end delay remains within the 1-3 second target.
- Multiple Concurrent Translations: Confirm users can select different languages.
- Admin Panel Functionality: Test configuration changes and service restarts.
- Web App UI Testing: Ensure language selection and caption toggles work.
### 7.3 Failure Scenarios
- RTMP Stream Interruption: Verify that the system stops gracefully when the stream disconnects.
- Service Crashes: Ensure logging captures errors properly.
- Incorrect Configurations: Test handling of invalid YAML configurations.

## 8. Future Considerations
- Support for scalability (if needed later).
- Option to add remote access and API integrations.
- Possibility of integrating advanced monitoring tools.
- Potential for adding text-based manual overrides in the admin panel.