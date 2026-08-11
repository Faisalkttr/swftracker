import streamlit as st, plotly.express as px
from utils.ui import page_config, quote, source_note
from utils.io import load_csv
page_config("Level 2 — Sovereign Wealth Funds", "🌐")
st.title("🌐 Level 2 · Sovereign Wealth Funds")
quote("Sovereign wealth funds think in decades. Retail normally notices years later.")

df = load_csv("swf_deals.csv")
funds = st.multiselect("Fund", sorted(df["fund"].unique()), default=sorted(df["fund"].unique()))
sectors = st.multiselect("Sector theme", sorted(df["sector"].unique()), default=[])
view = df[df["fund"].isin(funds)]
if sectors: view = view[view["sector"].isin(sectors)]

st.dataframe(view.sort_values("date", ascending=False), use_container_width=True, hide_index=True)

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(px.bar(view["sector"].value_counts().reset_index(), x="count", y="sector",
                           orientation="h", template="plotly_dark",
                           title="Deals by strategic theme"), use_container_width=True)
with c2:
    btc = view[view["btc_related"] == "Yes"]
    st.markdown("#### ₿ Bitcoin / digital-reserve exposure")
    if btc.empty:
        st.write("No tracked BTC-linked deals in current filter.")
    for _, r in btc.iterrows():
        st.markdown(f"- **{r['fund']}** — {r['target_or_theme']} ({r['date']})")

source_note("Sources: SEC EDGAR 13F filings, Global SWF, Sovereign Wealth Fund Institute, annual reports. Snapshot data — verify before use.")