FROM voxbridge-base:latest

WORKDIR /app

# STT-specific dependencies
COPY docker/stt/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy STT service code
COPY src/stt ./stt
COPY src/common ./common

ENV SERVICE_NAME=stt
EXPOSE 5000

CMD ["python", "-m", "stt.server"]