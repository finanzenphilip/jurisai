"""Analyze uploaded legal documents and suggest defense strategies."""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field

from generation.claude_client import generate
from generation.prompts import SYSTEM_PROMPT
from generation.live_search import LiveSource, extract_search_terms
from ingestion.ris_client import RISClient
from ingestion.document_processor import extract_metadata, parse_html_decision

logger = logging.getLogger(__name__)


DOCUMENT_EXTRACTION_PROMPT = """Du bist ein juristischer Experte für österreichisches Recht.
Analysiere das folgende Dokument und extrahiere die wichtigsten juristischen Suchbegriffe.

DOKUMENT:
{document_text}

AUFGABE:
Extrahiere die 3-5 wichtigsten juristischen Suchbegriffe für eine Recherche in der
RIS-Rechtsprechungsdatenbank. Fokus auf:
- Delikte / Straftatbestände (z.B. "Diebstahl", "Körperverletzung")
- Relevante Paragraphen (z.B. "§ 127 StGB", "§ 83 StGB")
- Juristische Schlüsselbegriffe

Antworte NUR mit den Suchbegriffen, getrennt durch Komma. Nichts anderes."""

DOCUMENT_ANALYSIS_PROMPT = """Du erhältst ein juristisches Dokument (z.B. eine Anklageschrift, einen Strafantrag, oder eine Anzeige).

DOKUMENT:
{document_text}

RELEVANTE GERICHTSENTSCHEIDUNGEN:
{context}

AUFGABEN:
1. Identifiziere alle Vorwürfe/Delikte mit den relevanten Paragraphen
2. Analysiere die Beweislage basierend auf dem Dokument
3. Zeige ALLE möglichen Verteidigungsstrategien auf
4. Nenne relevante Rechtsprechung aus den Quellen
5. Bewerte die Erfolgsaussichten der einzelnen Strategien
6. Empfehle nächste Schritte

Format die Antwort klar und strukturiert."""

DOCUMENT_ANALYSIS_NO_SOURCES_PROMPT = """Du erhältst ein juristisches Dokument (z.B. eine Anklageschrift, einen Strafantrag, oder eine Anzeige).

DOKUMENT:
{document_text}

Es wurden keine spezifischen Gerichtsentscheidungen in der RIS-Datenbank gefunden.

AUFGABEN:
1. Identifiziere alle Vorwürfe/Delikte mit den relevanten Paragraphen
2. Analysiere die Beweislage basierend auf dem Dokument
3. Zeige ALLE möglichen Verteidigungsstrategien auf basierend auf deinem Wissen über österreichisches Recht
4. Bewerte die Erfolgsaussichten der einzelnen Strategien
5. Empfehle nächste Schritte

Weise darauf hin, dass keine konkreten Gerichtsentscheidungen zitiert werden konnten,
und empfehle, einen Anwalt zu konsultieren.

Format die Antwort klar und strukturiert."""


@dataclass
class DocumentAnalysisResponse:
    """Response from document analysis."""
    answer: str
    sources: list = field(default_factory=list)
    extracted_charges: str = ""
    query_used: str = ""


def extract_text_from_upload(uploaded_file) -> str:
    """Extract text from uploaded PDF or text file.

    Args:
        uploaded_file: Streamlit UploadedFile object.

    Returns:
        Extracted text content.

    Raises:
        ValueError: If file type is unsupported or text extraction fails.
    """
    filename = uploaded_file.name.lower()

    if filename.endswith(".txt"):
        raw = uploaded_file.read()
        # Try common encodings
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                return raw.decode(encoding)
            except (UnicodeDecodeError, AttributeError):
                continue
        # Last resort
        return raw.decode("utf-8", errors="replace")

    if filename.endswith(".pdf"):
        return _extract_pdf_text(uploaded_file)

    raise ValueError(f"Nicht unterstütztes Dateiformat: {filename}. Bitte PDF oder TXT hochladen.")


def _extract_pdf_text(uploaded_file) -> str:
    """Extract text from a PDF file, trying multiple libraries."""
    pdf_bytes = uploaded_file.read()

    # Try PyPDF2 first
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        if pages:
            result = "\n\n".join(pages)
            if result.strip():
                return result
    except ImportError:
        logger.warning("PyPDF2 not installed, trying fallback")
    except Exception as e:
        logger.warning(f"PyPDF2 failed: {e}")

    # Try pdfplumber as fallback
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            if pages:
                result = "\n\n".join(pages)
                if result.strip():
                    return result
    except ImportError:
        logger.warning("pdfplumber not installed either")
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")

    raise ValueError(
        "PDF konnte nicht gelesen werden. Bitte installiere PyPDF2 "
        "(pip install PyPDF2) oder lade eine TXT-Datei hoch."
    )


def _search_ris_for_document(
    search_terms: str,
    applikation: str = "Justiz",
    max_sources: int = 5,
) -> list[LiveSource]:
    """Search RIS using extracted terms from a document."""
    ris = RISClient(delay=0.3)
    sources: list[LiveSource] = []

    # Try the full search terms, then progressively fewer
    terms_list = search_terms.split(",")
    attempts = []
    for term in terms_list:
        cleaned = term.strip()
        if cleaned:
            attempts.append(extract_search_terms(cleaned))

    # Also try all combined
    all_terms = " ".join(t.strip() for t in terms_list if t.strip())
    attempts.insert(0, extract_search_terms(all_terms))

    seen_gz: set[str] = set()

    for attempt in attempts:
        if not attempt.strip():
            continue
        if len(sources) >= max_sources:
            break

        try:
            count = 0
            for doc_ref in ris.iter_decisions(
                applikation=applikation,
                suchworte=attempt,
                max_pages=1,
            ):
                if len(sources) >= max_sources:
                    break
                if count >= 3:  # Max per attempt to get diversity
                    break

                meta = extract_metadata(doc_ref)
                gz = meta.get("geschaeftszahl", "")
                if not gz or gz in seen_gz:
                    continue
                seen_gz.add(gz)

                # Fetch full text
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
                logger.info(f"  Document analysis source: {gz}")

        except Exception as e:
            logger.warning(f"Search attempt '{attempt}' failed: {e}")
            continue

    return sources


def analyze_document(
    document_text: str,
    applikation: str = "Justiz",
    max_sources: int = 5,
) -> DocumentAnalysisResponse:
    """Analyze a legal document and return defense strategies.

    Steps:
        1. Send document to Claude to extract key legal issues/search terms
        2. Use extracted terms to search RIS
        3. Send document + RIS results to Claude for full analysis

    Args:
        document_text: The full text of the uploaded document.
        applikation: RIS court application to search.
        max_sources: Maximum number of RIS sources to retrieve.

    Returns:
        DocumentAnalysisResponse with answer, sources, and extracted charges.
    """
    # Truncate very long documents to avoid token limits
    max_doc_chars = 15000
    truncated = document_text[:max_doc_chars]
    if len(document_text) > max_doc_chars:
        truncated += "\n\n[... Dokument gekürzt ...]"

    # Step 1: Extract search terms from the document
    logger.info("Step 1: Extracting legal terms from document...")
    extraction_prompt = DOCUMENT_EXTRACTION_PROMPT.format(document_text=truncated)
    extracted_terms = generate(
        user_prompt=extraction_prompt,
        system_prompt="Du bist ein juristischer Experte. Antworte nur mit Suchbegriffen.",
        max_tokens=200,
    )
    logger.info(f"Extracted terms: {extracted_terms}")

    # Step 2: Search RIS with extracted terms
    logger.info("Step 2: Searching RIS...")
    sources = _search_ris_for_document(
        search_terms=extracted_terms,
        applikation=applikation,
        max_sources=max_sources,
    )
    logger.info(f"Found {len(sources)} RIS sources")

    # Step 3: Generate full analysis
    logger.info("Step 3: Generating full document analysis...")
    if sources:
        context_parts = []
        for i, s in enumerate(sources, 1):
            header = f"[Quelle {i}] {s.gericht} {s.geschaeftszahl} ({s.datum})"
            if s.normen:
                header += f" | Normen: {', '.join(s.normen[:5])}"
            if s.source_url:
                header += f"\nLink: {s.source_url}"
            context_parts.append(f"{header}\n{s.full_text}")

        context = "\n\n---\n\n".join(context_parts)
        analysis_prompt = DOCUMENT_ANALYSIS_PROMPT.format(
            document_text=truncated,
            context=context,
        )
    else:
        analysis_prompt = DOCUMENT_ANALYSIS_NO_SOURCES_PROMPT.format(
            document_text=truncated,
        )

    answer = generate(
        user_prompt=analysis_prompt,
        system_prompt=SYSTEM_PROMPT,
        max_tokens=4096,
    )

    return DocumentAnalysisResponse(
        answer=answer,
        sources=sources,
        extracted_charges=extracted_terms,
        query_used=extracted_terms,
    )
