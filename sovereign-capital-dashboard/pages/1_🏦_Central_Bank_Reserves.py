import streamlit as st, pandas as pd, plotly.graph_objects as go
from utils.ui import page_config, quote, source_note, GOLD
from utils.io import load_csv
page_config("Level 1 — Central Bank Reserves", "🏦")
st.title("🏦 Level 1 · Central Bank Behaviour")
quote("Central banks tell you what they fear.")

cofer = load_csv("cofer_reserve_shares.csv")

c1, c2, c3, c4 = st.columns(4)
c1.metric("USD share (latest)", f"{cofer['USD'].iloc[-1]:.1f}%", f"{cofer['USD'].iloc[-1]-cofer['USD'].iloc[-2]:+.1f}pp")
c2.metric("USD share (2000)", f"{cofer['USD'].iloc[0]:.1f}%", f"{cofer['USD'].iloc[-1]-cofer['USD'].iloc[0]:.0f}pp since")
c3.metric("CNY share", f"{cofer['CNY'].iloc[-1]:.1f}%")
c4.metric("Gold ≈ share of reserves", "≈19%", "WGC 2024 est. — update quarterly")

tab1, tab2 = st.tabs(["Reserve composition", "USD decline"])
with tab1:
    fig = go.Figure()
    for cur in ["USD", "EUR", "JPY", "GBP", "CNY", "CAD", "AUD", "Other"]:
        fig.add_scatter(x=cofer.year, y=cofer[cur], name=cur, mode="lines",
                        line=dict(width=3 if cur in ("USD", "CNY") else 1.5))
    fig.update_layout(height=420, template="plotly_dark", yaxis_title="% of allocated reserves",
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    usd = cofer.set_index("year")["USD"]
    fig = go.Figure(go.Scatter(x=usd.index, y=usd.values, line=dict(color=GOLD, width=3)))
    fig.update_layout(height=380, template="plotly_dark", title="USD share of global reserves",
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

st.sidebar.markdown("### Questions I ask")
for q in ["Is gold rising as a share of reserves?", "Is the dollar share falling?",
          "Which countries are accumulating fastest?", "Are they buying gold, euros, yuan, or other assets?"]:
    st.sidebar.write("•", q)

source_note("IMF COFER (data.imf.org/COFER), updated quarterly. Values in this repo are a snapshot — verify against latest release.")