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
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

    .stApp { background: #fafafa; }

    /* ── HEADER ── */
    .jurai-header {
        text-align: center;
        padding: 3rem 1rem 2rem;
    }
    .jurai-header h1 {
        font-family: 'DM Serif Display', serif;
        font-size: 2.4rem;
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
    .jurai-header .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-top: 12px;
        font-size: 0.72rem;
        color: #6b7280;
        background: white;
        border: 1px solid #e5e7eb;
        padding: 4px 12px;
        border-radius: 20px;
    }
    .jurai-header .live-badge .dot {
        width: 6px; height: 6px;
        background: #22c55e;
        border-radius: 50%;
        animation: blink 2s ease-in-out infinite;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    /* ── DIVIDER ── */
    .divider {
        width: 60px;
        height: 2px;
        background: #4338ca;
        margin: 0 auto 2rem;
    }

    /* ── EXAMPLES ── */
    .section-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
    }
    div[data-testid="column"] .stButton > button {
        text-align: left;
        background: white;
        border: 1px solid #e5e7eb;
        color: #374151;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 0.88rem;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    div[data-testid="column"] .stButton > button:hover {
        border-color: #4338ca;
        color: #4338ca;
        box-shadow: 0 2px 8px rgba(67,56,202,0.1);
        transform: translateY(-1px);
    }

    /* ── SIDEBAR ── */
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

    /* ── CHAT ── */
    .stChatMessage { max-width: 800px; }
    [data-testid="stChatMessageContent"] {
        border: 1px solid #e5e7eb !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }

    /* ── BUTTONS ── */
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

    /* ── CHAT INPUT ── */
    [data-testid="stChatInput"] {
        border: 1px solid #e5e7eb !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    }
    [data-testid="stChatInput"] textarea {
        font-size: 0.95rem !important;
    }

    /* ── EXPANDER ── */
    [data-testid="stExpander"] {
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        background: white !important;
    }

    /* ── DISCLAIMER ── */
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

    /* ── FOOTER ── */
    .footer {
        text-align: center;
        font-size: 0.7rem;
        color: #9ca3af;
        padding: 1rem 0;
        border-top: 1px solid #e5e7eb;
        margin-top: 1rem;
    }

    /* ── HIDE STREAMLIT ── */
    #MainMenu, footer, header { visibility: hidden; }

    /* ── MOBILE ── */
    @media (max-width: 768px) {
        .jurai-header { padding: 2rem 0.5rem 1.5rem; }
        .jurai-header h1 { font-size: 1.8rem; }
        .main .block-container { padding: 0.5rem 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="jurai-header">
    <h1>Juris<span>AI</span></h1>
    <div class="tagline">Juristische Recherche für österreichisches Recht</div>
    <div class="live-badge"><div class="dot"></div>Verbunden mit RIS-Datenbank</div>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    if st.button("Neue Recherche", use_container_width=True, type="primary"):
        st.session_state.messages = []
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
        "<strong>Hinweis:</strong> KI-gestützte Recherche — keine Rechtsberatung. "
        "Alle Ergebnisse anhand der Originalquellen verifizieren."
        "</div>", unsafe_allow_html=True)
    st.markdown('<div class="footer">JurisAI &middot; Claude AI &middot; RIS OGD API</div>', unsafe_allow_html=True)

# --- Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("gesetz_sources"):
            with st.expander(f"Gesetze ({len(msg['gesetz_sources'])})"):
                for g in msg["gesetz_sources"]:
                    label = f"{g.get('kurztitel','')} {g.get('paragraph','')}"
                    url = g.get("url", "")
                    st.markdown(f"**[{label}]({url})**" if url else f"**{label}**")
        if msg.get("sources"):
            with st.expander(f"Rechtsprechung ({len(msg['sources'])})"):
                for s in msg["sources"]:
                    gz = s.get("geschaeftszahl", "")
                    url = s.get("url", "")
                    st.markdown(f"**{s.get('gericht','')} [{gz}]({url})**" if url else f"**{s.get('gericht','')} {gz}**")
                    if s.get("text_preview"): st.caption(s["text_preview"][:200] + "...")
        if msg["role"] == "assistant" and msg.get("content") and not msg["content"].startswith("Fehler"):
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Schriftsatz", key=f"b_{idx}", use_container_width=True):
                    st.session_state.generate_schriftsatz_from = msg["content"]
                    st.rerun()
            with c2:
                st.download_button("Export", generate_export_html(st.session_state.messages),
                    file_name="recherche.html", mime="text/html", key=f"e_{idx}", use_container_width=True)

# --- Welcome ---
if not st.session_state.messages:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-label">Strafrecht</div>', unsafe_allow_html=True)
        for ex in ["Was passiert bei Diebstahl?", "Verteidigung bei Körperverletzung?", "Wann bekommt man Diversion?", "Wann ist eine Tat verjährt?"]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex; st.rerun()
        st.markdown('<div class="section-label">Zivilrecht & Mietrecht</div>', unsafe_allow_html=True)
        for ex in ["Kündigungsfristen im Mietrecht?", "Schadenersatz — wann verjährt?", "Rechte als Mieter bei Mängeln?", "Unterlassungsklage einbringen?"]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex; st.rerun()
    with col2:
        st.markdown('<div class="section-label">Arbeitsrecht</div>', unsafe_allow_html=True)
        for ex in ["Kündigungsfristen für Angestellte?", "Wann ist Entlassung gerechtfertigt?", "Wie funktioniert Abfertigung Neu?", "Dienstverhinderung — Ansprüche?"]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex; st.rerun()
        st.markdown('<div class="section-label">Verwaltungsrecht</div>', unsafe_allow_html=True)
        for ex in ["Beschwerde gegen Bescheid?", "Rechte bei Polizei-Vernehmung?", "Fristen im Verwaltungsverfahren?", "Verwaltungsakt — wann nichtig?"]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex; st.rerun()

# --- Schriftsatz ---
if st.session_state.get("generate_schriftsatz_from"):
    research_text = st.session_state.pop("generate_schriftsatz_from")
    st.session_state.messages.append({"role": "user", "content": "Schriftsatz generieren"})
    with st.chat_message("user"): st.markdown("Schriftsatz generieren")
    with st.chat_message("assistant"):
        with st.spinner("Schriftsatz wird erstellt..."):
            try:
                from generation.schriftsatz import generate_schriftsatz
                result = generate_schriftsatz(research_text)
                st.markdown(result)
                st.session_state.messages.append({"role": "assistant", "content": result})
            except Exception as e:
                st.error(str(e)); st.session_state.messages.append({"role": "assistant", "content": f"Fehler: {e}"})

# --- Document Analysis ---
if st.session_state.get("analyze_document"):
    st.session_state.analyze_document = False
    file_data = st.session_state.pop("uploaded_file_data", None)
    file_name = st.session_state.pop("uploaded_file_name", "Dokument")
    if file_data:
        st.session_state.messages.append({"role": "user", "content": f"Analyse: {file_name}"})
        with st.chat_message("user"): st.markdown(f"Analyse: {file_name}")
        with st.chat_message("assistant"):
            with st.spinner("Dokument wird analysiert..."):
                try:
                    from generation.document_analyzer import extract_text_from_upload, analyze_document
                    class _P:
                        def __init__(s, d, n): s.name=n; s.size=len(d); s._data=d
                        def read(s): return s._data
                        def getvalue(s): return s._data
                    doc_text = extract_text_from_upload(_P(file_data, file_name))
                    if not doc_text.strip(): raise ValueError("Kein Text gefunden.")
                    response = analyze_document(doc_text, applikation or "Justiz", n_results)
                    st.markdown(response.answer)
                    sources_data = []
                    if response.sources:
                        with st.expander(f"Quellen ({len(response.sources)})"):
                            for s in response.sources:
                                gz = s.geschaeftszahl
                                st.markdown(f"**{s.gericht} [{gz}]({s.source_url})**" if s.source_url else f"**{s.gericht} {gz}**")
                                st.divider()
                                sources_data.append({"geschaeftszahl": gz, "gericht": s.gericht, "datum": s.datum, "url": s.source_url, "text_preview": s.text_preview[:300] if s.text_preview else ""})
                    st.session_state.messages.append({"role": "assistant", "content": response.answer, "sources": sources_data})
                except Exception as e:
                    st.error(str(e)); st.session_state.messages.append({"role": "assistant", "content": f"Fehler: {e}"})

# --- Chat Input ---
pending = st.session_state.pop("pending_question", None)
prompt = pending or st.chat_input("Rechtsfrage eingeben...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Durchsuche RIS..."):
            try:
                from generation.live_search import live_search_with_history
                history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                response = live_search_with_history(prompt, history, applikation or "Justiz", norm or "", n_results)
                st.markdown(response.answer)
                sources_data, gesetz_data = [], []
                if response.gesetz_sources:
                    with st.expander(f"Gesetze ({len(response.gesetz_sources)})", expanded=True):
                        for g in response.gesetz_sources:
                            label = f"{g.kurztitel} {g.paragraph}"
                            st.markdown(f"**[{label}]({g.source_url})**" if g.source_url else f"**{label}**")
                            if g.kundmachungsorgan: st.caption(g.kundmachungsorgan)
                            st.divider()
                            gesetz_data.append({"kurztitel": g.kurztitel, "paragraph": g.paragraph, "url": g.source_url})
                if response.sources:
                    with st.expander(f"Rechtsprechung ({len(response.sources)})", expanded=True):
                        for s in response.sources:
                            gz = s.geschaeftszahl
                            st.markdown(f"**{s.gericht} [{gz}]({s.source_url})**" if s.source_url else f"**{s.gericht} {gz}**")
                            if s.normen: st.caption(f"Normen: {', '.join(s.normen[:5])}")
                            st.divider()
                            sources_data.append({"geschaeftszahl": gz, "gericht": s.gericht, "datum": s.datum, "url": s.source_url, "text_preview": s.text_preview[:300] if s.text_preview else ""})
                st.session_state.messages.append({"role": "assistant", "content": response.answer, "sources": sources_data, "gesetz_sources": gesetz_data})
            except Exception as e:
                st.error(str(e)); st.session_state.messages.append({"role": "assistant", "content": f"Fehler: {e}"})
