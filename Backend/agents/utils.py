import os
from langchain_groq import ChatGroq

try:
    # Prefer HTTP-backed client if HINDSIGHT_URL is set
    from hindsight_client import HindsightHTTPClient, default_client_from_env
except Exception:
    HindsightHTTPClient = None

from hindsight_db import HindsightDB


def get_llm() -> ChatGroq:
    """Initializes and returns the ChatGroq model using configured environment variables."""
    # Note: ChatGroq will automatically look for GROQ_API_KEY in environment
    model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    return ChatGroq(model_name=model, temperature=0.0)


def get_db():
    """Return a DB-like object. If `HINDSIGHT_URL` is configured, return an HTTP client wrapper.

    This preserves the `HindsightDB` interface (`query_incidents`, `save_session`, `get_all_incidents`)
    while enabling a live Hindsight service for integration testing.
    """
    hindsight_url = os.getenv("HINDSIGHT_URL")
    if hindsight_url and HindsightHTTPClient is not None:
        return HindsightHTTPClient(hindsight_url, api_key=os.getenv("HINDSIGHT_API_KEY"))
    # Fallback to local JSON-backed DB
    return HindsightDB()
