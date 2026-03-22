"""Streamlit web interface for RIS Legal AI."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from config import STREAMLIT_PAGE_TITLE, COURT_APPS

# Page config
st.set_page_config(
    page_title=STREAMLIT_PAGE_TITLE,
    page_icon="⚖️",
    layout="wide",
)

st.title("⚖️ RIS Legal AI")
st.caption("AI-gestützte Rechtsprechungsrecherche für österreichisches Recht")

# --- Sidebar: Filters & Settings ---
with st.sidebar:
    st.header("Einstellungen")

    # Mode selection
    search_mode = st.radio(
        "Suchmodus",
        ["Live-Suche (RIS API)", "Datenbank (vorindexiert)"],
        index=0,
        help="Live-Suche: Direkte RIS-Abfrage (kein Setup nötig)\n"
             "Datenbank: Vorindexierte Entscheidungen (schneller, braucht Ingestion)",
    )
    is_live = search_mode.startswith("Live")

    st.divider()
    st.header("🔍 Suchfilter")

    # Court filter
    gericht_options = ["Alle"] + list(COURT_APPS.keys())
    selected_app = st.selectbox(
        "Gericht / Applikation",
        gericht_options,
        format_func=lambda x: f"{x} — {COURT_APPS[x]}" if x in COURT_APPS else x,
        help="Filter nach Gerichtstyp",
    )
    applikation = selected_app if selected_app != "Alle" else None

    # Norm filter
    norm = st.text_input(
        "Norm / Gesetz",
        placeholder="z.B. StGB §127, ABGB §1295",
        help="Filter nach referenzierter Norm",
    )
    norm = norm if norm else None

    if is_live:
        n_results = st.slider("Anzahl Quellen", 2, 10, 5,
                              help="Mehr Quellen = langsamere aber bessere Antwort")
    else:
        # Database mode filters
        rechtsgebiet = st.text_input(
            "Rechtsgebiet",
            placeholder="z.B. Strafrecht, Zivilrecht",
        )
        rechtsgebiet = rechtsgebiet if rechtsgebiet else None

        st.subheader("Zeitraum")
        col1, col2 = st.columns(2)
        with col1:
            datum_von = st.text_input("Von", placeholder="2020-01-01")
        with col2:
            datum_bis = st.text_input("Bis", placeholder="2026-12-31")
        datum_von = datum_von if datum_von else None
        datum_bis = datum_bis if datum_bis else None

        n_results = st.slider("Anzahl Quellen", 3, 15, 8)

        st.divider()
        st.header("📊 Datenbank")
        try:
            from retrieval.vector_store import get_stats
            stats = get_stats()
            st.metric("Chunks in DB", stats["total_chunks"])
            if stats["courts"]:
                st.write("**Gerichte:**", ", ".join(stats["courts"][:10]))
        except Exception:
            st.info("Noch keine Daten. Starte Ingestion:\n```\npython ingestion/ingest_pipeline.py\n```")

    st.divider()
    st.caption(
        "⚖️ Dieses Tool dient ausschließlich der juristischen Recherche "
        "und stellt keine Rechtsberatung dar. Alle Angaben sind AI-gestützt "
        "und müssen anhand der Originalquellen verifiziert werden."
    )

# --- Main chat interface ---

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander(f"📚 {len(msg['sources'])} Quellen anzeigen"):
                for s in msg["sources"]:
                    url = s.get("url", "")
                    gz = s.get("geschaeftszahl", "")
                    link = f"[{gz}]({url})" if url else gz
                    st.markdown(f"- **{s.get('gericht', '')} {link}** ({s.get('datum', '')})")
                    if s.get("text_preview"):
                        st.caption(s["text_preview"][:200] + "...")

# Chat input
if prompt := st.chat_input("Stelle eine juristische Frage..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if is_live:
            # --- LIVE MODE: Direct RIS API search ---
            with st.spinner("🔍 Durchsuche RIS-Datenbank live..."):
                try:
                    from generation.live_search import live_search_and_answer

                    response = live_search_and_answer(
                        question=prompt,
                        applikation=applikation or "Justiz",
                        norm=norm or "",
                        max_sources=n_results,
                    )

                    st.markdown(response.answer)

                    sources_data = []
                    if response.sources:
                        with st.expander(f"📚 {len(response.sources)} Quellen aus RIS"):
                            st.caption(f"Suchbegriffe: *{response.query_used}*")
                            for s in response.sources:
                                if s.source_url:
                                    st.markdown(f"**{s.gericht} [{s.geschaeftszahl}]({s.source_url})** — {s.datum}")
                                else:
                                    st.markdown(f"**{s.gericht} {s.geschaeftszahl}** — {s.datum}")
                                if s.normen:
                                    st.caption(f"Normen: {', '.join(s.normen[:5])}")
                                if s.text_preview:
                                    st.caption(s.text_preview[:300] + "...")
                                st.divider()
                                sources_data.append({
                                    "geschaeftszahl": s.geschaeftszahl,
                                    "gericht": s.gericht,
                                    "datum": s.datum,
                                    "url": s.source_url,
                                    "text_preview": s.text_preview[:300],
                                })

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.answer,
                        "sources": sources_data,
                    })

                except Exception as e:
                    error_msg = f"Fehler: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

        else:
            # --- DATABASE MODE: Vector search ---
            with st.spinner("🔍 Durchsuche vorindexierte Rechtsprechung..."):
                try:
                    from generation.rag_chain import answer_legal_question

                    response = answer_legal_question(
                        question=prompt,
                        n_results=n_results,
                        applikation=applikation,
                        rechtsgebiet=rechtsgebiet,
                        datum_von=datum_von,
                        datum_bis=datum_bis,
                        norm=norm,
                    )

                    st.markdown(response.answer)

                    if response.hallucinated_citations:
                        st.warning(
                            f"⚠️ Möglicherweise halluzinierte Zitate: "
                            f"{', '.join(response.hallucinated_citations)}"
                        )

                    sources_data = []
                    if response.sources:
                        with st.expander(f"📚 {len(response.sources)} Quellen anzeigen"):
                            for s in response.sources:
                                if s.source_url:
                                    st.markdown(f"**{s.gericht} [{s.geschaeftszahl}]({s.source_url})** — {s.datum}")
                                else:
                                    st.markdown(f"**{s.gericht} {s.geschaeftszahl}** — {s.datum}")
                                st.caption(s.text[:300] + "..." if len(s.text) > 300 else s.text)
                                st.divider()
                                sources_data.append({
                                    "geschaeftszahl": s.geschaeftszahl,
                                    "gericht": s.gericht,
                                    "datum": s.datum,
                                    "url": s.source_url,
                                    "text_preview": s.text[:300],
                                })

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.answer,
                        "sources": sources_data,
                    })

                except Exception as e:
                    error_msg = f"Fehler: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# --- Example questions ---
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Beispielfragen:**")
    for ex in [
        "Welche Voraussetzungen hat Notwehr nach § 3 StGB?",
        "Schadenersatz bei Verkehrsunfällen — aktuelle Rechtsprechung?",
        "Mietminderung bei Lärmbelästigung?",
        "Betrug im Internet (§ 146 StGB) — Präzedenzfälle?",
    ]:
        st.caption(f"• {ex}")

with col2:
    st.markdown("**Tipps:**")
    st.caption("• Juristische Fachbegriffe verwenden")
    st.caption("• Relevante Paragraphen (§) nennen")
    st.caption("• Filter in der Sidebar nutzen")
    st.caption("• Quellen immer in RIS verifizieren")

with col3:
    st.markdown("**Links:**")
    st.caption("[RIS Rechtsinformationssystem](https://www.ris.bka.gv.at)")
    st.caption("[RIS Judikatur](https://www.ris.bka.gv.at/Judikatur/)")
    st.caption("[EUR-Lex](https://eur-lex.europa.eu)")
