import pandas as pd
import streamlit as st

@st.cache_data(show_spinner=False)
def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(f"data/{name}")