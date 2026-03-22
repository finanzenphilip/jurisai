"""RAG chain: query → retrieve → generate → verify citations."""
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
    sources: list[RetrievalResult]
    cited_gz: set[str]
    available_gz: set[str]
    hallucinated_citations: set[str]
    is_verified: bool


def extract_geschaeftszahlen(text: str) -> set[str]:
    """Extract case numbers (Geschaeftszahlen) from text.

    Austrian case numbers follow patterns like:
    - 1Ob535/90
    - 5Ob234/20b
    - 9ObA123/15v
    - Ro 2019/13/0012
    """
    patterns = [
        r'\d+\s?Ob[A-Za-z]?\s?\d+/\d+[a-z]?',  # OGH: 1Ob535/90, 5Ob234/20b
        r'\d+\s?Os\s?\d+/\d+[a-z]?',  # Strafrecht: 15Os42/21d
        r'\d+\s?Ra\s?\d+/\d+',  # OGH Revision: 9Ra12/20
        r'Ro\s?\d{4}/\d+/\d+',  # VwGH: Ro 2019/13/0012
        r'Ra\s?\d{4}/\d+/\d+',  # VwGH Revision: Ra 2020/21/0345
        r'[A-Z]\s?\d+/\d+',  # VfGH: G123/2020, E4567/2021
        r'\d+\s?Bvwg?\s?\d+/\d+',  # BVwG patterns
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
    """Full RAG pipeline: answer a legal question using retrieved court decisions.

    Args:
        question: Natural language legal question
        n_results: Number of source chunks to retrieve
        gericht: Filter by court
        rechtsgebiet: Filter by legal area
        datum_von: Date from filter
        datum_bis: Date to filter
        applikation: RIS application filter
        norm: Legal norm filter

    Returns:
        RAGResponse with answer, sources, and citation verification
    """
    # Step 1: Retrieve relevant chunks
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

    # Step 2: Format context
    context = format_context(sources)

    # Step 3: Build prompt
    user_prompt = RAG_PROMPT_TEMPLATE.format(question=question, context=context)

    # Step 4: Generate answer
    logger.info("Generating answer with Claude...")
    answer = generate(user_prompt=user_prompt, system_prompt=SYSTEM_PROMPT)

    # Step 5: Verify citations
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
