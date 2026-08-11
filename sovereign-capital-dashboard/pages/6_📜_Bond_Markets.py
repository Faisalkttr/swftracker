import streamlit as st, pandas as pd, plotly.graph_objects as go
from utils.ui import page_config, quote, source_note
from utils.io import load_csv
from utils.fred import fred_series, fred_available
page_config("Level 6 — Bond Markets", "📜")
st.title("📜 Level 6 · Sovereign Bond Markets")
quote("Governments reveal their stress through debt issuance. Money follows debt.")

if not fred_available():
    st.warning("Add your free FRED_API_KEY (Streamlit secrets) to unlock live Treasury & foreign-holdings data.")
else:
    d10, d2, cust = fred_series("DGS10"), fred_series("DGS2"), fred_series("WRESCRTREAS")
    if d10 is not None and d2 is not None:
        spread = pd.concat([d10["value"], d2["value"]], axis=1).dropna()
        spread.columns = ["y10", "y2"]
        spread["spread"] = spread["y10"] - spread["y2"]
        fig = go.Figure()
        fig.add_scatter(x=spread.index, y=spread["y10"], name="10Y")
        fig.add_scatter(x=spread.index, y=spread["y2"], name="2Y")
        fig.update_layout(template="plotly_dark", height=340, title="US Treasury yields (%)",
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    if cust is not None:
        fig = go.Figure(go.Scatter(x=cust.index, y=cust["value"], line=dict(color="#D4AF37", width=2.5)))
        fig.update_layout(template="plotly_dark", height=340,
                          title="Foreign official custody of US Treasuries ($B) — WRESCRTREAS",
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Fiscal stress map")
st.dataframe(load_csv("bonds_fiscal.csv"), use_container_width=True, hide_index=True)
source_note("Yields/holdings: FRED. Fiscal map: curated snapshot (IMF Fiscal Monitor) — update semi-annually.")