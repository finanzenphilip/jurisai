"""High-level retrieval: embed query, search vector store, rerank results."""
import logging
from dataclasses import dataclass
from typing import Optional

from ingestion.embedder import embed_query
from retrieval.vector_store import search

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """A single retrieval result with text, metadata, and score."""
    text: str
    metadata: dict
    distance: float  # lower = more similar

    @property
    def geschaeftszahl(self) -> str:
        return self.metadata.get("geschaeftszahl", "")

    @property
    def gericht(self) -> str:
        return self.metadata.get("gericht", "")

    @property
    def datum(self) -> str:
        return self.metadata.get("entscheidungsdatum", "")

    @property
    def source_url(self) -> str:
        return self.metadata.get("source_url", "")

    def citation(self) -> str:
        """Format as a legal citation."""
        parts = [self.gericht, self.geschaeftszahl]
        if self.datum:
            parts.append(self.datum)
        return " ".join(filter(None, parts))


def retrieve(
    query: str,
    n_results: int = 8,
    gericht: Optional[str] = None,
    rechtsgebiet: Optional[str] = None,
    datum_von: Optional[str] = None,
    datum_bis: Optional[str] = None,
    applikation: Optional[str] = None,
    norm: Optional[str] = None,
    boost_rechtssaetze: bool = True,
) -> list[RetrievalResult]:
    """Retrieve relevant court decision chunks for a query.

    Args:
        query: Natural language legal question
        n_results: Number of results to return
        gericht: Filter by court
        rechtsgebiet: Filter by legal area
        datum_von: Date from filter
        datum_bis: Date to filter
        applikation: RIS application filter
        norm: Legal norm filter
        boost_rechtssaetze: Boost Rechtssatz and summary sections

    Returns:
        List of RetrievalResult sorted by relevance
    """
    # Embed query
    query_embedding = embed_query(query)

    # Over-retrieve for reranking
    fetch_n = n_results * 2

    raw = search(
        query_embedding=query_embedding,
        n_results=fetch_n,
        gericht=gericht,
        rechtsgebiet=rechtsgebiet,
        datum_von=datum_von,
        datum_bis=datum_bis,
        applikation=applikation,
        norm=norm,
    )

    # Parse results
    results = []
    ids = raw.get("ids", [[]])[0]
    docs = raw.get("documents", [[]])[0]
    metas = raw.get("metadatas", [[]])[0]
    dists = raw.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, dists):
        results.append(RetrievalResult(text=doc, metadata=meta, distance=dist))

    # Rerank: boost Rechtssatz and summary sections
    if boost_rechtssaetze:
        for r in results:
            section = r.metadata.get("section", "")
            if section in ("rechtssatz", "summary"):
                r.distance *= 0.8  # boost by reducing distance

    # Sort by distance (ascending = most similar first)
    results.sort(key=lambda r: r.distance)

    # Deduplicate by Geschaeftszahl — keep best chunk per decision
    seen_gz = set()
    deduplicated = []
    for r in results:
        gz = r.geschaeftszahl
        if gz not in seen_gz:
            seen_gz.add(gz)
            deduplicated.append(r)

    return deduplicated[:n_results]


def format_context(results: list[RetrievalResult]) -> str:
    """Format retrieval results as context for the LLM prompt."""
    if not results:
        return "Keine relevanten Entscheidungen gefunden."

    parts = []
    for i, r in enumerate(results, 1):
        header = f"[Quelle {i}] {r.citation()}"
        normen = r.metadata.get("normen", "")
        if normen:
            header += f" | Normen: {normen}"
        url = r.source_url
        if url:
            header += f"\nLink: {url}"

        parts.append(f"{header}\n{r.text}")

    return "\n\n---\n\n".join(parts)
