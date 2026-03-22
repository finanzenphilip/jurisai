"""Process RIS court decisions: parse HTML, extract metadata, chunk text."""
import re
import logging
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup

from config import CHUNK_SIZE_TOKENS, CHUNK_OVERLAP_TOKENS, MAX_CHUNK_CHARS

logger = logging.getLogger(__name__)

# Rough token estimation: 1 token ≈ 4 chars for German text
CHARS_PER_TOKEN = 4


@dataclass
class DocumentChunk:
    """A chunk of a court decision with full metadata."""
    text: str
    chunk_id: str
    geschaeftszahl: str
    gericht: str
    entscheidungsdatum: str
    rechtsgebiet: str = ""
    fachgebiet: str = ""
    normen: list[str] = field(default_factory=list)
    section: str = ""  # kopf, spruch, begruendung, rechtssatz
    chunk_index: int = 0
    total_chunks: int = 1
    dokumenttyp: str = ""
    applikation: str = ""
    source_url: str = ""

    def to_metadata(self) -> dict:
        return {
            "geschaeftszahl": self.geschaeftszahl,
            "gericht": self.gericht,
            "entscheidungsdatum": self.entscheidungsdatum,
            "rechtsgebiet": self.rechtsgebiet,
            "fachgebiet": self.fachgebiet,
            "normen": ", ".join(self.normen),
            "section": self.section,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "dokumenttyp": self.dokumenttyp,
            "applikation": self.applikation,
            "source_url": self.source_url,
        }


def extract_metadata(doc_ref: dict) -> dict:
    """Extract structured metadata from an OgdDocumentReference."""
    data = doc_ref.get("Data", {})
    metadaten = data.get("Metadaten", {})

    # The metadata structure varies by Applikation
    # Try common locations
    judikatur = metadaten.get("Judikatur", metadaten.get("Allgemein", {}))

    geschaeftszahl = ""
    gz_data = judikatur.get("Geschaeftszahl", data.get("Geschaeftszahl", ""))
    if isinstance(gz_data, dict):
        geschaeftszahl = gz_data.get("#text", str(gz_data))
    else:
        geschaeftszahl = str(gz_data)

    gericht = str(judikatur.get("Gericht", data.get("Gericht", "")))

    datum = str(judikatur.get("Entscheidungsdatum", data.get("Entscheidungsdatum", "")))
    # Normalize date format
    if datum and "T" in datum:
        datum = datum.split("T")[0]

    # Normen can be a list or string
    normen_raw = judikatur.get("Normen", data.get("Normen", ""))
    if isinstance(normen_raw, list):
        normen = [str(n) for n in normen_raw]
    elif isinstance(normen_raw, str) and normen_raw:
        normen = [n.strip() for n in normen_raw.split(";")]
    else:
        normen = []

    rechtsgebiet = str(judikatur.get("Rechtsgebiet", ""))
    fachgebiet = str(judikatur.get("Fachgebiet", ""))
    dokumenttyp = str(judikatur.get("Dokumenttyp", data.get("Dokumenttyp", "")))
    applikation = str(data.get("Applikation", ""))

    # Build source URL
    source_url = ""
    try:
        doc_list = data.get("Dokumentliste", {})
        content_ref = doc_list.get("ContentReference", {})
        if isinstance(content_ref, list):
            content_ref = content_ref[0]
        urls = content_ref.get("Urls", {}).get("ContentUrl", [])
        if isinstance(urls, dict):
            urls = [urls]
        for u in urls:
            if u.get("DataType", "").lower() == "html":
                source_url = u.get("Url", "")
                break
    except Exception:
        pass

    return {
        "geschaeftszahl": geschaeftszahl,
        "gericht": gericht,
        "entscheidungsdatum": datum,
        "normen": normen,
        "rechtsgebiet": rechtsgebiet,
        "fachgebiet": fachgebiet,
        "dokumenttyp": dokumenttyp,
        "applikation": applikation,
        "source_url": source_url,
    }


def parse_html_decision(html: str) -> dict[str, str]:
    """Parse a RIS HTML decision into sections.

    Returns dict with keys: kopf, spruch, begruendung, full_text
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style"]):
        tag.decompose()

    full_text = soup.get_text(separator="\n", strip=True)

    sections = {
        "kopf": "",
        "spruch": "",
        "begruendung": "",
        "full_text": full_text,
    }

    # Try to find structural sections
    # RIS decisions often use specific class names or heading patterns
    text = full_text

    # Common patterns in Austrian court decisions
    spruch_match = re.search(r'(?i)(S\s*p\s*r\s*u\s*c\s*h|Entscheidungsformel)', text)
    begruendung_match = re.search(
        r'(?i)(B\s*e\s*g\s*r\s*ü\s*n\s*d\s*u\s*n\s*g|Entscheidungsgründe|Gründe\s*:)',
        text
    )

    if spruch_match:
        sections["kopf"] = text[:spruch_match.start()].strip()
        if begruendung_match:
            sections["spruch"] = text[spruch_match.start():begruendung_match.start()].strip()
            sections["begruendung"] = text[begruendung_match.start():].strip()
        else:
            sections["spruch"] = text[spruch_match.start():].strip()
    elif begruendung_match:
        sections["kopf"] = text[:begruendung_match.start()].strip()
        sections["begruendung"] = text[begruendung_match.start():].strip()

    return sections


def chunk_text(text: str, target_tokens: int = CHUNK_SIZE_TOKENS, overlap_tokens: int = CHUNK_OVERLAP_TOKENS) -> list[str]:
    """Split text into chunks at paragraph boundaries with overlap.

    Uses paragraph-aware splitting to avoid breaking mid-sentence.
    """
    if not text.strip():
        return []

    target_chars = target_tokens * CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * CHARS_PER_TOKEN

    # Split on double newlines (paragraphs) first
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if not paragraphs:
        return [text.strip()] if text.strip() else []

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # If adding this paragraph exceeds target, save current and start new
        if current_chunk and len(current_chunk) + len(para) + 2 > target_chars:
            chunks.append(current_chunk.strip())
            # Start new chunk with overlap from end of previous
            if overlap_chars > 0 and len(current_chunk) > overlap_chars:
                # Find a sentence boundary near the overlap point
                overlap_text = current_chunk[-overlap_chars:]
                sentence_end = overlap_text.find(". ")
                if sentence_end > 0:
                    overlap_text = overlap_text[sentence_end + 2:]
                current_chunk = overlap_text + "\n\n" + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para

    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def process_decision(
    doc_ref: dict,
    full_text_html: Optional[str],
    applikation: str = "Justiz",
) -> list[DocumentChunk]:
    """Process a single court decision into chunks with metadata.

    Args:
        doc_ref: OgdDocumentReference from the API
        full_text_html: HTML content of the full decision (or None)
        applikation: Which RIS application this came from

    Returns:
        List of DocumentChunk objects ready for embedding
    """
    meta = extract_metadata(doc_ref)
    meta["applikation"] = applikation
    gz = meta["geschaeftszahl"]

    if not gz:
        logger.warning("Decision without Geschaeftszahl, skipping")
        return []

    chunks = []

    if full_text_html:
        sections = parse_html_decision(full_text_html)

        # Chunk the main reasoning section (or full text if no sections found)
        main_text = sections.get("begruendung") or sections.get("full_text", "")

        if not main_text.strip():
            return []

        text_chunks = chunk_text(main_text)

        for i, chunk_text_content in enumerate(text_chunks):
            chunk = DocumentChunk(
                text=chunk_text_content,
                chunk_id=f"{gz}_chunk_{i:03d}",
                geschaeftszahl=gz,
                gericht=meta["gericht"],
                entscheidungsdatum=meta["entscheidungsdatum"],
                rechtsgebiet=meta["rechtsgebiet"],
                fachgebiet=meta["fachgebiet"],
                normen=meta["normen"],
                section="begruendung" if sections.get("begruendung") else "full_text",
                chunk_index=i,
                total_chunks=len(text_chunks),
                dokumenttyp=meta["dokumenttyp"],
                applikation=applikation,
                source_url=meta["source_url"],
            )
            chunks.append(chunk)

        # Also add Kopf + Spruch as a single summary chunk if available
        summary_parts = []
        if sections.get("kopf"):
            summary_parts.append(sections["kopf"][:500])
        if sections.get("spruch"):
            summary_parts.append(sections["spruch"][:1000])

        if summary_parts:
            summary = "\n\n".join(summary_parts)
            chunks.insert(0, DocumentChunk(
                text=summary,
                chunk_id=f"{gz}_summary",
                geschaeftszahl=gz,
                gericht=meta["gericht"],
                entscheidungsdatum=meta["entscheidungsdatum"],
                rechtsgebiet=meta["rechtsgebiet"],
                fachgebiet=meta["fachgebiet"],
                normen=meta["normen"],
                section="summary",
                chunk_index=0,
                total_chunks=len(text_chunks) + 1,
                dokumenttyp=meta["dokumenttyp"],
                applikation=applikation,
                source_url=meta["source_url"],
            ))
    else:
        # No full text available — create a metadata-only chunk from API data
        api_text = f"Entscheidung {gz} vom {meta['entscheidungsdatum']}, {meta['gericht']}"
        if meta["normen"]:
            api_text += f"\nNormen: {', '.join(meta['normen'])}"

        chunks.append(DocumentChunk(
            text=api_text,
            chunk_id=f"{gz}_meta",
            geschaeftszahl=gz,
            gericht=meta["gericht"],
            entscheidungsdatum=meta["entscheidungsdatum"],
            rechtsgebiet=meta["rechtsgebiet"],
            fachgebiet=meta["fachgebiet"],
            normen=meta["normen"],
            section="metadata",
            chunk_index=0,
            total_chunks=1,
            dokumenttyp=meta["dokumenttyp"],
            applikation=applikation,
            source_url=meta["source_url"],
        ))

    return chunks
