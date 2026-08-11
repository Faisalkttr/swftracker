import os, requests, pandas as pd, streamlit as st

URL = "https://api.stlouisfed.org/fred/series/observations"

SERIES = {
    "DGS10": "US 10Y Yield", "DGS2": "US 2Y Yield", "DGS30": "US 30Y Yield",
    "WRESCRTREAS": "Foreign Official Custody: US Treasuries ($B)",
    "WALCL": "Fed Balance Sheet ($M)", "FEDFUNDS": "Fed Funds Rate",
    "TBUI": "Total Marketable Treasury Borrowing ($B)",
}

def _key() -> str:
    key = ""
    try:
        key = st.secrets.get("FRED_API_KEY", "") or ""
    except Exception:
        pass
    if not key:
        key = os.environ.get("FRED_API_KEY", "")
    return key.strip()                      # kills stray spaces/newlines

def fred_available() -> bool:
    return bool(_key())

@st.cache_data(ttl=300, show_spinner=False)
def fred_status():
    """Probes FRED with DGS10 and returns (ok, message)."""
    key = _key()
    if not key:
        return False, "No FRED_API_KEY found in Streamlit secrets or environment."
    try:
        r = requests.get(URL, params={"series_id": "DGS10",
                                      "api_key": key,
                                      "file_type": "json"}, timeout=15)
        try:
            data = r.json()
        except Exception:
            return False, f"FRED returned non-JSON (HTTP {r.status_code})."
        if r.status_code == 200 and "observations" in data:
            return True, f"Key OK — FRED returned {len(data['observations'])} observations (probe: DGS10)."
        return False, f"FRED rejected the request: {data.get('error_message', f'HTTP {r.status_code}')}"
    except Exception as e:
        return False, f"Could not reach FRED API: {e}"

@st.cache_data(ttl=3600, show_spinner=False)
def fred_series(series_id: str, start: str = "2015-01-01"):
    key = _key()
    if not key:
        return None
    try:
        r = requests.get(URL, params={"series_id": series_id, "api_key": key,
                                      "file_type": "json",
                                      "observation_start": start}, timeout=15)
        if r.status_code != 200:
            return None
        obs = r.json().get("observations", [])
        if not obs:
            return None
        df = pd.DataFrame(obs)[["date", "value"]]
        df = df[df.value != "."]
        df["value"] = df["value"].astype(float)
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date").sort_index()
    except Exception:
        return None
