import streamlit as st

GOLD = "#D4AF37"

def page_config(title: str, icon: str):
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    css()

def css():
    st.markdown(f"""
    <style>
    div[data-testid="stMetric"] {{
        background: #14161c; border: 1px solid #262a33;
        border-radius: 12px; padding: 12px 14px;
    }}
    .quote {{
        border-left: 3px solid {GOLD}; padding: 8px 16px; margin: 8px 0 20px 0;
        color: #c9c9c9; font-style: italic; background: #101218;
        border-radius: 0 8px 8px 0;
    }}
    .src {{ color:#8a8f98; font-size:0.78rem; margin-top:6px; }}
    .chip {{ display:inline-block; padding:2px 10px; border-radius:999px;
        font-size:0.72rem; font-weight:700; letter-spacing:.04em; }}
    .chip-hot {{ background:#3a2a12; color:{GOLD}; border:1px solid {GOLD}; }}
    .chip-ok  {{ background:#12301f; color:#5ee08a; border:1px solid #2c6b46; }}
    .chip-neg {{ background:#331418; color:#ff7a7a; border:1px solid #7a2f36; }}
    </style>
    """, unsafe_allow_html=True)

def source_note(text: str):
    st.markdown(f"<div class='src'>📌 {text}</div>", unsafe_allow_html=True)

def quote(text: str):
    st.markdown(f"<div class='quote'>{text}</div>", unsafe_allow_html=True)