"""Streamlit web interface for RIS Legal AI."""
from __future__ import annotations

import sys
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
    .example-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 1.5rem;
    }
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
    .stChatMessage { max-width: 800px; }
    [data-testid="stChatMessageContent"] {
        border: 1px solid #e5e7eb !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }

    /* -- SOURCE CARDS -- */
    .source-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 6px;
        font-size: 0.82rem;
        transition: border-color 0.2s;
    }
    .source-card:hover {
        border-color: #4338ca;
    }
    .source-card .source-title {
        font-weight: 600;
        color: #1a1a2e;
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
        font-size: 0.75rem;
        margin-top: 2px;
    }

    /* -- FOLLOW-UP SUGGESTIONS -- */
    .followup-container {
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid #f3f4f6;
    }
    .followup-label {
        font-size: 0.68rem;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
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

    /* -- HIDE STREAMLIT -- */
    #MainMenu, footer, header { visibility: hidden; }

    /* -- MOBILE -- */
    @media (max-width: 768px) {
        .jurai-header { padding: 1.5rem 0.5rem 1rem; }
        .jurai-header h1 { font-size: 2rem; }
        .main .block-container { padding: 0.5rem 0.8rem; }
        .example-grid { grid-template-columns: 1fr; }
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="jurai-header">
    <h1>Juris<span>AI</span></h1>
    <div class="tagline">Juristische Recherche fur osterreichisches Recht</div>
    <div class="badges">
        <div class="badge"><div class="dot"></div>Verbunden mit RIS-Datenbank</div>
        <div class="badge">Gesetze + Rechtsprechung</div>
        <div class="badge">AI-Analyse</div>
    </div>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

# --- Sidebar ---
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
        help="Sucht zuerst letzte 2 Jahre, dann 5 Jahre, dann alle. Neueste Urteile zuerst.")

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
        "Alle Ergebnisse anhand der Originalquellen verifizieren."
        "</div>", unsafe_allow_html=True)
    st.markdown('<div class="footer">JurisAI &middot; Claude AI &middot; RIS OGD API</div>', unsafe_allow_html=True)

# --- Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []


def _render_sources(msg, idx):
    """Render source cards for a message."""
    gesetz_sources = msg.get("gesetz_sources", [])
    sources = msg.get("sources", [])

    if not gesetz_sources and not sources:
        return

    total = len(gesetz_sources) + len(sources)
    with st.expander(f"Quellen ({total})", expanded=True):
        if gesetz_sources:
            st.markdown("**Gesetze**")
            for g in gesetz_sources:
                label = f"{g.get('kurztitel','')} {g.get('paragraph','')}"
                url = g.get("url", "")
                if url:
                    st.markdown(f'<div class="source-card"><div class="source-title"><a href="{url}" target="_blank">{label}</a></div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="source-card"><div class="source-title">{label}</div></div>', unsafe_allow_html=True)

        if sources:
            st.markdown("**Rechtsprechung**")
            for s in sources:
                gz = s.get("geschaeftszahl", "")
                gericht = s.get("gericht", "")
                datum = s.get("datum", "")
                url = s.get("url", "")
                preview = s.get("text_preview", "")
                if url:
                    title_html = f'<a href="{url}" target="_blank">{gericht} {gz}</a>'
                else:
                    title_html = f'{gericht} {gz}'
                meta_html = f' &middot; {datum}' if datum else ''
                st.markdown(
                    f'<div class="source-card">'
                    f'<div class="source-title">{title_html}</div>'
                    f'<div class="source-meta">{meta_html}</div>'
                    f'</div>',
                    unsafe_allow_html=True)


def _render_actions(msg, idx):
    """Render action buttons (Schriftsatz, Export) for assistant messages."""
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


# Render chat history
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg.get("query_used") and msg["role"] == "assistant":
            st.markdown(f'<div class="query-badge">Suche: {msg["query_used"]}</div>', unsafe_allow_html=True)
        st.markdown(msg["content"])
        _render_sources(msg, idx)
        _render_actions(msg, idx)

# --- Follow-up suggestions (after last message) ---
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

# --- Welcome ---
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

# --- Schriftsatz ---
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

# --- Document Analysis ---
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
                            gz = s.geschaeftszahl
                            sources_data.append({
                                "geschaeftszahl": gz, "gericht": s.gericht,
                                "datum": s.datum, "url": s.source_url,
                                "text_preview": s.text_preview[:300] if s.text_preview else "",
                            })
                    st.session_state.messages.append({
                        "role": "assistant", "content": response.answer, "sources": sources_data,
                    })
                except Exception as e:
                    st.error(str(e))
                    st.session_state.messages.append({"role": "assistant", "content": f"Fehler: {e}"})

# --- Chat Input ---
pending = st.session_state.pop("pending_question", None)
prompt = pending or st.chat_input("Rechtsfrage eingeben...")
if prompt:
    st.session_state.pop("followups", None)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        # Progress indicator
        status_container = st.empty()

        def show_progress(step: str):
            status_container.markdown(
                f'<div class="search-steps"><div class="spinner"></div>{step}</div>',
                unsafe_allow_html=True,
            )

        try:
            from generation.live_search import stream_search_with_history, generate_followup_questions

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

            # Clear progress indicator
            status_container.empty()

            # Show search query badge
            if used_search:
                st.markdown(f'<div class="query-badge">Suche: {used_search}</div>', unsafe_allow_html=True)

            # Stream the response
            full_response = st.write_stream(stream)

            # Build source data
            sources_data, gesetz_data = [], []
            if gesetz_sources:
                with st.expander(f"Gesetze ({len(gesetz_sources)})", expanded=True):
                    for g in gesetz_sources:
                        label = f"{g.kurztitel} {g.paragraph}"
                        url = g.source_url or ""
                        if url:
                            st.markdown(f'<div class="source-card"><div class="source-title"><a href="{url}" target="_blank">{label}</a></div></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="source-card"><div class="source-title">{label}</div></div>', unsafe_allow_html=True)
                        if g.kundmachungsorgan:
                            st.caption(g.kundmachungsorgan)
                        gesetz_data.append({"kurztitel": g.kurztitel, "paragraph": g.paragraph, "url": url})

            if sources:
                with st.expander(f"Rechtsprechung ({len(sources)})", expanded=True):
                    for s in sources:
                        gz = s.geschaeftszahl
                        url = s.source_url or ""
                        gericht = s.gericht
                        datum = s.datum
                        if url:
                            title_html = f'<a href="{url}" target="_blank">{gericht} {gz}</a>'
                        else:
                            title_html = f'{gericht} {gz}'
                        meta_html = f' &middot; {datum}' if datum else ''
                        normen_html = f' &middot; {", ".join(s.normen[:3])}' if s.normen else ''
                        st.markdown(
                            f'<div class="source-card">'
                            f'<div class="source-title">{title_html}</div>'
                            f'<div class="source-meta">{meta_html}{normen_html}</div>'
                            f'</div>',
                            unsafe_allow_html=True)
                        sources_data.append({
                            "geschaeftszahl": gz, "gericht": gericht, "datum": datum,
                            "url": url, "text_preview": s.text_preview[:300] if s.text_preview else "",
                        })

            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "sources": sources_data,
                "gesetz_sources": gesetz_data,
                "query_used": used_search,
            })

            # Generate follow-up suggestions in background
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
