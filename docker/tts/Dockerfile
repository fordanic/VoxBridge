FROM voxbridge-base:latest

WORKDIR /app

# TTS-specific dependencies
COPY docker/tts/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy TTS service code
COPY src/tts ./tts
COPY src/common ./common

ENV SERVICE_NAME=tts
EXPOSE 5002

CMD ["python", "-m", "tts.server"]