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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Header */
    .main-header {
        padding: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #1a3a5c;
        margin-bottom: 1.5rem;
    }
    .main-header h1 {
        color: #1a3a5c;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #5a6c7d;
        font-size: 0.95rem;
        margin: 0.3rem 0 0 0;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f7f8fa;
        border-right: 1px solid #e2e6ea;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #1a3a5c;
        font-size: 1rem;
        font-weight: 600;
    }

    /* Chat messages */
    .stChatMessage { max-width: 900px; }

    /* Buttons */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.85rem;
        transition: all 0.15s;
    }

    /* Example buttons */
    div[data-testid="column"] .stButton > button {
        text-align: left;
        background-color: #f7f8fa;
        border: 1px solid #dde1e6;
        color: #1a3a5c;
        padding: 0.6rem 1rem;
    }
    div[data-testid="column"] .stButton > button:hover {
        background-color: #eef1f5;
        border-color: #1a3a5c;
    }

    /* Footer disclaimer */
    .disclaimer {
        background-color: #f7f8fa;
        border: 1px solid #e2e6ea;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        font-size: 0.8rem;
        color: #5a6c7d;
        margin-top: 1rem;
    }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Category headers */
    .category-header {
        color: #1a3a5c;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
        padding-bottom: 0.3rem;
        border-bottom: 1px solid #e2e6ea;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>JurisAI</h1>
    <p>Juristische Recherche für österreichisches Recht &mdash; Gesetze, Rechtsprechung & Verteidigungsstrategien</p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Sucheinstellungen")

    gericht_options = ["Alle Gerichte"] + list(COURT_APPS.keys())
    selected_app = st.selectbox(
        "Gericht",
        gericht_options,
        format_func=lambda x: f"{x} — {COURT_APPS[x]}" if x in COURT_APPS else x,
    )
    applikation = selected_app if selected_app != "Alle Gerichte" else None

    norm = st.text_input("Norm / Gesetz (optional)", placeholder="z.B. StGB §127")
    norm = norm if norm else None

    n_results = st.slider("Anzahl Quellen", 2, 10, 5)

    st.divider()

    # --- Document Upload ---
    st.markdown("### Dokument analysieren")
    uploaded_file = st.file_uploader(
        "Anklageschrift, Strafantrag oder Bescheid hochladen",
        type=["pdf", "txt"],
        help="Das Dokument wird analysiert und Verteidigungsoptionen werden aufgezeigt.",
    )
    if uploaded_file:
        st.success(f"{uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        if st.button("Dokument analysieren", use_container_width=True):
            st.session_state.analyze_document = True
            st.session_state.uploaded_file_data = uploaded_file.getvalue()
            st.session_state.uploaded_file_name = uploaded_file.name
            st.rerun()

    st.divider()

    st.markdown("### So funktioniert's")
    st.markdown("""
1. Frage stellen — einfach oder komplex
2. RIS wird durchsucht — Gesetze + Urteile
3. AI analysiert und fasst zusammen
4. Quellen direkt in RIS verifizieren
    """)

    st.divider()
    st.markdown(
        '<div class="disclaimer">'
        "<strong>Hinweis:</strong> Dieses Tool dient ausschliesslich der juristischen "
        "Recherche und stellt keine Rechtsberatung dar. Alle Angaben sind AI-gestützt "
        "und <strong>müssen anhand der Originalquellen im RIS verifiziert werden</strong>. "
        "Geschäftszahlen und Paragraphen können Fehler enthalten. "
        "Keine Haftung für Richtigkeit, Vollständigkeit oder Aktualität. "
        "Für verbindliche Auskünfte konsultieren Sie einen Rechtsanwalt."
        "</div>",
        unsafe_allow_html=True,
    )

# --- Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("gesetz_sources"):
            with st.expander(f"{len(msg['gesetz_sources'])} Gesetze anzeigen"):
                for g in msg["gesetz_sources"]:
                    label = f"{g.get('kurztitel', '')} {g.get('paragraph', '')}"
                    url = g.get("url", "")
                    link = f"[{label}]({url})" if url else label
                    st.markdown(f"**{link}**")
        if msg.get("sources"):
            with st.expander(f"{len(msg['sources'])} Gerichtsentscheidungen anzeigen"):
                for s in msg["sources"]:
                    url = s.get("url", "")
                    gz = s.get("geschaeftszahl", "")
                    link = f"[{gz}]({url})" if url else gz
                    st.markdown(f"**{s.get('gericht', '')} {link}** — {s.get('datum', '')}")
                    if s.get("text_preview"):
                        st.caption(s["text_preview"][:200] + "...")
        # Action buttons for assistant messages
        if msg["role"] == "assistant" and msg.get("content") and not msg["content"].startswith("Fehler"):
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                if st.button("Schriftsatz generieren", key=f"hist_brief_{idx}"):
                    st.session_state.generate_schriftsatz_from = msg["content"]
                    st.rerun()
            with bcol2:
                export_html = generate_export_html(st.session_state.messages)
                st.download_button(
                    "Recherche exportieren",
                    export_html,
                    file_name="recherche.html",
                    mime="text/html",
                    key=f"hist_export_{idx}",
                )

# Example questions if chat is empty
if not st.session_state.messages:
    st.markdown("#### Stellen Sie eine Frage zum österreichischen Recht")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="category-header">Strafrecht & Verteidigung</div>', unsafe_allow_html=True)
        examples_straf = [
            "Was passiert bei Diebstahl in Österreich?",
            "Verteidigungsmöglichkeiten bei Körperverletzung?",
            "Was ist Diversion und wann bekommt man sie?",
            "Wann ist eine Tat verjährt?",
        ]
        for ex in examples_straf:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()

        st.markdown('<div class="category-header">Zivilrecht & Mietrecht</div>', unsafe_allow_html=True)
        examples_zivil = [
            "Welche Kündigungsfristen gelten im Mietrecht?",
            "Wann verjähren Schadenersatzansprüche?",
            "Was sind meine Rechte als Mieter bei Mängeln?",
            "Wie funktioniert eine Klage auf Unterlassung?",
        ]
        for ex in examples_zivil:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()

    with col2:
        st.markdown('<div class="category-header">Arbeitsrecht & Sozialrecht</div>', unsafe_allow_html=True)
        examples_arbeit = [
            "Welche Kündigungsfristen gelten für Angestellte?",
            "Wann ist eine Entlassung gerechtfertigt?",
            "Wie funktioniert Abfertigung Neu?",
            "Welche Ansprüche habe ich bei Dienstverhinderung?",
        ]
        for ex in examples_arbeit:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()

        st.markdown('<div class="category-header">Verwaltungs- & Verfahrensrecht</div>', unsafe_allow_html=True)
        examples_verwaltung = [
            "Wie lege ich Beschwerde gegen einen Bescheid ein?",
            "Welche Rechte habe ich bei einer Polizei-Vernehmung?",
            "Welche Fristen gelten im Verwaltungsverfahren?",
            "Wann ist ein Verwaltungsakt nichtig?",
        ]
        for ex in examples_verwaltung:
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
            with st.spinner("Dokument wird analysiert (ca. 30-60 Sekunden)..."):
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
                        with st.expander(f"{len(response.sources)} Quellen aus RIS"):
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
prompt = pending or st.chat_input("Stellen Sie eine Frage zum österreichischen Recht...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Durchsuche Gesetze und Rechtsprechung..."):
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
                    with st.expander(f"{len(response.gesetz_sources)} Gesetze aus RIS"):
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
                    with st.expander(f"{len(response.sources)} Gerichtsentscheidungen aus RIS"):
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
