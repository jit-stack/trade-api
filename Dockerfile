# --- Base image ---
FROM python:3.12-slim

# Don't buffer stdout/stderr — logs show up immediately (important for Docker/K8s logs)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps first (separate layer) so Docker caches this step
# and doesn't reinstall every time only the app code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the actual application code
COPY app/ ./app/

EXPOSE 8000

# Basic container-level health check
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
