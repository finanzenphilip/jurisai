"""Live search mode: query RIS API directly, send results to Claude.

No pre-ingestion needed — works immediately for demos and testing.
"""
import sys
import logging
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.ris_client import RISClient
from ingestion.document_processor import extract_metadata, parse_html_decision
from generation.prompts import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE
from generation.claude_client import generate

logger = logging.getLogger(__name__)


@dataclass
class LiveSource:
    """A source from live RIS search."""
    geschaeftszahl: str
    gericht: str
    datum: str
    normen: list[str]
    text_preview: str
    source_url: str
    full_text: str


@dataclass
class LiveResponse:
    """Response from live search + Claude."""
    answer: str
    sources: list[LiveSource]
    query_used: str


def live_search_and_answer(
    question: str,
    applikation: str = "Justiz",
    norm: str = "",
    max_sources: int = 5,
) -> LiveResponse:
    """Search RIS live and answer using Claude.

    This mode requires no pre-ingested data. It:
    1. Searches RIS API with the question as search terms
    2. Fetches full text of top results
    3. Sends everything to Claude for analysis

    Args:
        question: Legal question in natural language
        applikation: Court type filter
        norm: Legal norm filter
        max_sources: Number of decisions to fetch (more = slower but better)

    Returns:
        LiveResponse with answer and sources
    """
    ris = RISClient(delay=0.5)

    # Use the question directly as search terms
    # Remove common question words for better RIS search
    search_terms = question
    for word in ["was", "wie", "welche", "gibt", "es", "der", "die", "das", "ist", "sind",
                  "bei", "zum", "zur", "für", "nach", "von", "in", "den", "dem", "des",
                  "sagt", "rechtsprechung", "präzedenzfälle", "entscheidungen"]:
        search_terms = search_terms.replace(f" {word} ", " ")

    search_terms = " ".join(search_terms.split())  # normalize whitespace
    logger.info(f"Live search: '{search_terms}' (app={applikation})")

    # Fetch decisions from RIS
    sources: list[LiveSource] = []
    decision_count = 0

    for doc_ref in ris.iter_decisions(
        applikation=applikation,
        suchworte=search_terms,
        norm=norm,
        max_pages=1,
    ):
        if decision_count >= max_sources:
            break

        meta = extract_metadata(doc_ref)
        gz = meta.get("geschaeftszahl", "")
        if not gz:
            continue

        # Fetch full text
        full_html = ris.fetch_full_text(doc_ref, fmt="Html")
        full_text = ""
        if full_html:
            sections = parse_html_decision(full_html)
            # Use reasoning section if available, otherwise full text
            full_text = sections.get("begruendung") or sections.get("full_text", "")

        # Truncate to ~2000 chars per source to fit in context
        text_for_context = full_text[:3000] if full_text else f"Entscheidung {gz}"

        sources.append(LiveSource(
            geschaeftszahl=gz,
            gericht=meta.get("gericht", ""),
            datum=meta.get("entscheidungsdatum", ""),
            normen=meta.get("normen", []),
            text_preview=full_text[:500] if full_text else "",
            source_url=meta.get("source_url", ""),
            full_text=text_for_context,
        ))

        decision_count += 1
        logger.info(f"  Fetched: {gz} ({meta.get('gericht', '')}, {meta.get('entscheidungsdatum', '')})")

    if not sources:
        return LiveResponse(
            answer="Zu dieser Frage wurden keine Entscheidungen in RIS gefunden. "
                   "Versuche eine andere Formulierung oder andere Suchbegriffe.\n\n"
                   "⚖️ Hinweis: Diese Zusammenfassung dient ausschließlich der juristischen "
                   "Recherche und stellt keine Rechtsberatung dar.",
            sources=[],
            query_used=search_terms,
        )

    # Format context for Claude
    context_parts = []
    for i, s in enumerate(sources, 1):
        header = f"[Quelle {i}] {s.gericht} {s.geschaeftszahl} ({s.datum})"
        if s.normen:
            header += f" | Normen: {', '.join(s.normen[:5])}"
        if s.source_url:
            header += f"\nLink: {s.source_url}"
        context_parts.append(f"{header}\n{s.full_text}")

    context = "\n\n---\n\n".join(context_parts)

    # Generate answer
    user_prompt = RAG_PROMPT_TEMPLATE.format(question=question, context=context)
    answer = generate(user_prompt=user_prompt, system_prompt=SYSTEM_PROMPT)

    return LiveResponse(
        answer=answer,
        sources=sources,
        query_used=search_terms,
    )
