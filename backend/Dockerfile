# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Create unprivileged system user
RUN useradd -u 1000 -m appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy app package and clinical data files only
COPY app/ ./app/
COPY data/curated/ ./data/curated/
COPY data/lexicon/ ./data/lexicon/
COPY data/index/ ./data/index/
COPY data/intake/ ./data/intake/

# Ensure non-root ownership
RUN chown -R appuser:appuser /app

USER appuser

# Liveness probe via standard library urllib
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request, os; port = os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health', timeout=4)" || exit 1

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
