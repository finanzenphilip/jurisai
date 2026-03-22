"""Configuration constants for the RIS Legal AI tool."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit Cloud secrets or environment."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


# Paths
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
CHROMA_DIR = DATA_DIR / "chroma_db"

# RIS API
RIS_API_BASE = "https://data.bka.gv.at/ris/api/v2.6"
RIS_DOC_BASE = "https://www.ris.bka.gv.at"
RIS_REQUEST_DELAY = 1.0  # seconds between API requests

# Court applications for Judikatur endpoint
COURT_APPS = {
    "Justiz": "OGH, OLG, LG, BG (ordentliche Gerichte)",
    "Vwgh": "Verwaltungsgerichtshof",
    "Vfgh": "Verfassungsgerichtshof",
    "Bvwg": "Bundesverwaltungsgericht",
    "Lvwg": "Landesverwaltungsgerichte",
}

# Embedding — use lighter model for cloud deployment
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Chunking
CHUNK_SIZE_TOKENS = 600  # target tokens per chunk
CHUNK_OVERLAP_TOKENS = 100
MAX_CHUNK_CHARS = 3000  # approximate char limit

# ChromaDB
CHROMA_COLLECTION = "ris_judikatur"

# Claude
ANTHROPIC_API_KEY = _get_secret("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_TEMPERATURE = 0
MAX_CONTEXT_CHUNKS = 8

# Streamlit
STREAMLIT_PAGE_TITLE = "RIS Legal AI - Österreichische Rechtsprechung"
