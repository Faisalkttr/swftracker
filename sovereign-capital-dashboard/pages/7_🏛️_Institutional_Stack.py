import streamlit as st, plotly.graph_objects as go
from utils.ui import page_config, quote, source_note, GOLD
from utils.io import load_csv
from utils.market_data import history
page_config("Level 7 — Institutional Stack", "🏛️")
st.title("🏛️ Level 7 · Institutional Adoption Stack")
quote("Retail usually follows after the products are already built.")

df = load_csv("institutional_adoption.csv")
st.dataframe(df, use_container_width=True, hide_index=True)

c1, c2 = st.columns(2)
for c, sym, title in [(c1, "IBIT", "IBIT — BlackRock spot BTC ETF"), (c2, "BTC-USD", "Bitcoin")]:
    with c:
        d = history(sym, "max")
        if d is not None:
            fig = go.Figure(go.Scatter(x=d.index, y=d["Close"], line=dict(color=GOLD, width=2)))
            fig.update_layout(template="plotly_dark", height=320, title=title,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

st.sidebar.markdown("### Questions I ask")
for q in ["Are they offering custody?", "Are they launching ETFs?",
          "Are they building tokenisation infrastructure?", "Are they integrating stablecoins?"]:
    st.sidebar.write("•", q)
source_note("Adoption matrix: curated from 13F filings (SEC EDGAR), issuer announcements and annual reports — refresh monthly.")