FROM voxbridge-base:latest

WORKDIR /app

# Admin-specific dependencies
COPY docker/admin/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy admin service code
COPY src/admin ./admin
COPY src/common ./common

# Copy static assets
COPY src/admin/static ./admin/static
COPY src/admin/templates ./admin/templates

ENV SERVICE_NAME=admin
EXPOSE 3000

CMD ["python", "-m", "admin.server"]
