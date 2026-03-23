"""Embedding wrapper for German legal text using sentence-transformers."""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_model = None


def get_model(model_name: str = None):
    """Lazy-load the embedding model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        from config import EMBEDDING_MODEL
        name = model_name or EMBEDDING_MODEL
        logger.info(f"Loading embedding model: {name}")
        _model = SentenceTransformer(name)
        logger.info("Embedding model loaded")
    return _model


def embed_texts(texts: list[str], model_name: str = None, batch_size: int = 32) -> list[list[float]]:
    """Embed a list of texts and return embeddings as lists of floats."""
    if not texts:
        return []

    model = get_model(model_name)
    logger.info(f"Embedding {len(texts)} texts...")

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 100,
        normalize_embeddings=True,
    )

    return [emb.tolist() for emb in embeddings]


def embed_query(query: str, model_name: str = None) -> list[float]:
    """Embed a single query string."""
    model = get_model(model_name)
    embedding = model.encode(query, normalize_embeddings=True)
    return embedding.tolist()
