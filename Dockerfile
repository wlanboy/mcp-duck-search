# Build stage
FROM python:3.12-slim AS builder

# Verhindert, dass Python .pyc Dateien schreibt und sorgt für sofortige Log-Ausgabe
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies in a virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim

# Umgebungsvariablen übernehmen
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    SEARXNG_URL=""

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser 

# Copy application files
COPY --chown=appuser:appuser main.py /app/
COPY --chown=appuser:appuser config.py /app/
COPY --chown=appuser:appuser search.py /app/

# Use non-root user
USER appuser

EXPOSE 9900

CMD ["python", "main.py"]