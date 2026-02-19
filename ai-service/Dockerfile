# Sentinel Drive AI - Python microservice
FROM python:3.12-slim

WORKDIR /app

# OpenCV/MediaPipe runtime deps + curl for model download
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxcb1 libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code and dashboard static files
COPY app/ ./app/
COPY static/ ./static/

# Face Landmarker model (required for vision pipeline)
RUN curl -fSL -o /app/face_landmarker.task \
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task" \
    && chmod 644 /app/face_landmarker.task

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
