FROM voxbridge-base:latest

WORKDIR /app

# STT-specific dependencies
COPY docker/stt/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy STT service code
COPY src/stt ./stt
COPY src/common ./common

# Create directory for Google Cloud credentials


ENV SERVICE_NAME=stt
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json
EXPOSE 5000

# Add README with credentials instructions
USER root
RUN echo "Google Cloud Credentials Setup:
1. Obtain a service account key file from Google Cloud Console
2. When running the container, mount your credentials file to /app/credentials/google-credentials.json
   Example: docker run -v /path/to/your/credentials.json:/app/credentials/google-credentials.json ...
" > /app/CREDENTIALS.md
USER voxbridge

CMD ["python", "-m", "stt.server"]
