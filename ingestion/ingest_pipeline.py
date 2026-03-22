"""Ingestion pipeline: fetch decisions from RIS → process → embed → store in ChromaDB."""
import logging
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CHROMA_COLLECTION, CHROMA_DIR
from ingestion.ris_client import RISClient
from ingestion.document_processor import process_decision, DocumentChunk
from ingestion.embedder import embed_texts

import chromadb

logger = logging.getLogger(__name__)


def get_chroma_collection():
    """Get or create the ChromaDB collection."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        metadata={"description": "Austrian court decisions from RIS"}
    )
    return collection


def ingest_decisions(
    applikation: str = "Justiz",
    suchworte: str = "",
    norm: str = "",
    datum_von: str = "",
    datum_bis: str = "",
    max_decisions: int = 100,
    fetch_full_text: bool = True,
    batch_size: int = 50,
):
    """Main ingestion pipeline.

    Args:
        applikation: Court type (Justiz, Vwgh, Vfgh, etc.)
        suchworte: Search terms for filtering
        norm: Legal norm filter
        datum_von: Start date
        datum_bis: End date
        max_decisions: Maximum number of decisions to ingest (0 = unlimited)
        fetch_full_text: Whether to fetch full HTML text (slower but better)
        batch_size: Number of chunks to embed and store at once
    """
    ris = RISClient()
    collection = get_chroma_collection()

    # Calculate max pages needed
    max_pages = (max_decisions // 100) + 1 if max_decisions > 0 else 0

    all_chunks: list[DocumentChunk] = []
    decision_count = 0
    skipped = 0

    logger.info(f"Starting ingestion: {applikation}, search='{suchworte}', max={max_decisions}")

    for doc_ref in ris.iter_decisions(
        applikation=applikation,
        suchworte=suchworte,
        norm=norm,
        datum_von=datum_von,
        datum_bis=datum_bis,
        max_pages=max_pages,
    ):
        if max_decisions > 0 and decision_count >= max_decisions:
            break

        decision_count += 1
        gz = doc_ref.get("Data", {}).get("Metadaten", {}).get("Judikatur", {}).get(
            "Geschaeftszahl", f"unknown_{decision_count}"
        )

        # Check if already ingested
        existing = collection.get(where={"geschaeftszahl": str(gz)})
        if existing and existing.get("ids"):
            skipped += 1
            if skipped % 50 == 0:
                logger.info(f"Skipped {skipped} already-ingested decisions")
            continue

        # Fetch full text if requested
        full_html = None
        if fetch_full_text:
            full_html = ris.fetch_full_text(doc_ref, fmt="Html")

        # Process into chunks
        chunks = process_decision(doc_ref, full_html, applikation)

        if chunks:
            all_chunks.extend(chunks)
            if decision_count % 10 == 0:
                logger.info(f"Processed {decision_count} decisions, {len(all_chunks)} chunks total")

        # Batch store when we have enough chunks
        if len(all_chunks) >= batch_size:
            _store_batch(collection, all_chunks)
            all_chunks = []

    # Store remaining chunks
    if all_chunks:
        _store_batch(collection, all_chunks)

    total_in_db = collection.count()
    logger.info(
        f"Ingestion complete: {decision_count} decisions processed, "
        f"{skipped} skipped (already in DB), {total_in_db} total chunks in database"
    )
    return {"decisions": decision_count, "skipped": skipped, "total_chunks": total_in_db}


def _store_batch(collection, chunks: list[DocumentChunk]):
    """Embed and store a batch of chunks in ChromaDB."""
    texts = [c.text for c in chunks]
    ids = [c.chunk_id for c in chunks]
    metadatas = [c.to_metadata() for c in chunks]

    # Deduplicate IDs (in case of processing errors)
    seen_ids = set()
    unique_texts, unique_ids, unique_meta = [], [], []
    for t, i, m in zip(texts, ids, metadatas):
        if i not in seen_ids:
            seen_ids.add(i)
            unique_texts.append(t)
            unique_ids.append(i)
            unique_meta.append(m)

    logger.info(f"Embedding {len(unique_texts)} chunks...")
    embeddings = embed_texts(unique_texts)

    logger.info(f"Storing {len(unique_texts)} chunks in ChromaDB...")
    collection.upsert(
        ids=unique_ids,
        documents=unique_texts,
        embeddings=embeddings,
        metadatas=unique_meta,
    )
    logger.info(f"Batch stored. DB now has {collection.count()} chunks.")


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Ingest RIS court decisions into vector database")
    parser.add_argument("--app", default="Justiz", help="Court type: Justiz, Vwgh, Vfgh, Bvwg, Lvwg")
    parser.add_argument("--search", default="", help="Full-text search filter")
    parser.add_argument("--norm", default="", help="Legal norm filter (e.g. 'StGB §127')")
    parser.add_argument("--from", dest="datum_von", default="", help="Start date YYYY-MM-DD")
    parser.add_argument("--to", dest="datum_bis", default="", help="End date YYYY-MM-DD")
    parser.add_argument("--max", type=int, default=100, help="Max decisions to ingest (0=unlimited)")
    parser.add_argument("--no-fulltext", action="store_true", help="Skip fetching full text (faster)")
    args = parser.parse_args()

    result = ingest_decisions(
        applikation=args.app,
        suchworte=args.search,
        norm=args.norm,
        datum_von=args.datum_von,
        datum_bis=args.datum_bis,
        max_decisions=args.max,
        fetch_full_text=not args.no_fulltext,
    )
    print(f"\nDone! {result}")
