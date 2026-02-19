"""
HTTP client to send risk events to the backend with retry/backoff.
"""
import logging
import time
from typing import Optional

import httpx

from app.models import RiskEventPayload

logger = logging.getLogger(__name__)


class BackendClient:
    """Send risk events to backend with retry and exponential backoff."""

    def __init__(
        self,
        base_url: str,
        max_retries: int = 5,
        backoff_sec: float = 1.0,
        timeout_sec: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.backoff_sec = backoff_sec
        self.timeout_sec = timeout_sec
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(timeout=self.timeout_sec)
        return self._client

    def send_event(self, payload: RiskEventPayload) -> bool:
        """
        POST risk event to backend. Retries with exponential backoff on failure.
        Returns True if accepted, False otherwise.
        """
        url = f"{self.base_url}/api/v1/risk-events"
        body = payload.model_dump(mode="json")
        client = self._get_client()
        last_error = None
        for attempt in range(self.max_retries):
            try:
                r = client.post(url, json=body)
                if r.is_success:
                    logger.debug("Event sent to backend: %s", payload.type)
                    return True
                last_error = f"HTTP {r.status_code}"
                logger.warning("Backend returned %s for risk event", r.status_code)
            except httpx.RequestError as e:
                last_error = str(e)
                logger.warning("Backend request failed (attempt %s): %s", attempt + 1, e)
            if attempt < self.max_retries - 1:
                delay = self.backoff_sec * (2 ** attempt)
                time.sleep(delay)
        logger.error("Failed to send event after %s retries: %s", self.max_retries, last_error)
        return False

    def close(self):
        if self._client and not self._client.is_closed:
            self._client.close()
