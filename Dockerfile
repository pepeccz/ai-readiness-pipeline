# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --ignore-scripts 2>/dev/null || npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python API + static files
FROM python:3.12-slim AS production
WORKDIR /app

# LibreOffice for docx→pdf conversion
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend source
COPY *.py ./
COPY *.md ./
COPY assets/ ./assets/
COPY app/ ./app/
COPY schemas/ ./schemas/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh

# Frontend build
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist/

# Non-root user + writable output dir + writable DB dir
RUN useradd -m -s /bin/bash app \
    && mkdir -p /app/output /app/app/data \
    && chmod +x /usr/local/bin/entrypoint.sh \
    && chown -R app:app /app
USER app

EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8100/api/health')"

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "webhook_service:app", "--host", "0.0.0.0", "--port", "8100"]
