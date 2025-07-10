# Testing VoxBridge

## Testing Google STT

### Prerequisites

1. **Google Cloud Credentials**

   - Create a service account in Google Cloud Console
   - Download the JSON key file
   - Set environment variable:
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json
     ```

2. **Test Audio Data**
   You need a WAV file that matches these specifications:

   - Sample Rate: 16000 Hz
   - Channels: 1 (mono)
   - Format: PCM 16-bit

   To convert an audio file to the correct format:

   ```bash
   ffmpeg -i input.mp3 -ar 16000 -ac 1 -acodec pcm_s16le output.wav
   ```

### Running Tests

1. **Start the RTMP Server**

   ```bash
   cd tests/rtmp_server
   docker-compose up -d
   ```

2. **Stream Test Audio**
   In one terminal:

   ```bash
   ffmpeg -re -i test.wav -f flv rtmp://localhost/live/test
   ```

3. **Run the Test**
   In another terminal:
   ```bash
   python tests/test_google_stt.py
   ```

### Test Scenarios

The test will:

1. Initialize Google STT with streaming recognition
2. Process 30 seconds of audio from the RTMP stream
3. Log all transcribed text
4. Test custom dictionary functionality
5. Test AGC if enabled

### Expected Output

You should see:

1. Successful connection to RTMP stream
2. Transcribed text in the logs
3. No errors in STT processing
4. Clean shutdown of services

### Troubleshooting

1. **RTMP Connection Issues**

   - Verify RTMP server is running: `docker ps`
   - Check RTMP URL is correct
   - Ensure no port conflicts

2. **Google Credentials Issues**

   - Verify credentials file exists
   - Check environment variable is set
   - Ensure service account has proper permissions

3. **Audio Issues**
   - Confirm audio format matches requirements
   - Check if audio is playing (should hear it)
   - Verify audio contains speech
