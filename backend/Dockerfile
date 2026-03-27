FROM python:3.11-slim

WORKDIR /workspace

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install backend Python dependencies
COPY backend/requirements.txt /tmp/backend_requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend_requirements.txt

# Install workspace-level requirements (agents etc.)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt || true

# Copy the entire workspace
COPY . .

EXPOSE 8000
CMD ["sh", "-c", "cd /workspace/backend && python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]
