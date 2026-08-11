import streamlit as st
import yfinance as yf

LABELS = {
    "GC=F": "Gold", "SI=F": "Silver", "CL=F": "WTI Crude", "BZ=F": "Brent",
    "DX-Y.NYB": "DXY", "BTC-USD": "Bitcoin", "IBIT": "IBIT (BlackRock)",
    "CNY=X": "USD/CNY", "INR=X": "USD/INR", "RUB=X": "USD/RUB",
    "EURUSD=X": "EUR/USD", "JPY=X": "USD/JPY", "^TNX": "US 10Y (%)",
}

@st.cache_data(ttl=900, show_spinner=False)
def _history(symbol: str, period: str = "2y"):
    try:
        df = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=True)
        if df.empty:
            return None
        out = df[["Close"]].copy()
        if symbol == "^TNX":
            out["Close"] = out["Close"] / 10.0   # TNX is quoted x10
        return out
    except Exception:
        return None

def history(symbol: str, period: str = "2y"):
    return _history(symbol, period)

@st.cache_data(ttl=900, show_spinner=False)
def snapshot(symbols):
    """{symbol: {'label','price','chg_pct'}} — 1-day change."""
    out = {}
    for s in symbols:
        df = _history(s, period="1mo")
        if df is None or len(df) < 2:
            continue
        last, prev = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2])
        out[s] = {"label": LABELS.get(s, s), "price": last,
                  "chg_pct": (last / prev - 1) * 100}
    return out