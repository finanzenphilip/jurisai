"""Live search mode: query RIS API directly, send results to Claude.

No pre-ingestion needed — works immediately.
Handles simple questions like "Was passiert bei Diebstahl?" and complex
legal queries like "OGH Rechtsprechung zu § 83 StGB Körperverletzung".
"""
from __future__ import annotations

import re
import sys
import logging
from pathlib import Path
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.ris_client import RISClient
from ingestion.document_processor import extract_metadata, parse_html_decision
from generation.prompts import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE
from generation.claude_client import generate, generate_with_history

logger = logging.getLogger(__name__)

# German stopwords that hurt RIS search
STOPWORDS = {
    "was", "wie", "welche", "welcher", "welches", "welchem", "welchen",
    "gibt", "es", "der", "die", "das", "ist", "sind", "war", "waren",
    "bei", "zum", "zur", "für", "nach", "von", "in", "den", "dem", "des",
    "sagt", "kann", "könnte", "muss", "darf", "soll", "sollte", "würde",
    "und", "oder", "aber", "wenn", "weil", "dass", "ob", "als", "auch",
    "man", "ich", "du", "er", "sie", "wir", "mir", "mich", "dir", "uns",
    "ein", "eine", "einem", "einen", "einer", "eines", "kein", "keine",
    "hat", "haben", "hatte", "werden", "wurde", "worden", "wird",
    "nicht", "noch", "schon", "nur", "mehr", "sehr", "so", "zu", "am",
    "auf", "an", "mit", "aus", "über", "unter", "vor", "hinter",
    "zwischen", "durch", "gegen", "ohne", "um", "bis",
    "alle", "alles", "dieser", "diese", "diesem", "diesen", "dieses",
    "jeder", "jede", "jedem", "jeden", "jedes",
    "mein", "meine", "meinem", "meinen", "meiner", "meines",
    "sein", "seine", "seinem", "seinen", "seiner", "seines",
    "ihr", "ihre", "ihrem", "ihren", "ihrer", "ihres",
    "machen", "tun", "gehen", "kommen", "lassen", "sagen",
    "wissen", "wollen", "müssen", "dürfen", "können", "sollen",
    "bitte", "danke", "ja", "nein", "ok", "also", "denn", "mal",
    "passiert", "passieren", "geschieht", "geschehen",
    "rechtsprechung", "präzedenzfälle", "entscheidungen", "urteile",
    "frage", "fragen", "antwort", "antworten", "hilfe", "helfen",
    "welche", "möglichkeiten", "optionen", "chancen",
    "gibt", "geben", "davon", "dabei", "damit", "dafür", "dagegen",
    "hier", "dort", "jetzt", "dann", "wann", "wo", "warum", "wieso",
}


def extract_search_terms(question: str) -> str:
    """Extract meaningful legal search terms from a natural language question.

    Handles everything from "Was passiert bei Diebstahl?" to complex queries.
    """
    # Remove punctuation
    clean = re.sub(r'[?!.,;:()\[\]{}"\']', ' ', question)

    # Extract any § references first (important for legal search)
    paragraphs = re.findall(r'§\s*\d+[a-z]?', clean)

    # Extract legal code references
    codes = re.findall(r'\b(?:StGB|StPO|ABGB|ZPO|UGB|GmbHG|AktG|VStG|AVG|BVergG|MRG|WEG|ASVG|KSchG|GewO|DSG|DSGVO)\b', clean, re.IGNORECASE)

    # Split into words and filter stopwords
    words = clean.lower().split()
    meaningful = [w for w in words if w not in STOPWORDS and len(w) > 1 and not w.isdigit()]

    # Combine: legal references first, then meaningful words
    terms = []
    for code in codes:
        terms.append(code)
    for para in paragraphs:
        terms.append(para)
    for word in meaningful:
        if word.lower() not in [t.lower() for t in terms]:
            terms.append(word)

    search = " ".join(terms) if terms else question.strip()

    logger.info(f"Search terms: '{question}' -> '{search}'")
    return search


@dataclass
class LiveSource:
    """A source from live RIS Judikatur search."""
    geschaeftszahl: str
    gericht: str
    datum: str
    normen: list
    text_preview: str
    source_url: str
    full_text: str


@dataclass
class GesetzSource:
    """A source from live RIS Bundesrecht search."""
    kurztitel: str
    paragraph: str
    gesetzesnummer: str
    inkrafttretensdatum: str
    kundmachungsorgan: str
    source_url: str
    full_text: str


@dataclass
class LiveResponse:
    """Response from live search + Claude."""
    answer: str
    sources: list
    gesetz_sources: list = field(default_factory=list)
    query_used: str = ""


def _build_combined_context(
    judikatur_sources: list[LiveSource],
    gesetz_sources: list[GesetzSource],
) -> str:
    """Build a combined context string with labelled sections for Gesetze and Gerichtsentscheidungen."""
    parts = []

    # Gesetze (Bundesrecht) first — the law itself
    if gesetz_sources:
        gesetz_parts = []
        for i, g in enumerate(gesetz_sources, 1):
            header = f"[Gesetz {i}] {g.kurztitel} {g.paragraph}"
            if g.kundmachungsorgan:
                header += f" ({g.kundmachungsorgan})"
            if g.source_url:
                header += f"\nLink: {g.source_url}"
            gesetz_parts.append(f"{header}\n{g.full_text}")
        parts.append("GESETZE:\n\n" + "\n\n---\n\n".join(gesetz_parts))

    # Gerichtsentscheidungen (Judikatur) second
    if judikatur_sources:
        jud_parts = []
        for i, s in enumerate(judikatur_sources, 1):
            header = f"[Quelle {i}] {s.gericht} {s.geschaeftszahl} ({s.datum})"
            if s.normen:
                header += f" | Normen: {', '.join(s.normen[:5])}"
            if s.source_url:
                header += f"\nLink: {s.source_url}"
            jud_parts.append(f"{header}\n{s.full_text}")
        parts.append("GERICHTSENTSCHEIDUNGEN:\n\n" + "\n\n---\n\n".join(jud_parts))

    return "\n\n===\n\n".join(parts)


def live_search_and_answer(
    question: str,
    applikation: str = "Justiz",
    norm: str = "",
    max_sources: int = 5,
) -> LiveResponse:
    """Search RIS live (Judikatur + Bundesrecht) and answer using Claude.

    Works with simple questions ("Was ist Notwehr?") and complex ones.
    Searches both court decisions and federal law texts.
    """
    search_terms = extract_search_terms(question)

    logger.info(f"Live search: '{search_terms}' (app={applikation})")

    # 1) Search Judikatur (court decisions)
    sources, used_search = _search_ris_sources(
        question=question,
        applikation=applikation,
        norm=norm,
        max_sources=max_sources,
    )

    # 2) Search Bundesrecht (federal law texts)
    gesetz_sources = _search_bundesrecht_sources(
        search_terms=search_terms,
        max_sources=3,
    )

    has_any = bool(sources) or bool(gesetz_sources)

    if not has_any:
        # No results from either source — fall back to general knowledge
        answer = generate(
            user_prompt=f"""Der Benutzer fragt: "{question}"

Es wurden keine spezifischen Gesetze oder Gerichtsentscheidungen in der RIS-Datenbank gefunden.

Bitte erkläre die rechtliche Situation basierend auf dem österreichischen Recht so gut du kannst.
Weise klar darauf hin, dass keine konkreten Quellen aus der RIS-Datenbank zitiert werden können
und empfehle, einen Anwalt zu konsultieren für den konkreten Fall.

Erkläre die relevanten Gesetze und Paragraphen allgemein verständlich.""",
            system_prompt=SYSTEM_PROMPT,
        )
        return LiveResponse(answer=answer, sources=[], gesetz_sources=[], query_used=used_search)

    # Build combined context with both Gesetze and Gerichtsentscheidungen
    context = _build_combined_context(sources, gesetz_sources)

    user_prompt = RAG_PROMPT_TEMPLATE.format(question=question, context=context)
    answer = generate(user_prompt=user_prompt, system_prompt=SYSTEM_PROMPT)

    return LiveResponse(
        answer=answer,
        sources=sources,
        gesetz_sources=gesetz_sources,
        query_used=used_search,
    )


def _search_bundesrecht_sources(
    search_terms: str,
    max_sources: int = 3,
) -> list[GesetzSource]:
    """Search RIS Bundesrecht and return GesetzSource list.

    Tries the full search terms first, then falls back to fewer terms.
    """
    ris = RISClient(delay=0.3)
    sources: list[GesetzSource] = []

    attempts = [
        search_terms,
        " ".join(sorted(search_terms.split(), key=len, reverse=True)[:3]),
        sorted(search_terms.split(), key=len, reverse=True)[0] if search_terms.split() else "",
    ]

    for attempt in attempts:
        if not attempt.strip():
            continue
        try:
            result = ris.search_bundesrecht(suchworte=attempt, pro_seite="Twenty")
            ogd_result = result.get("OgdSearchResult", {})
            doc_refs = ogd_result.get("OgdDocumentResults", {}).get("OgdDocumentReference", [])

            if not doc_refs:
                continue

            if isinstance(doc_refs, dict):
                doc_refs = [doc_refs]

            count = 0
            for doc_ref in doc_refs:
                if count >= max_sources:
                    break

                meta = ris.extract_bundesrecht_meta(doc_ref)
                kurztitel = meta.get("kurztitel", "")
                paragraph = meta.get("paragraph", "")
                if not kurztitel:
                    continue

                # Fetch the actual law text
                gesetz_text = ris.fetch_gesetz_text(doc_ref)
                if not gesetz_text:
                    gesetz_text = f"{kurztitel} {paragraph}"

                text_for_context = gesetz_text[:2000]

                sources.append(GesetzSource(
                    kurztitel=kurztitel,
                    paragraph=paragraph,
                    gesetzesnummer=meta.get("gesetzesnummer", ""),
                    inkrafttretensdatum=meta.get("inkrafttretensdatum", ""),
                    kundmachungsorgan=meta.get("kundmachungsorgan", ""),
                    source_url=meta.get("source_url", ""),
                    full_text=text_for_context,
                ))
                count += 1
                logger.info(f"  Fetched Gesetz: {kurztitel} {paragraph}")

            if sources:
                break
        except Exception as e:
            logger.warning(f"Bundesrecht search '{attempt}' failed: {e}")
            continue

    return sources


def _search_ris_sources(
    question: str,
    applikation: str = "Justiz",
    norm: str = "",
    max_sources: int = 5,
) -> tuple[list[LiveSource], str]:
    """Search RIS and return sources + the query that worked.

    Extracted helper so both live_search_and_answer and live_search_with_history
    can share the same search logic.
    """
    ris = RISClient(delay=0.3)
    search_terms = extract_search_terms(question)
    logger.info(f"Live search: '{search_terms}' (app={applikation})")

    sources: list[LiveSource] = []
    attempts = [
        search_terms,
        " ".join(sorted(search_terms.split(), key=len, reverse=True)[:3]),
        sorted(search_terms.split(), key=len, reverse=True)[0] if search_terms.split() else "",
    ]

    used_search = search_terms
    for attempt in attempts:
        if not attempt.strip():
            continue
        try:
            count = 0
            for doc_ref in ris.iter_decisions(
                applikation=applikation,
                suchworte=attempt,
                norm=norm,
                max_pages=1,
            ):
                if count >= max_sources:
                    break

                meta = extract_metadata(doc_ref)
                gz = meta.get("geschaeftszahl", "")
                if not gz:
                    continue

                full_html = ris.fetch_full_text(doc_ref, fmt="Html")
                full_text = ""
                if full_html:
                    sections = parse_html_decision(full_html)
                    full_text = sections.get("begruendung") or sections.get("full_text", "")

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
                count += 1
                logger.info(f"  Fetched: {gz}")

            if sources:
                used_search = attempt
                break
        except Exception as e:
            logger.warning(f"Search attempt '{attempt}' failed: {e}")
            continue

    return sources, used_search


def _build_ris_context(sources: list[LiveSource]) -> str:
    """Format RIS sources into a context string for the prompt."""
    context_parts = []
    for i, s in enumerate(sources, 1):
        header = f"[Quelle {i}] {s.gericht} {s.geschaeftszahl} ({s.datum})"
        if s.normen:
            header += f" | Normen: {', '.join(s.normen[:5])}"
        if s.source_url:
            header += f"\nLink: {s.source_url}"
        context_parts.append(f"{header}\n{s.full_text}")
    return "\n\n---\n\n".join(context_parts)


def live_search_with_history(
    question: str,
    history: list,  # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    applikation: str = "Justiz",
    norm: str = "",
    max_sources: int = 5,
) -> LiveResponse:
    """Search RIS live (Judikatur + Bundesrecht) and answer with conversation history.

    Like live_search_and_answer but sends previous conversation turns so Claude
    can understand follow-up questions like "und was wenn er vorbestraft ist?".
    """
    search_terms = extract_search_terms(question)

    # 1) Search Judikatur
    sources, used_search = _search_ris_sources(
        question=question,
        applikation=applikation,
        norm=norm,
        max_sources=max_sources,
    )

    # 2) Search Bundesrecht
    gesetz_sources = _search_bundesrecht_sources(
        search_terms=search_terms,
        max_sources=3,
    )

    has_any = bool(sources) or bool(gesetz_sources)

    # Build the new user message with RIS context
    if not has_any:
        new_user_content = (
            f'Der Benutzer fragt: "{question}"\n\n'
            "Es wurden keine spezifischen Gesetze oder Gerichtsentscheidungen in der RIS-Datenbank gefunden.\n\n"
            "Bitte erkläre die rechtliche Situation basierend auf dem österreichischen Recht so gut du kannst.\n"
            "Weise klar darauf hin, dass keine konkreten Quellen aus der RIS-Datenbank zitiert werden können\n"
            "und empfehle, einen Anwalt zu konsultieren für den konkreten Fall.\n\n"
            "Erkläre die relevanten Gesetze und Paragraphen allgemein verständlich."
        )
    else:
        context = _build_combined_context(sources, gesetz_sources)
        new_user_content = RAG_PROMPT_TEMPLATE.format(question=question, context=context)

    # Build full messages list: previous history + new user message
    messages = list(history) + [{"role": "user", "content": new_user_content}]

    answer = generate_with_history(messages=messages, system_prompt=SYSTEM_PROMPT)

    return LiveResponse(
        answer=answer,
        sources=sources,
        gesetz_sources=gesetz_sources,
        query_used=used_search,
    )
