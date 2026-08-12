import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.ui import page_config, quote, source_note, GOLD
from utils.io import load_csv
from utils.market_data import snapshot
from utils.news import fetch_news, QUERIES
from utils.fred import fred_series, fred_status, fred_series_with_fallback, to_billions

page_config("Sovereign Capital Flow Dashboard", "🏛️")

st.title("🏛️ Sovereign Capital Flow Dashboard")
quote("Don't follow where money is. Follow where the largest pools of money are preparing to go next.")

# ----------------------------------------------------------------------
# Live ticker strip
# ----------------------------------------------------------------------
snaps = snapshot(["GC=F", "DX-Y.NYB", "BTC-USD", "CL=F", "CNY=X", "^TNX"])
if snaps:
    cols = st.columns(len(snaps))
    for c, (sym, d) in zip(cols, snaps.items()):
        c.metric(d["label"], f"{d['price']:,.2f}", f"{d['chg_pct']:+.2f}%")
else:
    st.info("Market data warming up… (yfinance)")

# ----------------------------------------------------------------------
# FRED status banner
# ----------------------------------------------------------------------
fred_ok, fred_msg = fred_status()
if fred_ok:
    st.caption(f"✅ {fred_msg}")
else:
    st.warning(f"FRED data offline — {fred_msg}")

# ----------------------------------------------------------------------
# Data freshness system
# ----------------------------------------------------------------------
try:
    log = load_csv("refresh_log.csv")
    log["updated_on"] = pd.to_datetime(log["updated_on"], errors="coerce")
    age_days = {r.dataset: (pd.Timestamp.now() - r.updated_on).days
                for _, r in log.iterrows() if pd.notna(r.updated_on)}
    as_of = dict(zip(log["dataset"], log["as_of"]))
    freshness_available = True
except Exception:
    freshness_available = False
    age_days, as_of = {}, {}

REFRESH_MAP = {
    "1": ["cofer_reserve_shares"],
    "2": ["cb_gold_annual", "cb_gold_buyers"],
    "3": ["swf_deals"],
    "4": ["energy_settlement"],
    "5": ["swift_rmb_share", "cbdc_tracker"],
    "6": None,                            # live FRED — always fresh
    "7": ["institutional_adoption"],
}

FRESH_DAYS, WARN_DAYS = 120, 270

def freshness_badge(level_num: str) -> str:
    ds = REFRESH_MAP.get(level_num)
    if ds is None:
        return ("<span style='font-size:.68rem;color:#5ee08a;white-space:nowrap'>"
                "● LIVE · FRED</span>")
    names = ds if isinstance(ds, list) else [ds]
    ages = [age_days.get(n, 9999) for n in names]
    worst = max(ages) if ages else 9999
    period = as_of.get(names[ages.index(worst)], "?") if ages else "?"
    if worst <= FRESH_DAYS:
        color = "#5ee08a"
    elif worst <= WARN_DAYS:
        color = "#e0b45e"
    else:
        color = "#ff7a7a"
    return (f"<span style='font-size:.68rem;color:{color};white-space:nowrap'>"
            f"● as of {period} · {worst}d old</span>")

if freshness_available:
    stale = sorted([(ds, d) for ds, d in age_days.items() if d > FRESH_DAYS],
                   key=lambda x: -x[1])
    if stale:
        st.warning("⚠️ Datasets past the 120-day refresh window: " +
                   ", ".join(f"{ds} ({d}d)" for ds, d in stale))

st.divider()

# ----------------------------------------------------------------------
# Load curated datasets
# ----------------------------------------------------------------------
cofer   = load_csv("cofer_reserve_shares.csv")
gold_y  = load_csv("cb_gold_annual.csv")
rmb     = load_csv("swift_rmb_share.csv")
cbdc    = load_csv("cbdc_tracker.csv")
energy  = load_csv("energy_settlement.csv")
swf     = load_csv("swf_deals.csv")
inst    = load_csv("institutional_adoption.csv")

usd_now, usd_prev = cofer["USD"].iloc[-1], cofer["USD"].iloc[-2]
gold_now           = gold_y["tonnes"].iloc[-1]
gold_avg           = gold_y["tonnes"].iloc[-5:].mean()
rmb_now, rmb_base  = rmb["rmb_share_pct"].iloc[-1], rmb["rmb_share_pct"].iloc[0]
cbdc_active        = cbdc[cbdc["stage"].str.contains("Live|Pilot|MVP|Preparation", na=False)].shape[0]
energy_active      = energy[energy["status"].str.contains("Active", na=False)].shape[0]

# Level 6 live value — fallback series + unit normalization
cust, used_series = fred_series_with_fallback(
    ["WRESCRTREAS", "WTREGEN", "FDHBFIN", "WFRESTUS"])
if cust is not None and not cust.empty:
    bond_value = f"${to_billions(float(cust['value'].iloc[-1]), used_series):,.0f}B"
else:
    bond_value = "key missing" if not fred_ok else "series unavailable"


def chip(kind: str, text: str) -> str:
    return f"<span class='chip chip-{kind}'>{text}</span>"


cards = [
    ("1", "🏦 Central Bank Reserves", "USD share of allocated reserves",
     f"{usd_now:.1f}% ({usd_now - usd_prev:+.1f}pp YoY)",
     chip("hot", "DIVERSIFYING") if usd_now < usd_prev else chip("ok", "STABLE")),
    ("2", "🥇 Central-Bank Gold Buying", "Net official purchases, latest year",
     f"{gold_now:,.0f}t (5y avg {gold_avg:,.0f}t)",
     chip("hot", "ACCUMULATING") if gold_now > 800 else chip("ok", "NORMAL")),
    ("3", "🌐 Sovereign Wealth Funds", "Tracked deals, 24 months",
     f"{len(swf)} deals · {(swf['btc_related'] == 'Yes').sum()} BTC-linked",
     chip("hot", "REPOSITIONING")),
    ("4", "⚡ Energy Settlement", "Active non-USD corridors",
     f"{energy_active} corridors",
     chip("hot", "EXPANDING") if energy_active >= 3 else chip("ok", "EARLY")),
    ("5", "🔌 Payment Rails", "RMB share of SWIFT payments",
     f"{rmb_now:.1f}% (from {rmb_base:.1f}%) · {cbdc_active} CBDCs active",
     chip("hot", "PARALLEL RAILS BUILDING")),
    ("6", "📜 Bond Markets", "Foreign official Treasury custody",
     bond_value,
     chip("neg", "FISCAL STRESS")),
    ("7", "🏛️ Institutional Stack", "Custody / ETF / tokenization",
     f"{inst['custody'].str.contains('Yes').sum()} custody · "
     f"{inst['btc_etf'].str.contains('ETF|FBTC|IBIT|EZBC|SPLG').sum()} ETF",
     chip("hot", "INFRA LIVE")),
]

for row in (cards[0:3], cards[3:7]):
    cols = st.columns(len(row))
    for c, (num, title, sub, value, chip_html) in zip(cols, row):
        with c:
            st.markdown(f"""
            <div style="background:#14161c;border:1px solid #262a33;border-radius:12px;
                        padding:16px;height:100%">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div style="color:#8a8f98;font-size:.75rem">LEVEL {num}</div>
                {freshness_badge(num) if freshness_available else ""}
              </div>
              <div style="font-size:1.05rem;font-weight:700">{title}</div>
              <div style="color:#8a8f98;font-size:.8rem;margin:6px 0">{sub}</div>
              <div style="font-size:1.15rem;font-weight:700;color:{GOLD}">{value}</div>
              <div style="margin-top:8px">{chip_html}</div>
            </div>""", unsafe_allow_html=True)

st.divider()

# ----------------------------------------------------------------------
# Composite Reserve Diversification Index
# ----------------------------------------------------------------------
def norm(x, lo, hi):
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))


rdi = round(100 * (
    0.25 * norm(gold_now, 200, 1100) +
    0.25 * norm(71 - usd_now, 0, 15) +
    0.15 * norm(rmb_now, 1.5, 5) +
    0.15 * norm(cbdc_active, 0, 12) +
    0.20 * norm(energy_active, 0, 6)
))

fig = go.Figure(go.Indicator(
    mode="gauge+number", value=rdi,
    title={"text": "Reserve Diversification Index (0 = full dollar hegemony · 100 = advanced multipolar rails)"},
    gauge={"axis": {"range": [0, 100]},
           "steps": [{"range": [0, 40], "color": "#1f2937"},
                     {"range": [40, 70], "color": "#3a2a12"},
                     {"range": [70, 100], "color": "#6b4d10"}],
           "bar": {"color": GOLD}},
    number={"suffix": ""}))
fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font_color="#E6E6E6")
st.plotly_chart(fig, use_container_width=True)
source_note("Composite of curated datasets below — weights documented in app.py. Refresh quarterly.")

st.divider()

# ----------------------------------------------------------------------
# Signal news wire
# ----------------------------------------------------------------------
st.subheader("📡 Signal wire")
tabs = st.tabs(list(QUERIES.keys()))
for t, topic in zip(tabs, QUERIES.keys()):
    with t:
        items = fetch_news(topic, 6)
        if not items:
            st.caption("No items fetched (feed may be rate-limited — try again shortly).")
        for item in items:
            st.markdown(f"**[{item['title']}]({item['link']})**")
            st.caption(f"{item['source']} · {item['published']}")

st.divider()

# ----------------------------------------------------------------------
# Data freshness log
# ----------------------------------------------------------------------
if freshness_available:
    st.subheader("🗓 Data freshness log")
    show = log.sort_values("updated_on", ascending=False).copy()
    show["days_since_update"] = show["dataset"].map(age_days)
    st.dataframe(show[["dataset", "as_of", "updated_on", "days_since_update", "source"]],
                 use_container_width=True, hide_index=True)

quote("The biggest clue is not what they say. It's what goes on the balance sheet.")
source_note("Educational research dashboard — not investment advice. Curated CSVs are snapshots; verify against official sources.")
