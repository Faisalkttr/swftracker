import streamlit as st, pandas as pd, plotly.graph_objects as go, plotly.express as px
from utils.ui import page_config, quote, source_note, GOLD
from utils.io import load_csv
from utils.market_data import history
page_config("Level 4 — Gold Flows", "🥇")
st.title("🥇 Level 4 · Gold Flows Before Price")
quote("Many people watch the gold price. I watch who is buying.")

price = history("GC=F", "3y")
if price is not None:
    df = price.copy()
    df["MA50"] = df["Close"].rolling(50).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    fig = go.Figure()
    fig.add_scatter(x=df.index, y=df["Close"], name="Gold", line=dict(color=GOLD, width=2))
    fig.add_scatter(x=df.index, y=df["MA50"], name="50d", line=dict(width=1))
    fig.add_scatter(x=df.index, y=df["MA200"], name="200d", line=dict(width=1))
    fig.update_layout(template="plotly_dark", height=380, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", yaxis_title="USD/oz")
    st.plotly_chart(fig, use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    annual = load_csv("cb_gold_annual.csv")
    st.plotly_chart(px.bar(annual, x="year", y="tonnes", template="plotly_dark",
                           title="Central-bank net purchases (tonnes)",
                           color_discrete_sequence=[GOLD]), use_container_width=True)
with c2:
    buyers = load_csv("cb_gold_buyers.csv")
    year = st.selectbox("Year", sorted(buyers["year"].unique(), reverse=True))
    sub = buyers[buyers.year == year].sort_values("tonnes")
    st.plotly_chart(px.bar(sub, x="tonnes", y="country", orientation="h", template="plotly_dark",
                           title=f"Official buyers — {year}",
                           color_discrete_sequence=[GOLD]), use_container_width=True)

st.sidebar.markdown("### Questions I ask")
for q in ["Which countries are buying?", "Which are repatriating gold?", "Which are raising gold's reserve ratio?"]:
    st.sidebar.write("•", q)
source_note("Live price: Yahoo Finance (GC=F). Tonnage: World Gold Council 'Gold Demand Trends' — quarterly PDF, update data/ CSVs each release.")