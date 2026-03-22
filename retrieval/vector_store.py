"""ChromaDB vector store wrapper for legal document retrieval."""
import logging
from typing import Optional

import chromadb

from config import CHROMA_DIR, CHROMA_COLLECTION

logger = logging.getLogger(__name__)

_client = None
_collection = None


def get_collection():
    """Get the ChromaDB collection (singleton)."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"description": "Austrian court decisions from RIS"},
        )
    return _collection


def search(
    query_embedding: list[float],
    n_results: int = 10,
    gericht: Optional[str] = None,
    rechtsgebiet: Optional[str] = None,
    datum_von: Optional[str] = None,
    datum_bis: Optional[str] = None,
    applikation: Optional[str] = None,
    norm: Optional[str] = None,
) -> dict:
    """Search the vector store with optional metadata filters.

    Args:
        query_embedding: Query vector
        n_results: Number of results to return
        gericht: Filter by court name
        rechtsgebiet: Filter by legal area
        datum_von: Filter decisions after this date (YYYY-MM-DD)
        datum_bis: Filter decisions before this date (YYYY-MM-DD)
        applikation: Filter by RIS application
        norm: Filter by referenced norm (substring match)

    Returns:
        ChromaDB query result dict with ids, documents, metadatas, distances
    """
    collection = get_collection()

    # Build metadata filter
    where_clauses = []
    if gericht:
        where_clauses.append({"gericht": {"$eq": gericht}})
    if rechtsgebiet:
        where_clauses.append({"rechtsgebiet": {"$eq": rechtsgebiet}})
    if applikation:
        where_clauses.append({"applikation": {"$eq": applikation}})
    if datum_von:
        where_clauses.append({"entscheidungsdatum": {"$gte": datum_von}})
    if datum_bis:
        where_clauses.append({"entscheidungsdatum": {"$lte": datum_bis}})

    where = None
    if len(where_clauses) == 1:
        where = where_clauses[0]
    elif len(where_clauses) > 1:
        where = {"$and": where_clauses}

    # Also filter by norm in document text if specified
    where_document = None
    if norm:
        where_document = {"$contains": norm}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        where_document=where_document,
        include=["documents", "metadatas", "distances"],
    )

    return results


def get_stats() -> dict:
    """Get database statistics."""
    collection = get_collection()
    count = collection.count()

    # Sample some metadata to get unique courts/areas
    sample = collection.peek(limit=min(count, 100))

    courts = set()
    areas = set()
    apps = set()
    for meta in sample.get("metadatas", []):
        if meta.get("gericht"):
            courts.add(meta["gericht"])
        if meta.get("rechtsgebiet"):
            areas.add(meta["rechtsgebiet"])
        if meta.get("applikation"):
            apps.add(meta["applikation"])

    return {
        "total_chunks": count,
        "courts": sorted(courts),
        "rechtsgebiete": sorted(areas),
        "applikationen": sorted(apps),
    }
