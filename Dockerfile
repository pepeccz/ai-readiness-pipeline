FROM python:3.12-slim

# Install Node.js for deck generation (generate-deck.mjs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash app
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Own by app user
RUN chown -R app:app /app
USER app

EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import requests; r=requests.get('http://localhost:8100/health'); exit(0 if r.ok else 1)"

CMD ["uvicorn", "webhook_service:app", "--host", "0.0.0.0", "--port", "8100"]
