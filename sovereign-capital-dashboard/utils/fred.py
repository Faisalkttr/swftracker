"""
FRED API wrapper with diagnostics, fallback series, and unit normalization.

Free API key: https://fred.stlouisfed.org/docs/api/api_key.html
Add to Streamlit Cloud Secrets as:  FRED_API_KEY = "your_key_here"
"""

import os
import requests
import pandas as pd
import streamlit as st

BASE = "https://api.stlouisfed.org/fred"

# Reference list of series used across the dashboard
SERIES = {
    "DGS10": "US 10Y Treasury Yield (%)",
    "DGS2": "US 2Y Treasury Yield (%)",
    "DGS30": "US 30Y Treasury Yield (%)",
    "WRESCRTREAS": "Foreign Official Custody: US Treasuries",
    "WTREGEN": "Foreign Holdings of US Treasuries",
    "FDHBFIN": "Foreign & International Monetary Authority Holdings",
    "WFRESTUS": "Foreign Official Assets: US Treasuries",
    "WALCL": "Fed Balance Sheet ($M)",
    "FEDFUNDS": "Effective Federal Funds Rate (%)",
    "TBUI": "Total Marketable Treasury Borrowing ($B)",
}


# ----------------------------------------------------------------------
# Key handling
# ----------------------------------------------------------------------
def _key() -> str:
    """Read FRED_API_KEY from Streamlit secrets first, then env vars."""
    key = ""
    try:
        key = st.secrets.get("FRED_API_KEY", "") or ""
    except Exception:
        pass
    if not key:
        key = os.environ.get("FRED_API_KEY", "")
    return key.strip()  # kills stray spaces/newlines from pasting


def fred_available() -> bool:
    return bool(_key())


# ----------------------------------------------------------------------
# Diagnostics
# ----------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def fred_status():
    """
    Probe FRED with DGS10 and return (ok: bool, message: str).
    Tells you exactly which failure mode you're in:
      - no key configured
      - key rejected by FRED
      - network error
    """
    key = _key()
    if not key:
        return False, "No FRED_API_KEY found in Streamlit secrets or environment."
    try:
        r = requests.get(f"{BASE}/series/observations",
                         params={"series_id": "DGS10",
                                 "api_key": key,
                                 "file_type": "json"},
                         timeout=15)
        try:
            data = r.json()
        except Exception:
            return False, f"FRED returned non-JSON (HTTP {r.status_code})."
        if r.status_code == 200 and "observations" in data:
            return True, (f"Key OK — FRED returned "
                          f"{len(data['observations'])} observations (probe: DGS10).")
        return False, (f"FRED rejected the request: "
                       f"{data.get('error_message', f'HTTP {r.status_code}')}")
    except Exception as e:
        return False, f"Could not reach FRED API: {e}"


# ----------------------------------------------------------------------
# Series metadata (units lookup — used to normalize millions vs billions)
# ----------------------------------------------------------------------
@st.cache_data(ttl=86400, show_spinner=False)
def fred_units(series_id: str) -> str:
    """Ask FRED what unit a series is reported in (e.g. 'Millions of Dollars')."""
    key = _key()
    if not key:
        return ""
    try:
        r = requests.get(f"{BASE}/series",
                         params={"series_id": series_id,
                                 "api_key": key,
                                 "file_type": "json"},
                         timeout=15)
        return r.json().get("seriess", [{}])[0].get("units", "")
    except Exception:
        return ""


def to_billions(value: float, series_id: str) -> float:
    """Normalize a raw FRED value to billions using its declared units."""
    if "million" in fred_units(series_id).lower():
        return value / 1_000          # millions → billions
    return value                      # assume already in billions


# ----------------------------------------------------------------------
# Data fetching
# ----------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fred_series(series_id: str, start: str = "2015-01-01"):
    """
    Fetch one FRED series as a DataFrame indexed by date with column 'value'.
    Returns None if key missing, request fails, or no observations.
    """
    key = _key()
    if not key:
        return None
    try:
        r = requests.get(f"{BASE}/series/observations",
                         params={"series_id": series_id,
                                 "api_key": key,
                                 "file_type": "json",
                                 "observation_start": start},
                         timeout=15)
        if r.status_code != 200:
            return None
        obs = r.json().get("observations", [])
        if not obs:
            return None
        df = pd.DataFrame(obs)[["date", "value"]]
        df = df[df.value != "."]              # "." = missing observation
        if df.empty:
            return None
        df["value"] = df["value"].astype(float)
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date").sort_index()
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fred_series_with_fallback(candidates: list, start: str = "2015-01-01"):
    """
    Try multiple series IDs in order; return (df, series_id_used).
    Returns (None, None) if every candidate fails.

    Usage:
        cust, used = fred_series_with_fallback(
            ["WRESCRTREAS", "WTREGEN", "FDHBFIN", "WFRESTUS"])
    """
    for sid in candidates:
        df = fred_series(sid, start)
        if df is not None and not df.empty:
            return df, sid
    return None, None
