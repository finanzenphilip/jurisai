"""RAG chain: query -> retrieve -> generate -> verify citations."""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from typing import Optional

from retrieval.retriever import retrieve, format_context, RetrievalResult
from generation.prompts import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE
from generation.claude_client import generate

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Complete RAG response with answer, sources, and verification."""
    answer: str
    sources: list
    cited_gz: set
    available_gz: set
    hallucinated_citations: set
    is_verified: bool


def extract_geschaeftszahlen(text: str) -> set:
    """Extract case numbers (Geschaeftszahlen) from text."""
    patterns = [
        r'\d+\s?Ob[A-Za-z]?\s?\d+/\d+[a-z]?',
        r'\d+\s?Os\s?\d+/\d+[a-z]?',
        r'\d+\s?Ra\s?\d+/\d+',
        r'Ro\s?\d{4}/\d+/\d+',
        r'Ra\s?\d{4}/\d+/\d+',
        r'[A-Z]\s?\d+/\d+',
        r'\d+\s?Bvwg?\s?\d+/\d+',
    ]

    found = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        found.update(m.strip() for m in matches)

    return found


def answer_legal_question(
    question: str,
    n_results: int = 8,
    gericht: Optional[str] = None,
    rechtsgebiet: Optional[str] = None,
    datum_von: Optional[str] = None,
    datum_bis: Optional[str] = None,
    applikation: Optional[str] = None,
    norm: Optional[str] = None,
) -> RAGResponse:
    """Full RAG pipeline: answer a legal question using retrieved court decisions."""
    logger.info(f"Retrieving sources for: {question}")
    sources = retrieve(
        query=question,
        n_results=n_results,
        gericht=gericht,
        rechtsgebiet=rechtsgebiet,
        datum_von=datum_von,
        datum_bis=datum_bis,
        applikation=applikation,
        norm=norm,
    )

    if not sources:
        return RAGResponse(
            answer="Zu dieser Frage wurden keine relevanten Entscheidungen in der Datenbank gefunden. "
                   "Bitte versuchen Sie eine andere Formulierung oder erweitern Sie die Suchkriterien.\n\n"
                   "⚖️ Hinweis: Diese Zusammenfassung dient ausschließlich der juristischen Recherche "
                   "und stellt keine Rechtsberatung dar.",
            sources=[],
            cited_gz=set(),
            available_gz=set(),
            hallucinated_citations=set(),
            is_verified=True,
        )

    context = format_context(sources)
    user_prompt = RAG_PROMPT_TEMPLATE.format(question=question, context=context)

    logger.info("Generating answer with Claude...")
    answer = generate(user_prompt=user_prompt, system_prompt=SYSTEM_PROMPT)

    cited_gz = extract_geschaeftszahlen(answer)
    available_gz = {s.geschaeftszahl for s in sources}
    hallucinated = cited_gz - available_gz if cited_gz else set()

    if hallucinated:
        logger.warning(f"Potentially hallucinated citations: {hallucinated}")

    return RAGResponse(
        answer=answer,
        sources=sources,
        cited_gz=cited_gz,
        available_gz=available_gz,
        hallucinated_citations=hallucinated,
        is_verified=len(hallucinated) == 0,
    )
