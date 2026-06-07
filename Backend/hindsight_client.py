import os
import time
import json
from typing import List, Dict, Any, Optional

import requests


class HindsightHTTPClient:
    """Lightweight HTTP client wrapper for a Hindsight service.

    This client intentionally mirrors the interface of `HindsightDB` used
    in the codebase so agents can swap to a real service with minimal changes.
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("HINDSIGHT_API_KEY")
        self.timeout = timeout
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        retries = kwargs.pop("retries", 3)
        backoff = kwargs.pop("backoff", 0.5)
        for attempt in range(1, retries + 1):
            try:
                resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
                resp.raise_for_status()
                if resp.headers.get("content-type", "").lower().startswith("application/json"):
                    return resp.json()
                # fallback: attempt to parse JSON body even if content-type missing
                try:
                    return resp.json()
                except Exception:
                    return resp.text
            except requests.RequestException as e:
                if attempt == retries:
                    raise
                time.sleep(backoff * attempt)

    def query_incidents(self, query_text: str, limit: int = 2) -> List[Dict[str, Any]]:
        """Query incidents by text. Endpoint: GET /incidents?query=...&limit=..."""
        params = {"query": query_text, "limit": limit}
        try:
            data = self._request("GET", "/incidents", params=params)
            # Expect list of incidents
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            return []
        except Exception:
            return []

    def save_session(self, session_id: str, git_diff: str, metadata: Dict[str, Any]):
        """Index or save a session into Hindsight. Endpoint: POST /sessions"""
        payload = {
            "session_id": session_id,
            "metadata": metadata,
            "git_diff": git_diff
        }
        try:
            return self._request("POST", "/sessions", json=payload)
        except Exception:
            # Best-effort: do not raise for agent pipelines; return None
            return None

    def get_all_incidents(self) -> List[Dict[str, Any]]:
        """Return all incidents. Endpoint: GET /incidents"""
        try:
            data = self._request("GET", "/incidents", params={})
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            return []
        except Exception:
            return []


def default_client_from_env() -> HindsightHTTPClient:
    url = os.getenv("HINDSIGHT_URL", "http://localhost:8080")
    token = os.getenv("HINDSIGHT_API_KEY")
    return HindsightHTTPClient(url, api_key=token)
