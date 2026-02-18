"""
Sentinel Drive AI - Python microservice entrypoint.
Health check and future CV/risk endpoints.
"""
from fastapi import FastAPI

app = FastAPI(title="Sentinel Drive AI", version="0.1.0")


@app.get("/health")
def health():
    """Health check for Docker and orchestration."""
    return {"status": "UP", "service": "sentinel-drive-ai"}
