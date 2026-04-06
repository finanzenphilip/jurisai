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
    initial_sidebar_state="collapsed",
)

# --- Premium CSS with Animations ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ═══ ANIMATIONS ═══ */
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
    }
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    @keyframes scaleIn {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }

    /* ═══ GLOBAL ═══ */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif !important;
    }
    .stApp {
        background: linear-gradient(135deg, #0a0f1c 0%, #0f1629 50%, #0a1628 100%);
    }
    .main .block-container {
        max-width: 900px;
        padding: 1rem 1.5rem;
    }

    /* ═══ HEADER ═══ */
    .hero-header {
        text-align: center;
        padding: 2rem 1rem 1.5rem;
        margin-bottom: 1.5rem;
        animation: fadeInUp 0.8s ease-out;
        position: relative;
    }
    .hero-header::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 10%;
        right: 10%;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99,102,241,0.4), transparent);
    }
    .hero-logo {
        width: 80px;
        height: 80px;
        margin-bottom: 0.5rem;
        animation: float 3s ease-in-out infinite;
        display: inline-block;
        filter: drop-shadow(0 0 15px rgba(99,102,241,0.3));
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #818cf8, #6366f1, #a78bfa);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 4s ease infinite;
        letter-spacing: -1px;
        margin: 0;
    }
    .hero-subtitle {
        color: #64748b;
        font-size: 0.9rem;
        margin-top: 0.4rem;
        font-weight: 400;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(99,102,241,0.15);
        color: #818cf8;
        font-size: 0.65rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 12px;
        border: 1px solid rgba(99,102,241,0.3);
        margin-top: 0.6rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    /* ═══ SIDEBAR ═══ */
    section[data-testid="stSidebar"] {
        background: rgba(15,22,41,0.98);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(99,102,241,0.15);
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #c7d2fe;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    section[data-testid="stSidebar"] label {
        color: #94a3b8 !important;
    }

    /* ═══ CHAT MESSAGES ═══ */
    .stChatMessage {
        max-width: 900px;
        animation: fadeIn 0.4s ease-out;
    }
    [data-testid="stChatMessageContent"] {
        background: rgba(30,41,69,0.6) !important;
        border: 1px solid rgba(99,102,241,0.12) !important;
        backdrop-filter: blur(10px);
        border-radius: 12px !important;
        color: #e2e8f0 !important;
    }
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] li,
    [data-testid="stChatMessageContent"] span {
        color: #e2e8f0 !important;
    }
    [data-testid="stChatMessageContent"] h1,
    [data-testid="stChatMessageContent"] h2,
    [data-testid="stChatMessageContent"] h3 {
        color: #c7d2fe !important;
    }
    [data-testid="stChatMessageContent"] strong {
        color: #a5b4fc !important;
    }
    [data-testid="stChatMessageContent"] code {
        background: rgba(99,102,241,0.15) !important;
        color: #c7d2fe !important;
    }
    [data-testid="stChatMessageContent"] a {
        color: #818cf8 !important;
    }

    /* ═══ BUTTONS ═══ */
    .stButton > button {
        border-radius: 10px;
        font-weight: 500;
        font-size: 0.85rem;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(99,102,241,0.2);
        background: rgba(30,41,69,0.5);
        color: #c7d2fe;
        backdrop-filter: blur(10px);
    }
    .stButton > button:hover {
        background: rgba(99,102,241,0.2);
        border-color: rgba(99,102,241,0.5);
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(99,102,241,0.15);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: white;
        border: none;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #818cf8, #6366f1);
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(99,102,241,0.3);
    }

    /* ═══ EXAMPLE CARDS ═══ */
    div[data-testid="column"] .stButton > button {
        text-align: left;
        background: rgba(30,41,69,0.4);
        border: 1px solid rgba(99,102,241,0.12);
        color: #94a3b8;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        font-size: 0.88rem;
        backdrop-filter: blur(10px);
    }
    div[data-testid="column"] .stButton > button:hover {
        background: rgba(99,102,241,0.12);
        border-color: rgba(99,102,241,0.4);
        color: #c7d2fe;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99,102,241,0.1);
    }

    /* ═══ CATEGORY HEADERS ═══ */
    .cat-header {
        color: #818cf8;
        font-weight: 600;
        font-size: 0.82rem;
        margin-bottom: 0.6rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid rgba(99,102,241,0.2);
        display: flex;
        align-items: center;
        gap: 6px;
        letter-spacing: 0.3px;
        animation: slideInLeft 0.6s ease-out;
    }

    /* ═══ WELCOME SECTION ═══ */
    .welcome {
        text-align: center;
        padding: 1.5rem 0 1rem;
        animation: fadeInUp 0.6s ease-out;
    }
    .welcome h2 {
        color: #e2e8f0;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .welcome p {
        color: #64748b;
        font-size: 0.88rem;
    }

    /* ═══ STATS BAR ═══ */
    .stats-row {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        padding: 1rem 0;
        margin-bottom: 1.5rem;
        animation: fadeInUp 0.8s ease-out 0.2s both;
    }
    .stat-card {
        text-align: center;
        padding: 0.8rem 1.2rem;
        background: rgba(30,41,69,0.4);
        border: 1px solid rgba(99,102,241,0.12);
        border-radius: 12px;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        min-width: 100px;
    }
    .stat-card:hover {
        border-color: rgba(99,102,241,0.3);
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(99,102,241,0.08);
    }
    .stat-num {
        font-size: 1.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #818cf8, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .stat-label {
        font-size: 0.65rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-top: 2px;
    }

    /* ═══ DISCLAIMER ═══ */
    .disclaimer {
        background: rgba(99,102,241,0.06);
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 1rem;
        line-height: 1.5;
    }
    .disclaimer strong { color: #818cf8; }

    /* ═══ EXPANDER ═══ */
    .streamlit-expanderHeader {
        background: rgba(30,41,69,0.4) !important;
        border-radius: 10px !important;
        color: #94a3b8 !important;
    }
    [data-testid="stExpander"] {
        border: 1px solid rgba(99,102,241,0.12) !important;
        border-radius: 10px !important;
        background: rgba(15,22,41,0.4) !important;
    }

    /* ═══ INPUTS ═══ */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    [data-testid="stChatInput"] textarea {
        background: rgba(30,41,69,0.6) !important;
        border: 1px solid rgba(99,102,241,0.2) !important;
        color: #e2e8f0 !important;
        border-radius: 10px !important;
    }
    .stTextInput > div > div > input:focus,
    [data-testid="stChatInput"] textarea:focus {
        border-color: rgba(99,102,241,0.5) !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.1) !important;
    }
    [data-testid="stChatInput"] {
        background: rgba(15,22,41,0.8) !important;
        border: 1px solid rgba(99,102,241,0.15) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px);
    }

    /* ═══ SLIDER ═══ */
    .stSlider > div > div > div > div {
        background: #6366f1 !important;
    }

    /* ═══ DIVIDER ═══ */
    hr { border-color: rgba(99,102,241,0.1) !important; }

    /* ═══ POWERED BY ═══ */
    .powered {
        text-align: center;
        font-size: 0.68rem;
        color: #475569;
        padding: 0.8rem 0;
        letter-spacing: 0.3px;
    }

    /* ═══ HIDE STREAMLIT ═══ */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* ═══ LIVE INDICATOR ═══ */
    .live-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #22c55e;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 2s ease-in-out infinite;
        box-shadow: 0 0 8px rgba(34,197,94,0.4);
    }

    /* ═══ MOBILE RESPONSIVE ═══ */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.8rem 1rem;
        }
        .hero-title { font-size: 1.5rem; }
        .hero-logo { font-size: 2.2rem; }
        .hero-subtitle { font-size: 0.8rem; }
        .stats-row {
            gap: 0.8rem;
            flex-wrap: wrap;
        }
        .stat-card {
            min-width: 80px;
            padding: 0.6rem 0.8rem;
        }
        .stat-num { font-size: 1rem; }
        .stChatMessage { max-width: 100%; }
        div[data-testid="column"] .stButton > button {
            font-size: 0.82rem;
            padding: 0.6rem 0.8rem;
        }
    }
    @media (max-width: 480px) {
        .hero-header { padding: 1.2rem 0.5rem 1rem; }
        .hero-title { font-size: 1.3rem; }
        .stats-row { gap: 0.5rem; }
        .stat-card { min-width: 70px; }
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="hero-header">
    <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA1MTIgNTEyIiBmaWxsPSJub25lIj4KICA8ZGVmcz4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0iZzEiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojODE4Y2Y4Ii8+CiAgICAgIDxzdG9wIG9mZnNldD0iNTAlIiBzdHlsZT0ic3RvcC1jb2xvcjojNjM2NmYxIi8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3R5bGU9InN0b3AtY29sb3I6IzRmNDZlNSIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0iZzIiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAlIiBzdHlsZT0ic3RvcC1jb2xvcjojYTViNGZjIi8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3R5bGU9InN0b3AtY29sb3I6IzgxOGNmOCIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KICAgIDxmaWx0ZXIgaWQ9Imdsb3ciPgogICAgICA8ZmVHYXVzc2lhbkJsdXIgc3RkRGV2aWF0aW9uPSIzIiByZXN1bHQ9ImJsdXIiLz4KICAgICAgPGZlTWVyZ2U+CiAgICAgICAgPGZlTWVyZ2VOb2RlIGluPSJibHVyIi8+CiAgICAgICAgPGZlTWVyZ2VOb2RlIGluPSJTb3VyY2VHcmFwaGljIi8+CiAgICAgIDwvZmVNZXJnZT4KICAgIDwvZmlsdGVyPgogIDwvZGVmcz4KCiAgPCEtLSBCYWNrZ3JvdW5kIGNpcmNsZSAtLT4KICA8Y2lyY2xlIGN4PSIyNTYiIGN5PSIyNTYiIHI9IjI0MCIgZmlsbD0iIzBmMTYyOSIgc3Ryb2tlPSJ1cmwoI2cxKSIgc3Ryb2tlLXdpZHRoPSIyIi8+CgogIDwhLS0gU2NhbGUgcGlsbGFyIC0tPgogIDxyZWN0IHg9IjI0OCIgeT0iMTQwIiB3aWR0aD0iMTYiIGhlaWdodD0iMjAwIiByeD0iOCIgZmlsbD0idXJsKCNnMSkiLz4KCiAgPCEtLSBCYXNlIC0tPgogIDxyZWN0IHg9IjE5NiIgeT0iMzMwIiB3aWR0aD0iMTIwIiBoZWlnaHQ9IjEyIiByeD0iNiIgZmlsbD0idXJsKCNnMSkiLz4KICA8cmVjdCB4PSIyMjAiIHk9IjM0MCIgd2lkdGg9IjcyIiBoZWlnaHQ9IjgiIHJ4PSI0IiBmaWxsPSJ1cmwoI2cyKSIgb3BhY2l0eT0iMC41Ii8+CgogIDwhLS0gQmFsYW5jZSBiZWFtIC0tPgogIDxyZWN0IHg9IjEyOCIgeT0iMTUyIiB3aWR0aD0iMjU2IiBoZWlnaHQ9IjgiIHJ4PSI0IiBmaWxsPSJ1cmwoI2cxKSIvPgoKICA8IS0tIEZ1bGNydW0gdHJpYW5nbGUgLS0+CiAgPHBvbHlnb24gcG9pbnRzPSIyNTYsMTI4IDI0NCwxNTIgMjY4LDE1MiIgZmlsbD0idXJsKCNnMikiLz4KCiAgPCEtLSBMZWZ0IHNjYWxlIHBhbiAtLT4KICA8bGluZSB4MT0iMTYwIiB5MT0iMTU2IiB4Mj0iMTYwIiB5Mj0iMjIwIiBzdHJva2U9InVybCgjZzIpIiBzdHJva2Utd2lkdGg9IjMiLz4KICA8cGF0aCBkPSJNIDEyMCAyMjAgUSAxNDAgMjQ0IDE2MCAyNDQgUSAxODAgMjQ0IDIwMCAyMjAiIHN0cm9rZT0idXJsKCNnMSkiIHN0cm9rZS13aWR0aD0iMyIgZmlsbD0icmdiYSg5OSwxMDIsMjQxLDAuMSkiLz4KICA8IS0tIExlZnQgcGFuIGNoYWlucyAtLT4KICA8bGluZSB4MT0iMTQwIiB5MT0iMTU2IiB4Mj0iMTI4IiB5Mj0iMjIwIiBzdHJva2U9InVybCgjZzIpIiBzdHJva2Utd2lkdGg9IjIiIG9wYWNpdHk9IjAuNiIvPgogIDxsaW5lIHgxPSIxODAiIHkxPSIxNTYiIHgyPSIxOTIiIHkyPSIyMjAiIHN0cm9rZT0idXJsKCNnMikiIHN0cm9rZS13aWR0aD0iMiIgb3BhY2l0eT0iMC42Ii8+CgogIDwhLS0gUmlnaHQgc2NhbGUgcGFuIC0tPgogIDxsaW5lIHgxPSIzNTIiIHkxPSIxNTYiIHgyPSIzNTIiIHkyPSIyMjAiIHN0cm9rZT0idXJsKCNnMikiIHN0cm9rZS13aWR0aD0iMyIvPgogIDxwYXRoIGQ9Ik0gMzEyIDIyMCBRIDMzMiAyNDQgMzUyIDI0NCBRIDM3MiAyNDQgMzkyIDIyMCIgc3Ryb2tlPSJ1cmwoI2cxKSIgc3Ryb2tlLXdpZHRoPSIzIiBmaWxsPSJyZ2JhKDk5LDEwMiwyNDEsMC4xKSIvPgogIDwhLS0gUmlnaHQgcGFuIGNoYWlucyAtLT4KICA8bGluZSB4MT0iMzMyIiB5MT0iMTU2IiB4Mj0iMzIwIiB5Mj0iMjIwIiBzdHJva2U9InVybCgjZzIpIiBzdHJva2Utd2lkdGg9IjIiIG9wYWNpdHk9IjAuNiIvPgogIDxsaW5lIHgxPSIzNzIiIHkxPSIxNTYiIHgyPSIzODQiIHkyPSIyMjAiIHN0cm9rZT0idXJsKCNnMikiIHN0cm9rZS13aWR0aD0iMiIgb3BhY2l0eT0iMC42Ii8+CgogIDwhLS0gQ2lyY3VpdC9EaWdpdGFsIGVsZW1lbnRzIC0tPgogIDwhLS0gTGVmdCBjaXJjdWl0IG5vZGVzIC0tPgogIDxjaXJjbGUgY3g9IjE0OCIgY3k9IjI4MCIgcj0iNCIgZmlsbD0iIzgxOGNmOCIgZmlsdGVyPSJ1cmwoI2dsb3cpIi8+CiAgPGNpcmNsZSBjeD0iMTI4IiBjeT0iMzAwIiByPSIzIiBmaWxsPSIjNjM2NmYxIiBvcGFjaXR5PSIwLjciLz4KICA8Y2lyY2xlIGN4PSIxNjgiIGN5PSIyOTYiIHI9IjMiIGZpbGw9IiM2MzY2ZjEiIG9wYWNpdHk9IjAuNyIvPgogIDxsaW5lIHgxPSIxNDgiIHkxPSIyODQiIHgyPSIxMjgiIHkyPSIyOTciIHN0cm9rZT0iIzYzNjZmMSIgc3Ryb2tlLXdpZHRoPSIxLjUiIG9wYWNpdHk9IjAuNCIvPgogIDxsaW5lIHgxPSIxNDgiIHkxPSIyODQiIHgyPSIxNjgiIHkyPSIyOTMiIHN0cm9rZT0iIzYzNjZmMSIgc3Ryb2tlLXdpZHRoPSIxLjUiIG9wYWNpdHk9IjAuNCIvPgoKICA8IS0tIFJpZ2h0IGNpcmN1aXQgbm9kZXMgLS0+CiAgPGNpcmNsZSBjeD0iMzY0IiBjeT0iMjgwIiByPSI0IiBmaWxsPSIjODE4Y2Y4IiBmaWx0ZXI9InVybCgjZ2xvdykiLz4KICA8Y2lyY2xlIGN4PSIzNDQiIGN5PSIzMDAiIHI9IjMiIGZpbGw9IiM2MzY2ZjEiIG9wYWNpdHk9IjAuNyIvPgogIDxjaXJjbGUgY3g9IjM4NCIgY3k9IjI5NiIgcj0iMyIgZmlsbD0iIzYzNjZmMSIgb3BhY2l0eT0iMC43Ii8+CiAgPGxpbmUgeDE9IjM2NCIgeTE9IjI4NCIgeDI9IjM0NCIgeTI9IjI5NyIgc3Ryb2tlPSIjNjM2NmYxIiBzdHJva2Utd2lkdGg9IjEuNSIgb3BhY2l0eT0iMC40Ii8+CiAgPGxpbmUgeDE9IjM2NCIgeTE9IjI4NCIgeDI9IjM4NCIgeTI9IjI5MyIgc3Ryb2tlPSIjNjM2NmYxIiBzdHJva2Utd2lkdGg9IjEuNSIgb3BhY2l0eT0iMC40Ii8+CgogIDwhLS0gQ2VudGVyIGNpcmN1aXQgLSBBSSBicmFpbiAtLT4KICA8Y2lyY2xlIGN4PSIyNTYiIGN5PSIzOTAiIHI9IjUiIGZpbGw9IiM4MThjZjgiIGZpbHRlcj0idXJsKCNnbG93KSIvPgogIDxjaXJjbGUgY3g9IjIzNiIgY3k9IjQwMCIgcj0iMyIgZmlsbD0iIzYzNjZmMSIgb3BhY2l0eT0iMC42Ii8+CiAgPGNpcmNsZSBjeD0iMjc2IiBjeT0iNDAwIiByPSIzIiBmaWxsPSIjNjM2NmYxIiBvcGFjaXR5PSIwLjYiLz4KICA8Y2lyY2xlIGN4PSIyNTYiIGN5PSI0MTIiIHI9IjMiIGZpbGw9IiM2MzY2ZjEiIG9wYWNpdHk9IjAuNSIvPgogIDxsaW5lIHgxPSIyNTYiIHkxPSIzOTUiIHgyPSIyMzYiIHkyPSIzOTciIHN0cm9rZT0iIzYzNjZmMSIgc3Ryb2tlLXdpZHRoPSIxIiBvcGFjaXR5PSIwLjQiLz4KICA8bGluZSB4MT0iMjU2IiB5MT0iMzk1IiB4Mj0iMjc2IiB5Mj0iMzk3IiBzdHJva2U9IiM2MzY2ZjEiIHN0cm9rZS13aWR0aD0iMSIgb3BhY2l0eT0iMC40Ii8+CiAgPGxpbmUgeDE9IjI1NiIgeTE9IjM5NSIgeDI9IjI1NiIgeTI9IjQwOSIgc3Ryb2tlPSIjNjM2NmYxIiBzdHJva2Utd2lkdGg9IjEiIG9wYWNpdHk9IjAuNCIvPgoKICA8IS0tIFN1YnRsZSBvcmJpdGFsIHJpbmdzIC0tPgogIDxlbGxpcHNlIGN4PSIyNTYiIGN5PSIyNTYiIHJ4PSIyMDAiIHJ5PSIzMCIgc3Ryb2tlPSIjNjM2NmYxIiBzdHJva2Utd2lkdGg9IjAuNSIgb3BhY2l0eT0iMC4xIiB0cmFuc2Zvcm09InJvdGF0ZSgtMjAgMjU2IDI1NikiLz4KICA8ZWxsaXBzZSBjeD0iMjU2IiBjeT0iMjU2IiByeD0iMTgwIiByeT0iMjUiIHN0cm9rZT0iIzgxOGNmOCIgc3Ryb2tlLXdpZHRoPSIwLjUiIG9wYWNpdHk9IjAuMDgiIHRyYW5zZm9ybT0icm90YXRlKDE1IDI1NiAyNTYpIi8+Cjwvc3ZnPgo=" class="hero-logo" alt="JurisAI Logo"/>
    <div class="hero-title">JurisAI</div>
    <div class="hero-subtitle">Juristische Recherche mit KI — Gesetze, Rechtsprechung &amp; Analyse</div>
    <div class="hero-badge"><span class="live-dot"></span>Live RIS-Datenbank</div>
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
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
    )
    applikation = selected_app if selected_app != "Alle Gerichte" else None

    norm = st.text_input("Norm / Paragraph", placeholder="z.B. StGB §127")
    norm = norm if norm else None

    n_results = st.slider("Quellenanzahl", 2, 10, 5)

    st.divider()
    st.markdown("### Dokument-Analyse")
    uploaded_file = st.file_uploader(
        "PDF oder TXT hochladen",
        type=["pdf", "txt"],
        help="Anklageschriften, Bescheide, Verträge analysieren",
    )
    if uploaded_file:
        st.success(f"{uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        if st.button("Analysieren", use_container_width=True):
            st.session_state.analyze_document = True
            st.session_state.uploaded_file_data = uploaded_file.getvalue()
            st.session_state.uploaded_file_name = uploaded_file.name
            st.rerun()

    st.divider()
    with st.expander("So funktioniert's"):
        st.markdown("""
**1.** Rechtsfrage eingeben

**2.** RIS-Datenbank wird durchsucht

**3.** KI analysiert Quellen

**4.** Quellen im RIS verifizieren
        """)

    st.markdown(
        '<div class="disclaimer">'
        "<strong>Hinweis:</strong> Dieses Tool dient der juristischen "
        "Recherche und stellt keine Rechtsberatung dar. Alle Angaben "
        "<strong>müssen anhand der Originalquellen verifiziert werden</strong>. "
        "Keine Haftung für Richtigkeit oder Vollständigkeit."
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="powered">Powered by Claude AI + RIS OGD API v2.6</div>', unsafe_allow_html=True)

# --- Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("gesetz_sources"):
            with st.expander(f"Gesetze ({len(msg['gesetz_sources'])})"):
                for g in msg["gesetz_sources"]:
                    label = f"{g.get('kurztitel', '')} {g.get('paragraph', '')}"
                    url = g.get("url", "")
                    link = f"[{label}]({url})" if url else label
                    st.markdown(f"**{link}**")
        if msg.get("sources"):
            with st.expander(f"Rechtsprechung ({len(msg['sources'])})"):
                for s in msg["sources"]:
                    url = s.get("url", "")
                    gz = s.get("geschaeftszahl", "")
                    link = f"[{gz}]({url})" if url else gz
                    st.markdown(f"**{s.get('gericht', '')} {link}** — {s.get('datum', '')}")
                    if s.get("text_preview"):
                        st.caption(s["text_preview"][:200] + "...")
        if msg["role"] == "assistant" and msg.get("content") and not msg["content"].startswith("Fehler"):
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                if st.button("Schriftsatz", key=f"b_{idx}", use_container_width=True):
                    st.session_state.generate_schriftsatz_from = msg["content"]
                    st.rerun()
            with bcol2:
                export_html = generate_export_html(st.session_state.messages)
                st.download_button("Export", export_html, file_name="recherche.html", mime="text/html", key=f"e_{idx}", use_container_width=True)

# --- Welcome Screen ---
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome">
        <h2>Stellen Sie eine Frage zum österreichischen Recht</h2>
        <p>JurisAI durchsucht das RIS live und analysiert Gesetze &amp; Rechtsprechung</p>
    </div>
    <div class="stats-row">
        <div class="stat-card"><div class="stat-num">500K+</div><div class="stat-label">Entscheidungen</div></div>
        <div class="stat-card"><div class="stat-num">Live</div><div class="stat-label">RIS-Anbindung</div></div>
        <div class="stat-card"><div class="stat-num">Opus</div><div class="stat-label">AI-Modell</div></div>
        <div class="stat-card"><div class="stat-num">6</div><div class="stat-label">Rechtsgebiete</div></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="cat-header">Strafrecht</div>', unsafe_allow_html=True)
        for ex in ["Was passiert bei Diebstahl?", "Verteidigung bei Körperverletzung?", "Wann bekommt man Diversion?", "Wann ist eine Tat verjährt?"]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()
        st.markdown('<div class="cat-header">Zivilrecht & Mietrecht</div>', unsafe_allow_html=True)
        for ex in ["Kündigungsfristen im Mietrecht?", "Wann verjähren Schadenersatzansprüche?", "Rechte als Mieter bei Mängeln?", "Klage auf Unterlassung?"]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()
    with col2:
        st.markdown('<div class="cat-header">Arbeitsrecht</div>', unsafe_allow_html=True)
        for ex in ["Kündigungsfristen für Angestellte?", "Wann ist Entlassung gerechtfertigt?", "Wie funktioniert Abfertigung Neu?", "Ansprüche bei Dienstverhinderung?"]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()
        st.markdown('<div class="cat-header">Verwaltungsrecht</div>', unsafe_allow_html=True)
        for ex in ["Beschwerde gegen Bescheid einlegen?", "Rechte bei Polizei-Vernehmung?", "Fristen im Verwaltungsverfahren?", "Wann ist ein Verwaltungsakt nichtig?"]:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state.pending_question = ex
                st.rerun()

# --- Schriftsatz ---
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
                st.session_state.messages.append({"role": "assistant", "content": schriftsatz})
            except Exception as e:
                import traceback
                st.error(f"Fehler: {e}")
                st.code(traceback.format_exc())
                st.session_state.messages.append({"role": "assistant", "content": f"Fehler: {e}"})

# --- Document Analysis ---
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
            with st.spinner("Dokument wird analysiert..."):
                try:
                    from generation.document_analyzer import extract_text_from_upload, analyze_document
                    class _Proxy:
                        def __init__(self, data, name):
                            self.name = name
                            self.size = len(data)
                            self._data = data
                        def read(self): return self._data
                        def getvalue(self): return self._data
                    doc_text = extract_text_from_upload(_Proxy(file_data, file_name))
                    if not doc_text.strip():
                        raise ValueError("Keine Textinhalte gefunden.")
                    with st.expander("Extrahierter Text"):
                        st.text(doc_text[:2000] + ("..." if len(doc_text) > 2000 else ""))
                    response = analyze_document(doc_text, applikation or "Justiz", n_results)
                    st.markdown(response.answer)
                    sources_data = []
                    if response.extracted_charges:
                        st.info(f"Suchbegriffe: {response.extracted_charges}")
                    if response.sources:
                        with st.expander(f"Rechtsprechung ({len(response.sources)})"):
                            for s in response.sources:
                                gz = s.geschaeftszahl
                                link = f"[{gz}]({s.source_url})" if s.source_url else gz
                                st.markdown(f"**{s.gericht} {link}** — {s.datum}")
                                if s.normen: st.caption(f"Normen: {', '.join(s.normen[:5])}")
                                if s.text_preview: st.caption(s.text_preview[:300] + "...")
                                st.divider()
                                sources_data.append({"geschaeftszahl": gz, "gericht": s.gericht, "datum": s.datum, "url": s.source_url, "text_preview": s.text_preview[:300] if s.text_preview else ""})
                    st.session_state.messages.append({"role": "assistant", "content": response.answer, "sources": sources_data})
                except Exception as e:
                    import traceback
                    st.error(f"Fehler: {e}")
                    st.code(traceback.format_exc())
                    st.session_state.messages.append({"role": "assistant", "content": f"Fehler: {e}"})

# --- Chat Input ---
pending = st.session_state.pop("pending_question", None)
prompt = pending or st.chat_input("Rechtsfrage eingeben...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Durchsuche RIS-Datenbank..."):
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
                        if response.query_used: st.caption(f"Suchbegriffe: {response.query_used}")
                        for s in response.sources:
                            gz = s.geschaeftszahl
                            link = f"[{gz}]({s.source_url})" if s.source_url else gz
                            st.markdown(f"**{s.gericht} {link}** — {s.datum}")
                            if s.normen: st.caption(f"Normen: {', '.join(s.normen[:5])}")
                            if s.text_preview: st.caption(s.text_preview[:300] + "...")
                            st.divider()
                            sources_data.append({"geschaeftszahl": gz, "gericht": s.gericht, "datum": s.datum, "url": s.source_url, "text_preview": s.text_preview[:300] if s.text_preview else ""})
                st.session_state.messages.append({"role": "assistant", "content": response.answer, "sources": sources_data, "gesetz_sources": gesetz_data})
            except Exception as e:
                import traceback
                st.error(f"Fehler: {e}")
                st.code(traceback.format_exc())
                st.session_state.messages.append({"role": "assistant", "content": f"Fehler: {e}"})
