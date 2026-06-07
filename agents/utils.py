import os
from langchain_groq import ChatGroq
from hindsight_db import HindsightDB

def get_llm() -> ChatGroq:
    """Initializes and returns the ChatGroq model using configured environment variables."""
    # Note: ChatGroq will automatically look for GROQ_API_KEY in environment
    model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    return ChatGroq(model_name=model, temperature=0.0)

def get_db() -> HindsightDB:
    """Returns an instance of HindsightDB."""
    return HindsightDB()
