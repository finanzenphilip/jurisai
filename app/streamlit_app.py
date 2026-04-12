"""Streamlit web interface for RIS Legal AI — professional lawyer-grade tool."""
from __future__ import annotations

import sys
import html as html_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from config import COURT_APPS
from generation.pdf_export import generate_export_html

st.set_page_config(
    page_title="JurisAI — Juristische Recherche",
    page_icon="https://em-content.zobj.net/source/apple/391/balance-scale_2696-fe0f.png",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- Clean Professional CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

    .stApp { background: #fafafa; }

    /* -- HEADER -- */
    .jurai-header {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
    }
    .jurai-header h1 {
        font-family: 'DM Serif Display', serif;
        font-size: 2.6rem;
        color: #1a1a2e;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .jurai-header h1 span { color: #4338ca; }
    .jurai-header .tagline {
        color: #6b7280;
        font-size: 0.95rem;
        margin-top: 6px;
        font-weight: 400;
    }
    .jurai-header .badges {
        display: flex;
        justify-content: center;
        gap: 8px;
        margin-top: 14px;
        flex-wrap: wrap;
    }
    .jurai-header .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.7rem;
        color: #6b7280;
        background: white;
        border: 1px solid #e5e7eb;
        padding: 4px 12px;
        border-radius: 20px;
    }
    .jurai-header .badge .dot {
        width: 6px; height: 6px;
        background: #22c55e;
        border-radius: 50%;
        animation: blink 2s ease-in-out infinite;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    /* -- DIVIDER -- */
    .divider {
        width: 60px;
        height: 2px;
        background: #4338ca;
        margin: 0 auto 1.5rem;
    }

    /* -- SEARCH STEP INDICATOR -- */
    .search-steps {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 12px 16px;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        margin-bottom: 12px;
        font-size: 0.82rem;
        color: #4338ca;
        font-weight: 500;
    }
    .search-steps .spinner {
        width: 14px; height: 14px;
        border: 2px solid #e5e7eb;
        border-top-color: #4338ca;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* -- EXAMPLE CARDS -- */
    .example-category {
        font-size: 0.68rem;
        font-weight: 700;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 6px;
        margin-top: 8px;
    }
    div[data-testid="column"] .stButton > button {
        text-align: left;
        background: white;
        border: 1px solid #e5e7eb;
        color: #374151;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 0.85rem;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        width: 100%;
    }
    div[data-testid="column"] .stButton > button:hover {
        border-color: #4338ca;
        color: #4338ca;
        box-shadow: 0 2px 8px rgba(67,56,202,0.1);
        transform: translateY(-1px);
    }

    /* -- SIDEBAR -- */
    section[data-testid="stSidebar"] {
        background: #fafafa;
        border-right: 1px solid #e5e7eb;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #1a1a2e;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* -- CHAT -- */
    .stChatMessage { max-width: 820px; }
    [data-testid="stChatMessageContent"] {
        border: 1px solid #e5e7eb !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }

    /* -- SOURCE CARDS -- */
    .source-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 8px;
        transition: all 0.15s ease;
        position: relative;
    }
    .source-card:hover {
        border-color: #4338ca;
        box-shadow: 0 2px 8px rgba(67,56,202,0.06);
    }
    .source-card .source-header {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 4px;
    }
    .source-card .source-title {
        font-weight: 600;
        color: #1a1a2e;
        font-size: 0.88rem;
        flex: 1;
        min-width: 150px;
    }
    .source-card .source-title a {
        color: #4338ca;
        text-decoration: none;
    }
    .source-card .source-title a:hover {
        text-decoration: underline;
    }
    .source-card .source-meta {
        color: #6b7280;
        font-size: 0.73rem;
        margin-top: 4px;
    }
    .source-card .citation-code {
        background: #f3f4f6;
        color: #374151;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 0.72rem;
        user-select: all;
        cursor: text;
    }

    /* -- DOC TYPE BADGES -- */
    .doc-badge {
        display: inline-block;
        font-size: 0.62rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap;
    }
    .doc-badge.rechtssatz {
        background: #ddd6fe;
        color: #5b21b6;
    }
    .doc-badge.entscheidung {
        background: #dbeafe;
        color: #1e40af;
    }
    .doc-badge.gesetz {
        background: #d1fae5;
        color: #065f46;
    }
    .doc-badge.recent {
        background: #fef3c7;
        color: #92400e;
    }

    /* -- VERIFICATION WARNING -- */
    .verify-warning {
        background: #fef2f2;
        border: 1px solid #fca5a5;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 0.82rem;
        color: #991b1b;
        margin-top: 12px;
    }
    .verify-success {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 0.78rem;
        color: #166534;
        margin-top: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* -- FOLLOW-UP SUGGESTIONS -- */
    .followup-label {
        font-size: 0.68rem;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
        margin-top: 12px;
    }

    /* -- BUTTONS -- */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.85rem;
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"] {
        background: #4338ca;
        color: white;
        border: none;
    }
    .stButton > button[kind="primary"]:hover {
        background: #3730a3;
    }

    /* -- CHAT INPUT -- */
    [data-testid="stChatInput"] {
        border: 1px solid #e5e7eb !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    }
    [data-testid="stChatInput"] textarea {
        font-size: 0.95rem !important;
    }

    /* -- EXPANDER -- */
    [data-testid="stExpander"] {
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        background: white !important;
    }

    /* -- DISCLAIMER -- */
    .disclaimer {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 0.75rem;
        color: #92400e;
        line-height: 1.5;
        margin-top: 16px;
    }

    /* -- FOOTER -- */
    .footer {
        text-align: center;
        font-size: 0.7rem;
        color: #9ca3af;
        padding: 1rem 0;
        border-top: 1px solid #e5e7eb;
        margin-top: 1rem;
    }

    /* -- QUERY BADGE -- */
    .query-badge {
        display: inline-block;
        background: #eef2ff;
        color: #4338ca;
        font-size: 0.72rem;
        padding: 3px 10px;
        border-radius: 12px;
        margin-bottom: 8px;
        font-weight: 500;
    }

    /* -- HISTORY ITEM -- */
    .history-item {
        font-size: 0.78rem;
        color: #4b5563;
        padding: 6px 10px;
        border-radius: 6px;
        cursor: pointer;
        margin-bottom: 2px;
    }
    .history-item:hover {
        background: #eef2ff;
        color: #4338ca;
    }

    /* -- HIDE STREAMLIT -- */
    #MainMenu, footer, header { visibility: hidden; }

    /* -- MOBILE -- */
    @media (max-width: 768px) {
        .jurai-header { padding: 1.5rem 0.5rem 1rem; }
        .jurai-header h1 { font-size: 2rem; }
        .main .block-container { padding: 0.5rem 0.8rem; }
    }
</style>
""", unsafe_allow_html=True)


# ================ HELPERS ================

def _source_to_dict(s) -> dict:
    """Convert LiveSource to dict for session storage."""
    return {
        "geschaeftszahl": s.geschaeftszahl,
        "gericht": s.gericht,
        "datum": s.datum,
        "url": s.source_url or "",
        "text_preview": (s.text_preview or "")[:300],
        "dokumenttyp": s.dokumenttyp,
        "rechtsgebiet": s.rechtsgebiet,
    }


def _is_recent(date_str: str, days: int = 730) -> bool:
    """Check if ISO date string is within the last N days."""
    from datetime import datetime
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        delta = (datetime.now() - d).days
        return 0 <= delta <= days
    except Exception:
        return False


def _format_citation(gericht: str, datum: str, gz: str) -> str:
    """Build 'OGH 15.03.2023, 7Ob40/22s' formal citation string."""
    try:
        y, m, d = datum.split("-")
        datum = f"{d}.{m}.{y}"
    except Exception:
        pass
    parts = [p for p in [gericht, datum] if p]
    citation = " ".join(parts)
    if gz:
        citation += f", {gz}"
    return citation


def _render_source_card(*, title: str, title_url: str, citation_code: str,
                         badge_class: str, badge_label: str, meta_parts: list[str],
                         is_recent: bool = False):
    """Render a single source card with badge + copy-friendly citation."""
    recent_badge = '<span class="doc-badge recent">NEU</span>' if is_recent else ''
    badge = f'<span class="doc-badge {badge_class}">{badge_label}</span>'
    if title_url:
        title_html = f'<a href="{html_module.escape(title_url)}" target="_blank">{html_module.escape(title)}</a>'
    else:
        title_html = html_module.escape(title)
    meta = html_module.escape(" · ".join(p for p in meta_parts if p))
    citation_html = ""
    if citation_code:
        citation_html = f'<div class="source-meta">Zitat: <span class="citation-code">{html_module.escape(citation_code)}</span></div>'
    st.markdown(
        f'<div class="source-card">'
        f'<div class="source-header">{badge}{recent_badge}<span class="source-title">{title_html}</span></div>'
        f'{f"<div class=source-meta>{meta}</div>" if meta else ""}'
        f'{citation_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ================ HEADER ================

st.markdown("""
<div class="jurai-header">
    <h1>Juris<span>AI</span></h1>
    <div class="tagline">Juristische Recherche fur osterreichisches Recht</div>
    <div class="badges">
        <div class="badge"><div class="dot"></div>RIS-Datenbank live</div>
        <div class="badge">Aktuelle Rechtsprechung</div>
        <div class="badge">Verifizierte Zitate</div>
    </div>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)


# ================ SIDEBAR ================

with st.sidebar:
    if st.button("Neue Recherche", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.pop("followups", None)
        st.rerun()

    st.divider()
    st.markdown("### Suchfilter")

    gericht_options = ["Alle Gerichte"] + list(COURT_APPS.keys())
    selected_app = st.selectbox("Gericht", gericht_options,
        format_func=lambda x: f"{x} — {COURT_APPS[x]}" if x in COURT_APPS else x)
    applikation = selected_app if selected_app != "Alle Gerichte" else None

    norm = st.text_input("Norm", placeholder="z.B. StGB §127")
    norm = norm if norm else None
    n_results = st.slider("Quellenanzahl", 2, 10, 5)
    prefer_recent = st.toggle("Aktuelle Rechtsprechung bevorzugen", value=True,
        help="Multi-Wave: letzte 2 Jahre, dann 5 Jahre, dann alle. Neueste Urteile zuerst.")

    st.divider()

    # Session history
    history_items = st.session_state.get("search_history", [])
    if history_items:
        st.markdown("### Letzte Recherchen")
        for i, item in enumerate(history_items[-5:][::-1]):
            if st.button(item[:40] + ("..." if len(item) > 40 else ""),
                         key=f"hist_{i}", use_container_width=True):
                st.session_state.pending_question = item
                st.rerun()
        st.divider()

    st.markdown("### Dokument hochladen")
    uploaded_file = st.file_uploader("PDF / TXT", type=["pdf", "txt"])
    if uploaded_file:
        st.success(f"{uploaded_file.name}")
        if st.button("Analysieren", use_container_width=True):
            st.session_state.analyze_document = True
            st.session_state.uploaded_file_data = uploaded_file.getvalue()
            st.session_state.uploaded_file_name = uploaded_file.name
            st.rerun()

    st.divider()
    st.markdown(
        '<div class="disclaimer">'
        "<strong>Hinweis:</strong> KI-gestutzte Recherche — keine Rechtsberatung. "
        "Zitate werden gegen die Quellen verifiziert, aber Originalquellen immer prufen."
        "</div>", unsafe_allow_html=True)
    st.markdown('<div class="footer">JurisAI &middot; Claude AI &middot; RIS OGD API</div>',
                unsafe_allow_html=True)


# ================ SESSION STATE ================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "search_history" not in st.session_state:
    st.session_state.search_history = []


# ================ RENDERING ================

def _render_sources(msg, idx):
    """Render source cards grouped by type for a stored message."""
    gesetz_sources = msg.get("gesetz_sources", [])
    sources = msg.get("sources", [])

    if not gesetz_sources and not sources:
        return

    # Split sources by type
    rechtssaetze = [s for s in sources if s.get("dokumenttyp") == "Rechtssatz"]
    entscheidungen = [s for s in sources if s.get("dokumenttyp") != "Rechtssatz"]

    total = len(gesetz_sources) + len(sources)
    with st.expander(f"Quellen ({total})", expanded=True):
        if gesetz_sources:
            st.markdown("**Geltende Gesetze**")
            for g in gesetz_sources:
                title = f"{g.get('kurztitel','')} {g.get('paragraph','')}"
                _render_source_card(
                    title=title,
                    title_url=g.get("url", ""),
                    citation_code=title,
                    badge_class="gesetz",
                    badge_label="Aktuelle Fassung",
                    meta_parts=[g.get("kundmachungsorgan", "")],
                )

        if rechtssaetze:
            st.markdown("**Rechtssätze** — distillierte Rechtsprinzipien")
            for s in rechtssaetze:
                gericht = s.get("gericht", "")
                datum = s.get("datum", "")
                gz = s.get("geschaeftszahl", "")
                title = f"{gericht} {gz}"
                citation = _format_citation(gericht, datum, gz)
                meta = []
                if datum:
                    meta.append(datum)
                if s.get("rechtsgebiet"):
                    meta.append(s["rechtsgebiet"])
                _render_source_card(
                    title=title,
                    title_url=s.get("url", ""),
                    citation_code=citation,
                    badge_class="rechtssatz",
                    badge_label="Rechtssatz",
                    meta_parts=meta,
                    is_recent=_is_recent(datum),
                )

        if entscheidungen:
            st.markdown("**Einzelentscheidungen**")
            for s in entscheidungen:
                gericht = s.get("gericht", "")
                datum = s.get("datum", "")
                gz = s.get("geschaeftszahl", "")
                title = f"{gericht} {gz}"
                citation = _format_citation(gericht, datum, gz)
                meta = []
                if datum:
                    meta.append(datum)
                if s.get("rechtsgebiet"):
                    meta.append(s["rechtsgebiet"])
                _render_source_card(
                    title=title,
                    title_url=s.get("url", ""),
                    citation_code=citation,
                    badge_class="entscheidung",
                    badge_label=s.get("dokumenttyp") or "Entscheidung",
                    meta_parts=meta,
                    is_recent=_is_recent(datum),
                )


def _render_verification(msg):
    """Render citation verification badge."""
    cited_count = msg.get("cited_count", 0)
    hallucinated = msg.get("hallucinated_gz", [])
    if cited_count == 0:
        return
    if hallucinated:
        hallu_str = ", ".join(sorted(hallucinated)[:5])
        st.markdown(
            f'<div class="verify-warning">'
            f'⚠️ <strong>Warnung:</strong> {len(hallucinated)} Geschäftszahl(en) im Text konnten nicht in den Quellen verifiziert werden: '
            f'<code>{html_module.escape(hallu_str)}</code>. Bitte im RIS direkt prüfen.'
            f'</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="verify-success">'
            f'✓ Alle {cited_count} zitierten Geschäftszahlen in den Quellen verifiziert'
            f'</div>',
            unsafe_allow_html=True)


def _render_actions(msg, idx):
    """Render Schriftsatz + Export buttons for assistant messages."""
    if msg["role"] != "assistant" or not msg.get("content") or msg["content"].startswith("Fehler"):
        return
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Schriftsatz erstellen", key=f"b_{idx}", use_container_width=True):
            st.session_state.generate_schriftsatz_from = msg["content"]
            st.rerun()
    with c2:
        st.download_button("Als HTML exportieren", generate_export_html(st.session_state.messages),
            file_name="recherche.html", mime="text/html", key=f"e_{idx}", use_container_width=True)


# Render existing conversation
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg.get("query_used") and msg["role"] == "assistant":
            st.markdown(f'<div class="query-badge">Suche: {html_module.escape(msg["query_used"])}</div>',
                        unsafe_allow_html=True)
        st.markdown(msg["content"])
        _render_sources(msg, idx)
        _render_verification(msg)
        _render_actions(msg, idx)


# Follow-up suggestions after last assistant message
followups = st.session_state.get("followups", [])
if followups and st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    st.markdown('<div class="followup-label">Weiterfuhrende Fragen</div>', unsafe_allow_html=True)
    cols = st.columns(len(followups))
    for i, (col, fq) in enumerate(zip(cols, followups)):
        with col:
            if st.button(fq, key=f"fq_{i}", use_container_width=True):
                st.session_state.pending_question = fq
                st.session_state.pop("followups", None)
                st.rerun()


# ================ WELCOME SCREEN ================

if not st.session_state.messages:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="example-category">Strafrecht</div>', unsafe_allow_html=True)
        for ex in [
            "Was passiert bei Diebstahl?",
            "Verteidigung bei Korperverletzung?",
            "Wann bekommt man Diversion?",
            "Wann ist eine Tat verjahrt?",
        ]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()
        st.markdown('<div class="example-category">Zivilrecht & Mietrecht</div>', unsafe_allow_html=True)
        for ex in [
            "Kundigungsfristen im Mietrecht?",
            "Schadenersatz — wann verjahrt?",
            "Rechte als Mieter bei Mangeln?",
            "Unterlassungsklage einbringen?",
        ]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()
    with col2:
        st.markdown('<div class="example-category">Arbeitsrecht</div>', unsafe_allow_html=True)
        for ex in [
            "Kundigungsfristen fur Angestellte?",
            "Wann ist Entlassung gerechtfertigt?",
            "Wie funktioniert Abfertigung Neu?",
            "Dienstverhinderung — Anspruche?",
        ]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()
        st.markdown('<div class="example-category">Verwaltungsrecht</div>', unsafe_allow_html=True)
        for ex in [
            "Beschwerde gegen Bescheid?",
            "Rechte bei Polizei-Vernehmung?",
            "Fristen im Verwaltungsverfahren?",
            "Verwaltungsakt — wann nichtig?",
        ]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()


# ================ SCHRIFTSATZ ================

if st.session_state.get("generate_schriftsatz_from"):
    research_text = st.session_state.pop("generate_schriftsatz_from")
    st.session_state.messages.append({"role": "user", "content": "Schriftsatz generieren"})
    with st.chat_message("user"):
        st.markdown("Schriftsatz generieren")
    with st.chat_message("assistant"):
        with st.spinner("Schriftsatz wird erstellt..."):
            try:
                from generation.schriftsatz import generate_schriftsatz
                result = generate_schriftsatz(research_text)
                st.markdown(result)
                st.session_state.messages.append({"role": "assistant", "content": result})
            except Exception as e:
                st.error(str(e))
                st.session_state.messages.append({"role": "assistant", "content": f"Fehler: {e}"})


# ================ DOCUMENT ANALYSIS ================

if st.session_state.get("analyze_document"):
    st.session_state.analyze_document = False
    file_data = st.session_state.pop("uploaded_file_data", None)
    file_name = st.session_state.pop("uploaded_file_name", "Dokument")
    if file_data:
        st.session_state.messages.append({"role": "user", "content": f"Analyse: {file_name}"})
        with st.chat_message("user"):
            st.markdown(f"Analyse: {file_name}")
        with st.chat_message("assistant"):
            with st.spinner("Dokument wird analysiert..."):
                try:
                    from generation.document_analyzer import extract_text_from_upload, analyze_document

                    class _P:
                        def __init__(s, d, n):
                            s.name = n
                            s.size = len(d)
                            s._data = d
                        def read(s): return s._data
                        def getvalue(s): return s._data

                    doc_text = extract_text_from_upload(_P(file_data, file_name))
                    if not doc_text.strip():
                        raise ValueError("Kein Text gefunden.")
                    response = analyze_document(doc_text, applikation or "Justiz", n_results)
                    st.markdown(response.answer)
                    sources_data = []
                    if response.sources:
                        for s in response.sources:
                            sources_data.append({
                                "geschaeftszahl": s.geschaeftszahl,
                                "gericht": s.gericht,
                                "datum": s.datum,
                                "url": s.source_url,
                                "text_preview": s.text_preview[:300] if s.text_preview else "",
                                "dokumenttyp": getattr(s, "dokumenttyp", ""),
                                "rechtsgebiet": getattr(s, "rechtsgebiet", ""),
                            })
                    st.session_state.messages.append({
                        "role": "assistant", "content": response.answer, "sources": sources_data,
                    })
                except Exception as e:
                    st.error(str(e))
                    st.session_state.messages.append({"role": "assistant", "content": f"Fehler: {e}"})


# ================ CHAT INPUT ================

pending = st.session_state.pop("pending_question", None)
prompt = pending or st.chat_input("Rechtsfrage eingeben...")
if prompt:
    st.session_state.pop("followups", None)
    # Add to history (dedup)
    if prompt not in st.session_state.search_history:
        st.session_state.search_history.append(prompt)
        st.session_state.search_history = st.session_state.search_history[-20:]  # keep last 20

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        status_container = st.empty()

        def show_progress(step: str):
            status_container.markdown(
                f'<div class="search-steps"><div class="spinner"></div>{step}</div>',
                unsafe_allow_html=True,
            )

        try:
            from generation.live_search import (
                stream_search_with_history, generate_followup_questions, verify_citations,
            )

            history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]

            sources, gesetz_sources, used_search, stream = stream_search_with_history(
                question=prompt,
                history=history,
                applikation=applikation or "Justiz",
                norm=norm or "",
                max_sources=n_results,
                progress_callback=show_progress,
                prefer_recent=prefer_recent,
            )

            status_container.empty()

            if used_search:
                st.markdown(f'<div class="query-badge">Suche: {html_module.escape(used_search)}</div>',
                            unsafe_allow_html=True)

            full_response = st.write_stream(stream)

            # Build sources data + show cards
            sources_data, gesetz_data = [], []

            if gesetz_sources or sources:
                total = len(gesetz_sources) + len(sources)
                with st.expander(f"Quellen ({total})", expanded=True):
                    if gesetz_sources:
                        st.markdown("**Geltende Gesetze**")
                        for g in gesetz_sources:
                            title = f"{g.kurztitel} {g.paragraph}"
                            _render_source_card(
                                title=title,
                                title_url=g.source_url or "",
                                citation_code=title,
                                badge_class="gesetz",
                                badge_label="Aktuelle Fassung",
                                meta_parts=[g.kundmachungsorgan or ""],
                            )
                            gesetz_data.append({
                                "kurztitel": g.kurztitel, "paragraph": g.paragraph,
                                "url": g.source_url or "",
                                "kundmachungsorgan": g.kundmachungsorgan or "",
                            })

                    rechtssaetze = [s for s in sources if s.is_rechtssatz]
                    entscheidungen = [s for s in sources if not s.is_rechtssatz]

                    if rechtssaetze:
                        st.markdown("**Rechtssätze** — distillierte Rechtsprinzipien")
                        for s in rechtssaetze:
                            title = f"{s.gericht} {s.geschaeftszahl}"
                            citation = s.formatted_citation()
                            meta = [s.datum] if s.datum else []
                            if s.rechtsgebiet:
                                meta.append(s.rechtsgebiet)
                            _render_source_card(
                                title=title,
                                title_url=s.source_url or "",
                                citation_code=citation,
                                badge_class="rechtssatz",
                                badge_label="Rechtssatz",
                                meta_parts=meta,
                                is_recent=_is_recent(s.datum),
                            )
                            sources_data.append(_source_to_dict(s))

                    if entscheidungen:
                        st.markdown("**Einzelentscheidungen**")
                        for s in entscheidungen:
                            title = f"{s.gericht} {s.geschaeftszahl}"
                            citation = s.formatted_citation()
                            meta = [s.datum] if s.datum else []
                            if s.rechtsgebiet:
                                meta.append(s.rechtsgebiet)
                            _render_source_card(
                                title=title,
                                title_url=s.source_url or "",
                                citation_code=citation,
                                badge_class="entscheidung",
                                badge_label=s.dokumenttyp or "Entscheidung",
                                meta_parts=meta,
                                is_recent=_is_recent(s.datum),
                            )
                            sources_data.append(_source_to_dict(s))

            # Citation verification
            cited, hallucinated = verify_citations(full_response, sources)
            if cited:
                if hallucinated:
                    hallu_str = ", ".join(sorted(hallucinated)[:5])
                    st.markdown(
                        f'<div class="verify-warning">'
                        f'⚠️ <strong>Warnung:</strong> {len(hallucinated)} Geschäftszahl(en) konnten nicht in den Quellen verifiziert werden: '
                        f'<code>{html_module.escape(hallu_str)}</code>. Bitte im RIS direkt prüfen.'
                        f'</div>',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<div class="verify-success">✓ Alle {len(cited)} zitierten Geschäftszahlen verifiziert</div>',
                        unsafe_allow_html=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "sources": sources_data,
                "gesetz_sources": gesetz_data,
                "query_used": used_search,
                "cited_count": len(cited),
                "hallucinated_gz": list(hallucinated),
            })

            # Background: generate follow-ups
            try:
                followups = generate_followup_questions(prompt, full_response)
                if followups:
                    st.session_state.followups = followups
                    st.rerun()
            except Exception:
                pass

        except Exception as e:
            status_container.empty()
            st.error(str(e))
            st.session_state.messages.append({"role": "assistant", "content": f"Fehler: {e}"})
