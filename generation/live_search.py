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
from datetime import datetime, timedelta
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.ris_client import RISClient
from ingestion.document_processor import extract_metadata, parse_html_decision
from generation.prompts import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE, QUERY_REWRITE_PROMPT, FOLLOWUP_PROMPT
from generation.claude_client import generate, generate_fast, generate_with_history, stream_with_history

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


def rewrite_query_with_ai(question: str) -> str:
    """Use Claude (Sonnet) to rewrite a user question into optimal legal search terms.

    Falls back to rule-based extraction if AI rewriting fails.
    """
    try:
        rewritten = generate_fast(
            user_prompt=QUERY_REWRITE_PROMPT.format(question=question),
            system_prompt="Du bist ein juristischer Suchexperte für österreichisches Recht. Antworte NUR mit der optimierten Suchanfrage.",
            max_tokens=80,
        )
        rewritten = rewritten.strip().strip('"').strip("'")
        if rewritten and len(rewritten) > 2:
            logger.info(f"AI query rewrite: '{question}' -> '{rewritten}'")
            return rewritten
    except Exception as e:
        logger.warning(f"AI query rewrite failed: {e}")

    return extract_search_terms(question)


def extract_search_terms(question: str) -> str:
    """Extract meaningful legal search terms from a natural language question (rule-based fallback)."""
    clean = re.sub(r'[?!.,;:()\[\]{}"\']', ' ', question)

    paragraphs = re.findall(r'§\s*\d+[a-z]?', clean)
    codes = re.findall(r'\b(?:StGB|StPO|ABGB|ZPO|UGB|GmbHG|AktG|VStG|AVG|BVergG|MRG|WEG|ASVG|KSchG|GewO|DSG|DSGVO|EStG|BAO|FinStrG|IO|AußStrG|SMG|VbVG|VerG|UStG|KStG|BWG|WAG|WpHG|BörseG|FMABG|InvFG|AIFMG|GSpG|TKG|MedienG|StVO|FSG|KFG|EheG|EPG|KindNamRÄG|ABGB|PHG|FernFinG|FAGG|VKrG|HIKrG|AltFG|ArbVG|AngG|AZG|UrlG|MuttSchG|KBGG|BMSVG|GlBG|BEinstG|AuslBG)\b', clean, re.IGNORECASE)

    words = clean.lower().split()
    meaningful = [w for w in words if w not in STOPWORDS and len(w) > 1 and not w.isdigit()]

    terms = []
    for code in codes:
        terms.append(code)
    for para in paragraphs:
        terms.append(para)
    for word in meaningful:
        if word.lower() not in [t.lower() for t in terms]:
            terms.append(word)

    search = " ".join(terms) if terms else question.strip()
    logger.info(f"Rule-based search terms: '{question}' -> '{search}'")
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

                text_for_context = gesetz_text[:4000]

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


def _fetch_sources_for_query(
    ris: RISClient,
    search_term: str,
    applikation: str,
    norm: str,
    max_sources: int,
    datum_von: str = "",
    datum_bis: str = "",
    seen_gz: set = None,
) -> list[LiveSource]:
    """Fetch LiveSource objects for a single search query + date range."""
    if seen_gz is None:
        seen_gz = set()

    results: list[LiveSource] = []
    try:
        for doc_ref in ris.iter_decisions(
            applikation=applikation,
            suchworte=search_term,
            norm=norm,
            datum_von=datum_von,
            datum_bis=datum_bis,
            max_pages=2,
        ):
            if len(results) >= max_sources:
                break

            meta = extract_metadata(doc_ref)
            gz = meta.get("geschaeftszahl", "")
            if not gz or gz in seen_gz:
                continue
            seen_gz.add(gz)

            full_html = ris.fetch_full_text(doc_ref, fmt="Html")
            full_text = ""
            if full_html:
                sections = parse_html_decision(full_html)
                full_text = sections.get("begruendung") or sections.get("full_text", "")

            text_for_context = full_text[:5000] if full_text else f"Entscheidung {gz}"

            results.append(LiveSource(
                geschaeftszahl=gz,
                gericht=meta.get("gericht", ""),
                datum=meta.get("entscheidungsdatum", ""),
                normen=meta.get("normen", []),
                text_preview=full_text[:500] if full_text else "",
                source_url=meta.get("source_url", ""),
                full_text=text_for_context,
            ))
            logger.info(f"  Fetched: {gz} ({meta.get('entscheidungsdatum', '?')})")
    except Exception as e:
        logger.warning(f"Search '{search_term}' [{datum_von}..{datum_bis}] failed: {e}")

    return results


def _sort_sources_by_date(sources: list[LiveSource]) -> list[LiveSource]:
    """Sort sources by date DESC (newest first). Empty dates go last."""
    def date_key(s: LiveSource):
        try:
            return datetime.strptime(s.datum, "%Y-%m-%d")
        except (ValueError, TypeError):
            return datetime(1900, 1, 1)
    return sorted(sources, key=date_key, reverse=True)


def _search_ris_sources(
    question: str,
    applikation: str = "Justiz",
    norm: str = "",
    max_sources: int = 5,
    ai_search_terms: str = "",
    prefer_recent: bool = True,
) -> tuple[list[LiveSource], str]:
    """Search RIS with multi-wave recency strategy.

    Wave 1: Last 2 years (most current jurisprudence)
    Wave 2: Last 5 years (if wave 1 insufficient)
    Wave 3: All time (fallback, if still insufficient)

    Within each wave, results are sorted newest-first.
    """
    ris = RISClient(delay=0.3)
    search_terms = ai_search_terms or extract_search_terms(question)
    logger.info(f"Live search: '{search_terms}' (app={applikation}, prefer_recent={prefer_recent})")

    fallback_terms = [
        search_terms,
        " ".join(sorted(search_terms.split(), key=len, reverse=True)[:3]),
        sorted(search_terms.split(), key=len, reverse=True)[0] if search_terms.split() else "",
    ]

    sources: list[LiveSource] = []
    used_search = search_terms
    seen_gz: set[str] = set()

    if prefer_recent:
        today = datetime.now()
        waves = [
            (today - timedelta(days=365 * 2)).strftime("%Y-%m-%d"),  # last 2 years
            (today - timedelta(days=365 * 5)).strftime("%Y-%m-%d"),  # last 5 years
            "",  # all time
        ]
    else:
        waves = [""]

    for wave_idx, datum_von in enumerate(waves):
        if len(sources) >= max_sources:
            break

        wave_label = {0: "letzte 2J", 1: "letzte 5J", 2: "alle"}.get(wave_idx, f"wave {wave_idx}")
        logger.info(f"Wave {wave_idx+1} ({wave_label}): searching...")

        for term in fallback_terms:
            if not term.strip() or len(sources) >= max_sources:
                continue

            wave_sources = _fetch_sources_for_query(
                ris=ris,
                search_term=term,
                applikation=applikation,
                norm=norm,
                max_sources=max_sources - len(sources),
                datum_von=datum_von,
                seen_gz=seen_gz,
            )

            if wave_sources:
                sources.extend(wave_sources)
                used_search = term
                logger.info(f"  Wave {wave_idx+1} got {len(wave_sources)} results with '{term}'")
                break  # try next wave only if still under max_sources

    # Final sort: newest first
    sources = _sort_sources_by_date(sources)

    return sources[:max_sources], used_search


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
    history: list,
    applikation: str = "Justiz",
    norm: str = "",
    max_sources: int = 5,
    progress_callback=None,
    prefer_recent: bool = True,
) -> LiveResponse:
    """Search RIS live (Judikatur + Bundesrecht) and answer with conversation history."""
    if progress_callback:
        progress_callback("Analysiere Rechtsfrage...")
    ai_terms = rewrite_query_with_ai(question)

    if progress_callback:
        progress_callback("Durchsuche aktuelle Rechtsprechung..." if prefer_recent else "Durchsuche Rechtsprechung...")
    sources, used_search = _search_ris_sources(
        question=question,
        applikation=applikation,
        norm=norm,
        max_sources=max_sources,
        ai_search_terms=ai_terms,
        prefer_recent=prefer_recent,
    )

    # Step 3: Search Bundesrecht
    if progress_callback:
        progress_callback("Durchsuche Bundesgesetze...")
    gesetz_sources = _search_bundesrecht_sources(
        search_terms=ai_terms,
        max_sources=3,
    )

    has_any = bool(sources) or bool(gesetz_sources)

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

    messages = list(history) + [{"role": "user", "content": new_user_content}]

    if progress_callback:
        progress_callback("Erstelle rechtliche Analyse...")

    answer = generate_with_history(messages=messages, system_prompt=SYSTEM_PROMPT)

    return LiveResponse(
        answer=answer,
        sources=sources,
        gesetz_sources=gesetz_sources,
        query_used=used_search,
    )


def stream_search_with_history(
    question: str,
    history: list,
    applikation: str = "Justiz",
    norm: str = "",
    max_sources: int = 5,
    progress_callback=None,
    prefer_recent: bool = True,
):
    """Like live_search_with_history but streams the answer.

    Returns (sources, gesetz_sources, query_used, stream_iterator).
    The caller iterates stream_iterator to get text chunks.
    """
    if progress_callback:
        progress_callback("Analysiere Rechtsfrage...")
    ai_terms = rewrite_query_with_ai(question)

    if progress_callback:
        progress_callback("Durchsuche aktuelle Rechtsprechung..." if prefer_recent else "Durchsuche Rechtsprechung...")
    sources, used_search = _search_ris_sources(
        question=question,
        applikation=applikation,
        norm=norm,
        max_sources=max_sources,
        ai_search_terms=ai_terms,
        prefer_recent=prefer_recent,
    )

    if progress_callback:
        progress_callback("Durchsuche Bundesgesetze...")
    gesetz_sources = _search_bundesrecht_sources(
        search_terms=ai_terms,
        max_sources=3,
    )

    has_any = bool(sources) or bool(gesetz_sources)

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

    messages = list(history) + [{"role": "user", "content": new_user_content}]

    if progress_callback:
        progress_callback("Erstelle rechtliche Analyse...")

    stream = stream_with_history(messages=messages, system_prompt=SYSTEM_PROMPT)

    return sources, gesetz_sources, used_search, stream


def generate_followup_questions(question: str, answer: str) -> list[str]:
    """Generate 3 follow-up question suggestions based on the answer."""
    try:
        result = generate_fast(
            user_prompt=FOLLOWUP_PROMPT.format(question=question, answer=answer[:2000]),
            system_prompt="Du bist ein juristischer Assistent. Antworte NUR mit 3 Folgefragen, eine pro Zeile.",
            max_tokens=200,
        )
        questions = [q.strip().lstrip("0123456789.-) ") for q in result.strip().split("\n") if q.strip()]
        return questions[:3]
    except Exception as e:
        logger.warning(f"Follow-up generation failed: {e}")
        return []
