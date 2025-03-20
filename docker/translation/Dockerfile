FROM voxbridge-base:latest

WORKDIR /app

# Translation-specific dependencies
COPY docker/translation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy translation service code
COPY src/translation ./translation
COPY src/common ./common

ENV SERVICE_NAME=translation
EXPOSE 5001

CMD ["python", "-m", "translation.server"]