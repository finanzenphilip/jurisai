"""Client for the Austrian RIS OGD API v2.6 (Rechtsinformationssystem des Bundes).

Public REST API, no authentication required.
Docs: https://data.bka.gv.at/ris/api/v2.6/Help
License: CC BY 4.0 (commercial use allowed)
"""
from __future__ import annotations

import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Iterator, Optional

import requests

from config import RIS_API_BASE, RIS_REQUEST_DELAY, RAW_DIR

logger = logging.getLogger(__name__)

PAGE_SIZES = {"Ten": 10, "Twenty": 20, "Fifty": 50, "OneHundred": 100}

# In-process cache for RIS API responses (TTL 1 hour)
_API_CACHE: dict = {}
_CACHE_TTL_SECONDS = 3600


def _cache_key(method: str, params: dict) -> str:
    """Build a deterministic cache key from method + params."""
    payload = json.dumps({"m": method, "p": params}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _cache_get(key: str):
    """Return cached value if fresh, else None."""
    entry = _API_CACHE.get(key)
    if entry is None:
        return None
    ts, val = entry
    if time.time() - ts > _CACHE_TTL_SECONDS:
        _API_CACHE.pop(key, None)
        return None
    return val


def _cache_set(key: str, value):
    _API_CACHE[key] = (time.time(), value)


class RISClient:
    """Thin wrapper around the RIS OGD API v2.6 Judikatur + Bundesrecht endpoints."""

    def __init__(self, delay: float = RIS_REQUEST_DELAY, cache_dir: Path = RAW_DIR):
        self.base_url = f"{RIS_API_BASE}/Judikatur"
        self.delay = delay
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "RIS-Legal-AI/1.0 (legal research tool)",
        })

    def search(
        self,
        applikation: str = "Justiz",
        suchworte: str = "",
        norm: str = "",
        geschaeftszahl: str = "",
        datum_von: str = "",
        datum_bis: str = "",
        seite: int = 1,
        pro_seite: str = "OneHundred",
    ) -> dict:
        """Search the Judikatur endpoint with optional filters.

        Args:
            applikation: Court type (Justiz, Vwgh, Vfgh, Bvwg, Lvwg)
            suchworte: Full-text search terms
            norm: Legal norm filter (e.g. "StGB §127")
            geschaeftszahl: Case number (e.g. "1Ob535/90")
            datum_von: Start date YYYY-MM-DD
            datum_bis: End date YYYY-MM-DD
            seite: Page number (1-based)
            pro_seite: Page size (Ten, Twenty, Fifty, OneHundred)
        """
        params = {
            "Applikation": applikation,
            "DokumenteProSeite": pro_seite,
            "Seitennummer": seite,
        }
        if suchworte:
            params["Suchworte"] = suchworte
        if norm:
            params["Norm"] = norm
        if geschaeftszahl:
            params["Geschaeftszahl"] = geschaeftszahl
        if datum_von:
            params["EntscheidungsdatumVon"] = datum_von
        if datum_bis:
            params["EntscheidungsdatumBis"] = datum_bis

        logger.info(f"RIS API request: app={applikation}, page={seite}, search='{suchworte}'")

        cache_key = _cache_key("search_judikatur", params)
        cached = _cache_get(cache_key)
        if cached is not None:
            logger.info(f"  [cache hit] {applikation} p{seite} '{suchworte}'")
            return cached

        resp = self.session.get(self.base_url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        _cache_set(cache_key, data)
        return data

    def iter_decisions(
        self,
        applikation: str = "Justiz",
        suchworte: str = "",
        norm: str = "",
        datum_von: str = "",
        datum_bis: str = "",
        max_pages: int = 0,
    ) -> Iterator[dict]:
        """Iterate through all decisions matching the query, handling pagination.

        Yields individual OgdDocumentReference dicts.
        Set max_pages=0 for unlimited.
        """
        page = 1
        total_seen = 0

        while True:
            if max_pages > 0 and page > max_pages:
                break

            result = self.search(
                applikation=applikation,
                suchworte=suchworte,
                norm=norm,
                datum_von=datum_von,
                datum_bis=datum_bis,
                seite=page,
            )

            ogd_result = result.get("OgdSearchResult", {})
            doc_refs = ogd_result.get("OgdDocumentResults", {}).get("OgdDocumentReference", [])

            if not doc_refs:
                logger.info(f"No more results after page {page - 1}")
                break

            # Ensure it's always a list (single result comes as dict)
            if isinstance(doc_refs, dict):
                doc_refs = [doc_refs]

            for doc in doc_refs:
                total_seen += 1
                yield doc

            # Check if there are more pages
            hits_info = ogd_result.get("OgdDocumentResults", {}).get("Hits", {})
            page_size = PAGE_SIZES.get("OneHundred", 100)
            total_hits = int(hits_info.get("#text", "0")) if isinstance(hits_info, dict) else 0

            if total_hits > 0 and total_seen >= total_hits:
                logger.info(f"All {total_hits} results fetched")
                break

            page += 1
            time.sleep(self.delay)

        logger.info(f"Total decisions yielded: {total_seen}")

    def fetch_full_text(self, doc_ref: dict, fmt: str = "Html") -> Optional[str]:
        """Fetch the full text of a decision from its document URLs.

        Args:
            doc_ref: An OgdDocumentReference dict from the search results
            fmt: Format to fetch (Html, Xml, Rtf, Pdf)

        Returns:
            The full text content or None if not available.
        """
        try:
            doc_list = doc_ref.get("Data", {}).get("Dokumentliste", {})
            content_ref = doc_list.get("ContentReference", {})

            # ContentReference can be a list or single dict
            if isinstance(content_ref, list):
                refs = content_ref
            else:
                refs = [content_ref]

            for ref in refs:
                urls = ref.get("Urls", {}).get("ContentUrl", [])
                if isinstance(urls, dict):
                    urls = [urls]

                for url_entry in urls:
                    data_type = url_entry.get("DataType", "")
                    if data_type.lower() == fmt.lower():
                        url = url_entry.get("Url", "")
                        if url:
                            resp = self.session.get(url, timeout=30)
                            resp.raise_for_status()
                            resp.encoding = "utf-8"
                            time.sleep(0.3)
                            return resp.text
        except Exception as e:
            logger.warning(f"Failed to fetch full text: {e}")

        return None

    def cache_search_page(self, applikation: str, page: int, data: dict):
        """Cache a raw API response to disk."""
        cache_file = self.cache_dir / f"{applikation}_page_{page:04d}.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_total_count(self, applikation: str = "Justiz") -> int:
        """Get total number of documents for an application."""
        result = self.search(applikation=applikation, pro_seite="Ten", seite=1)
        hits = result.get("OgdSearchResult", {}).get("OgdDocumentResults", {}).get("Hits", {})
        if isinstance(hits, dict):
            return int(hits.get("#text", "0"))
        return 0

    # ------------------------------------------------------------------
    # Bundesrecht (consolidated federal law) endpoint
    # ------------------------------------------------------------------

    def search_bundesrecht(
        self,
        suchworte: str = "",
        norm: str = "",
        titel: str = "",
        paragraph: str = "",
        gesetzesnummer: str = "",
        fassung_vom: str = "",
        seite: int = 1,
        pro_seite: str = "Twenty",
    ) -> dict:
        """Search the Bundesrecht (consolidated federal law) endpoint.

        Args:
            suchworte: Full-text search terms (searches within law text)
            norm: Norm filter
            titel: Title filter (e.g. "Strafgesetzbuch") — MUCH more precise
            paragraph: Paragraph filter (API is unreliable, filter client-side)
            gesetzesnummer: Direct law number (e.g. "10002296" for StGB)
            fassung_vom: Return only the version valid on this date (YYYY-MM-DD).
                Use today's date to get currently valid law.
            seite: Page number (1-based)
            pro_seite: Page size (Ten, Twenty, Fifty, OneHundred)
        """
        params = {
            "Applikation": "BrKons",
            "DokumenteProSeite": pro_seite,
            "Seitennummer": seite,
        }
        if suchworte:
            params["Suchworte"] = suchworte
        if norm:
            params["Norm"] = norm
        if titel:
            params["Titel"] = titel
        if paragraph:
            params["Paragraph"] = paragraph
        if gesetzesnummer:
            params["Gesetzesnummer"] = gesetzesnummer
        if fassung_vom:
            params["FassungVom"] = fassung_vom

        url = f"{RIS_API_BASE}/Bundesrecht"
        logger.info(f"RIS Bundesrecht request: page={seite}, titel='{titel}', search='{suchworte}', paragraph='{paragraph}'")

        cache_key = _cache_key("search_bundesrecht", params)
        cached = _cache_get(cache_key)
        if cached is not None:
            logger.info(f"  [cache hit] Bundesrecht titel='{titel}' search='{suchworte}'")
            return cached

        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        _cache_set(cache_key, data)
        return data

    def fetch_gesetz_text(self, doc_ref: dict) -> Optional[str]:
        """Fetch the HTML full text of a Bundesrecht document.

        Uses the same Dokumentliste/ContentReference structure as Judikatur.
        Returns plain text extracted from HTML, or None.
        """
        html = self.fetch_full_text(doc_ref, fmt="Html")
        if not html:
            return None
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)
        except Exception as e:
            logger.warning(f"Failed to parse Gesetzestext HTML: {e}")
            return html

    def extract_bundesrecht_meta(self, doc_ref: dict) -> dict:
        """Extract metadata from a Bundesrecht OgdDocumentReference.

        Returns dict with: kurztitel, paragraph, gesetzesnummer,
        inkrafttretensdatum, kundmachungsorgan, source_url.
        """
        data = doc_ref.get("Data", {})
        metadaten = data.get("Metadaten", {})
        br = metadaten.get("Bundesrecht", {})
        br_kons = br.get("BrKons", {})

        kurztitel = str(br.get("Kurztitel", ""))
        paragraph = str(br_kons.get("ArtikelParagraphAnlage", ""))
        gesetzesnummer = str(br_kons.get("Gesetzesnummer", ""))
        inkrafttreten = str(br_kons.get("Inkrafttretensdatum", ""))
        if inkrafttreten and "T" in inkrafttreten:
            inkrafttreten = inkrafttreten.split("T")[0]
        kundmachung = str(br_kons.get("Kundmachungsorgan", ""))

        # Build source URL from ContentReference
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
            "kurztitel": kurztitel,
            "paragraph": paragraph,
            "gesetzesnummer": gesetzesnummer,
            "inkrafttretensdatum": inkrafttreten,
            "kundmachungsorgan": kundmachung,
            "source_url": source_url,
        }
