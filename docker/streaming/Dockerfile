FROM voxbridge-base:latest

WORKDIR /app

# Streaming-specific dependencies
COPY docker/streaming/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy streaming service code
COPY src/streaming ./streaming
COPY src/common ./common

ENV SERVICE_NAME=streaming
EXPOSE 1935 8080

CMD ["python", "-m", "streaming.server"]