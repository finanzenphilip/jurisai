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
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Professional CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Header */
    .main-header {
        padding: 1.2rem 0 1rem 0;
        border-bottom: 1px solid #e2e6ea;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .logo-icon {
        font-size: 2rem;
        line-height: 1;
    }
    .header-text h1 {
        color: #0f172a;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-text p {
        color: #64748b;
        font-size: 0.85rem;
        margin: 0.2rem 0 0 0;
        font-weight: 400;
    }
    .header-badge {
        display: inline-block;
        background: #dbeafe;
        color: #1e40af;
        font-size: 0.65rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 10px;
        margin-left: 8px;
        vertical-align: middle;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #0f172a;
        font-size: 0.9rem;
        font-weight: 600;
    }

    /* Chat messages */
    .stChatMessage { max-width: 900px; }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.85rem;
        transition: all 0.15s;
    }

    /* Example cards */
    .example-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.7rem 1rem;
        cursor: pointer;
        transition: all 0.15s;
        font-size: 0.88rem;
        color: #334155;
        line-height: 1.4;
    }
    .example-card:hover {
        background: #eff6ff;
        border-color: #3b82f6;
        color: #1e40af;
    }

    /* Example buttons */
    div[data-testid="column"] .stButton > button {
        text-align: left;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        color: #334155;
        padding: 0.65rem 1rem;
        border-radius: 10px;
        font-size: 0.88rem;
    }
    div[data-testid="column"] .stButton > button:hover {
        background-color: #eff6ff;
        border-color: #3b82f6;
        color: #1e40af;
    }

    /* Source cards */
    .source-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
    }
    .source-card .gz { color: #1e40af; font-weight: 600; }
    .source-card .meta { color: #64748b; font-size: 0.78rem; margin-top: 2px; }
    .source-card .preview { color: #475569; font-size: 0.8rem; margin-top: 6px; line-height: 1.4; }

    /* Disclaimer */
    .disclaimer {
        background-color: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.78rem;
        color: #92400e;
        margin-top: 1rem;
        line-height: 1.5;
    }

    /* Category headers */
    .category-header {
        color: #0f172a;
        font-weight: 600;
        font-size: 0.88rem;
        margin-bottom: 0.5rem;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid #e2e8f0;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Welcome section */
    .welcome-section {
        text-align: center;
        padding: 2rem 0 1.5rem 0;
    }
    .welcome-section h2 {
        color: #0f172a;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .welcome-section p {
        color: #64748b;
        font-size: 0.9rem;
    }

    /* Stats bar */
    .stats-bar {
        display: flex;
        justify-content: center;
        gap: 2rem;
        padding: 0.8rem 0;
        margin-bottom: 1.5rem;
    }
    .stats-bar .stat {
        text-align: center;
    }
    .stats-bar .stat-num {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e40af;
    }
    .stats-bar .stat-label {
        font-size: 0.7rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* New chat button */
    .new-chat-btn {
        background: #0f172a;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        font-size: 0.85rem;
        font-weight: 500;
        cursor: pointer;
        width: 100%;
        transition: all 0.15s;
    }
    .new-chat-btn:hover { background: #1e293b; }

    /* Powered by */
    .powered-by {
        text-align: center;
        font-size: 0.7rem;
        color: #94a3b8;
        padding: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="main-header">
    <div class="logo-icon">&#9878;&#65039;</div>
    <div class="header-text">
        <h1>JurisAI <span class="header-badge">BETA</span></h1>
        <p>Juristische Recherche &mdash; Gesetze, Rechtsprechung &amp; Analyse</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    # New chat button
    if st.button("Neue Recherche", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.markdown("### Suchfilter")

    gericht_options = ["Alle Gerichte"] + list(COURT_APPS.keys())
    selected_app = st.selectbox(
        "Gericht",
        gericht_options,
        format_func=lambda x: f"{x} — {COURT_APPS[x]}" if x in COURT_APPS else x,
        help="Wählen Sie ein spezifisches Gericht oder suchen Sie in allen.",
    )
    applikation = selected_app if selected_app != "Alle Gerichte" else None

    norm = st.text_input("Norm / Paragraph", placeholder="z.B. StGB §127", help="Optional: Suche auf bestimmte Normen einschränken")
    norm = norm if norm else None

    n_results = st.slider("Quellenanzahl", 2, 10, 5, help="Mehr Quellen = gründlichere Recherche, aber langsamer")

    st.divider()

    # --- Document Upload ---
    st.markdown("### Dokument-Analyse")
    uploaded_file = st.file_uploader(
        "PDF oder TXT hochladen",
        type=["pdf", "txt"],
        help="Anklageschriften, Strafanträge, Bescheide, Verträge — werden analysiert und rechtlich eingeordnet.",
    )
    if uploaded_file:
        st.success(f"{uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        if st.button("Analysieren", use_container_width=True):
            st.session_state.analyze_document = True
            st.session_state.uploaded_file_data = uploaded_file.getvalue()
            st.session_state.uploaded_file_name = uploaded_file.name
            st.rerun()

    st.divider()

    with st.expander("So funktioniert's", expanded=False):
        st.markdown("""
**1.** Frage eingeben — einfach oder komplex

**2.** RIS-Datenbank wird durchsucht (Gesetze + Urteile)

**3.** AI analysiert Quellen und fasst zusammen

**4.** Quellen direkt im RIS verifizieren

**5.** Optional: Schriftsatz generieren lassen
        """)

    st.markdown(
        '<div class="disclaimer">'
        "<strong>Hinweis:</strong> Dieses Tool dient der juristischen "
        "Recherche und stellt keine Rechtsberatung dar. Alle Angaben sind AI-gestützt "
        "und <strong>müssen anhand der Originalquellen verifiziert werden</strong>. "
        "Keine Haftung für Richtigkeit oder Vollständigkeit."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="powered-by">Powered by Claude AI + RIS OGD API</div>', unsafe_allow_html=True)

# --- Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("gesetz_sources"):
            with st.expander(f"Gesetze ({len(msg['gesetz_sources'])})", expanded=False):
                for g in msg["gesetz_sources"]:
                    label = f"{g.get('kurztitel', '')} {g.get('paragraph', '')}"
                    url = g.get("url", "")
                    link = f"[{label}]({url})" if url else label
                    st.markdown(f"**{link}**")
        if msg.get("sources"):
            with st.expander(f"Rechtsprechung ({len(msg['sources'])})", expanded=False):
                for s in msg["sources"]:
                    url = s.get("url", "")
                    gz = s.get("geschaeftszahl", "")
                    link = f"[{gz}]({url})" if url else gz
                    st.markdown(f"**{s.get('gericht', '')} {link}** — {s.get('datum', '')}")
                    if s.get("text_preview"):
                        st.caption(s["text_preview"][:200] + "...")
        # Action buttons
        if msg["role"] == "assistant" and msg.get("content") and not msg["content"].startswith("Fehler"):
            bcol1, bcol2, bcol3 = st.columns([1, 1, 1])
            with bcol1:
                if st.button("Schriftsatz", key=f"hist_brief_{idx}", use_container_width=True):
                    st.session_state.generate_schriftsatz_from = msg["content"]
                    st.rerun()
            with bcol2:
                export_html = generate_export_html(st.session_state.messages)
                st.download_button(
                    "Export HTML",
                    export_html,
                    file_name="recherche.html",
                    mime="text/html",
                    key=f"hist_export_{idx}",
                    use_container_width=True,
                )
            with bcol3:
                pass  # placeholder for future features

# Example questions if chat is empty
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-section">
        <h2>Stellen Sie eine Frage zum österreichischen Recht</h2>
        <p>JurisAI durchsucht das RIS (Bundesgesetze + Rechtsprechung) und analysiert die Ergebnisse.</p>
    </div>
    <div class="stats-bar">
        <div class="stat"><div class="stat-num">500K+</div><div class="stat-label">Gerichtsentscheidungen</div></div>
        <div class="stat"><div class="stat-num">Live</div><div class="stat-label">RIS-Datenbank</div></div>
        <div class="stat"><div class="stat-num">6</div><div class="stat-label">Rechtsgebiete</div></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="category-header">Strafrecht</div>', unsafe_allow_html=True)
        for ex in [
            "Was passiert bei Diebstahl in Österreich?",
            "Verteidigungsmöglichkeiten bei Körperverletzung?",
            "Was ist Diversion und wann bekommt man sie?",
            "Wann ist eine Tat verjährt?",
        ]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()

        st.markdown('<div class="category-header">Zivilrecht & Mietrecht</div>', unsafe_allow_html=True)
        for ex in [
            "Welche Kündigungsfristen gelten im Mietrecht?",
            "Wann verjähren Schadenersatzansprüche?",
            "Was sind meine Rechte als Mieter bei Mängeln?",
            "Wie funktioniert eine Klage auf Unterlassung?",
        ]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()

    with col2:
        st.markdown('<div class="category-header">Arbeitsrecht</div>', unsafe_allow_html=True)
        for ex in [
            "Welche Kündigungsfristen gelten für Angestellte?",
            "Wann ist eine Entlassung gerechtfertigt?",
            "Wie funktioniert Abfertigung Neu?",
            "Welche Ansprüche habe ich bei Dienstverhinderung?",
        ]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()

        st.markdown('<div class="category-header">Verwaltungsrecht</div>', unsafe_allow_html=True)
        for ex in [
            "Wie lege ich Beschwerde gegen einen Bescheid ein?",
            "Welche Rechte habe ich bei einer Polizei-Vernehmung?",
            "Welche Fristen gelten im Verwaltungsverfahren?",
            "Wann ist ein Verwaltungsakt nichtig?",
        ]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()

# --- Handle Schriftsatz Generation ---
if st.session_state.get("generate_schriftsatz_from"):
    research_text = st.session_state.pop("generate_schriftsatz_from")

    user_msg = "Schriftsatz generieren basierend auf der letzten Rechtsrecherche"
    st.session_state.messages.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    with st.chat_message("assistant"):
        with st.spinner("Schriftsatz wird erstellt..."):
            try:
                from generation.schriftsatz import generate_schriftsatz

                schriftsatz = generate_schriftsatz(research_text)
                st.markdown(schriftsatz)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": schriftsatz,
                })
            except Exception as e:
                import traceback
                error_msg = f"Fehler bei der Schriftsatz-Erstellung: {str(e)}"
                st.error(error_msg)
                st.code(traceback.format_exc())
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# --- Handle Document Analysis ---
if st.session_state.get("analyze_document"):
    st.session_state.analyze_document = False
    file_data = st.session_state.pop("uploaded_file_data", None)
    file_name = st.session_state.pop("uploaded_file_name", "Dokument")

    if file_data:
        user_msg = f"Dokument-Analyse: {file_name}"
        st.session_state.messages.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)

        with st.chat_message("assistant"):
            with st.spinner("Dokument wird analysiert — Gesetze & Rechtsprechung werden durchsucht..."):
                try:
                    from generation.document_analyzer import (
                        extract_text_from_upload,
                        analyze_document,
                    )

                    class _UploadedFileProxy:
                        def __init__(self, data: bytes, name: str):
                            self.name = name
                            self.size = len(data)
                            self._data = data
                        def read(self):
                            return self._data
                        def getvalue(self):
                            return self._data

                    proxy = _UploadedFileProxy(file_data, file_name)
                    doc_text = extract_text_from_upload(proxy)

                    if not doc_text.strip():
                        raise ValueError("Keine Textinhalte im Dokument gefunden.")

                    with st.expander("Extrahierter Text (Vorschau)"):
                        st.text(doc_text[:2000] + ("..." if len(doc_text) > 2000 else ""))

                    response = analyze_document(
                        document_text=doc_text,
                        applikation=applikation or "Justiz",
                        max_sources=n_results,
                    )

                    st.markdown(response.answer)

                    sources_data = []
                    if response.extracted_charges:
                        st.info(f"Erkannte Suchbegriffe: {response.extracted_charges}")

                    if response.sources:
                        with st.expander(f"Rechtsprechung ({len(response.sources)})"):
                            for s in response.sources:
                                gz = s.geschaeftszahl
                                if s.source_url:
                                    st.markdown(f"**{s.gericht} [{gz}]({s.source_url})** — {s.datum}")
                                else:
                                    st.markdown(f"**{s.gericht} {gz}** — {s.datum}")
                                if s.normen:
                                    st.caption(f"Normen: {', '.join(s.normen[:5])}")
                                if s.text_preview:
                                    st.caption(s.text_preview[:300] + "...")
                                st.divider()
                                sources_data.append({
                                    "geschaeftszahl": gz,
                                    "gericht": s.gericht,
                                    "datum": s.datum,
                                    "url": s.source_url,
                                    "text_preview": s.text_preview[:300] if s.text_preview else "",
                                })

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.answer,
                        "sources": sources_data,
                    })

                except Exception as e:
                    import traceback
                    error_msg = f"Fehler bei der Dokument-Analyse: {str(e)}"
                    st.error(error_msg)
                    st.code(traceback.format_exc())
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Handle pending question from example buttons
pending = st.session_state.pop("pending_question", None)
prompt = pending or st.chat_input("Rechtsfrage eingeben...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Durchsuche RIS-Datenbank — Gesetze & Rechtsprechung..."):
            try:
                from generation.live_search import live_search_with_history

                history = []
                for msg in st.session_state.messages[:-1]:
                    history.append({
                        "role": msg["role"],
                        "content": msg["content"],
                    })

                response = live_search_with_history(
                    question=prompt,
                    history=history,
                    applikation=applikation or "Justiz",
                    norm=norm or "",
                    max_sources=n_results,
                )

                st.markdown(response.answer)

                sources_data = []
                gesetz_data = []

                if response.gesetz_sources:
                    with st.expander(f"Gesetze ({len(response.gesetz_sources)})", expanded=True):
                        for g in response.gesetz_sources:
                            label = f"{g.kurztitel} {g.paragraph}"
                            if g.source_url:
                                st.markdown(f"**[{label}]({g.source_url})**")
                            else:
                                st.markdown(f"**{label}**")
                            if g.kundmachungsorgan:
                                st.caption(g.kundmachungsorgan)
                            st.divider()
                            gesetz_data.append({
                                "kurztitel": g.kurztitel,
                                "paragraph": g.paragraph,
                                "url": g.source_url,
                            })

                if response.sources:
                    with st.expander(f"Rechtsprechung ({len(response.sources)})", expanded=True):
                        if response.query_used:
                            st.caption(f"Suchbegriffe: {response.query_used}")
                        for s in response.sources:
                            gz = s.geschaeftszahl
                            if s.source_url:
                                st.markdown(f"**{s.gericht} [{gz}]({s.source_url})** — {s.datum}")
                            else:
                                st.markdown(f"**{s.gericht} {gz}** — {s.datum}")
                            if s.normen:
                                st.caption(f"Normen: {', '.join(s.normen[:5])}")
                            if s.text_preview:
                                st.caption(s.text_preview[:300] + "...")
                            st.divider()
                            sources_data.append({
                                "geschaeftszahl": gz,
                                "gericht": s.gericht,
                                "datum": s.datum,
                                "url": s.source_url,
                                "text_preview": s.text_preview[:300] if s.text_preview else "",
                            })

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.answer,
                    "sources": sources_data,
                    "gesetz_sources": gesetz_data,
                })

            except Exception as e:
                import traceback
                error_msg = f"Fehler: {str(e)}"
                st.error(error_msg)
                st.code(traceback.format_exc())
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
