# utils/io.py
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent      # repo root
DATA_DIR = ROOT / "data"

@st.cache_data(show_spinner=False)
def load_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        found = sorted(p.name for p in DATA_DIR.glob("*.csv")) if DATA_DIR.exists() else []
        raise FileNotFoundError(
            f"Missing dataset: {path}\n"
            f"Repo root resolved to: {ROOT}\n"
            f"CSVs present in data/: {found if found else 'NONE — the data/ folder is likely not committed to GitHub.'}"
        )
    return pd.read_csv(path)
