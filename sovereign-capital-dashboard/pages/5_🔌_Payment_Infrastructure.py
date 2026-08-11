import streamlit as st, pandas as pd, plotly.graph_objects as go
from utils.ui import page_config, quote, source_note, GOLD
from utils.io import load_csv
page_config("Level 5 — Payment Infrastructure", "🔌")
st.title("🔌 Level 5 · Payment Infrastructure")
quote("The question isn't 'will they replace SWIFT?' — it's 'are parallel rails being built?' Infrastructure precedes volume.")

tab1, tab2, tab3 = st.tabs(["Rails", "RMB in SWIFT", "CBDC tracker"])

with tab1:
    st.dataframe(load_csv("payment_systems.csv"), use_container_width=True, hide_index=True)

with tab2:
    rmb = load_csv("swift_rmb_share.csv")
    rmb["month"] = pd.to_datetime(rmb["month"])
    fig = go.Figure(go.Scatter(x=rmb.month, y=rmb.rmb_share_pct, line=dict(color=GOLD, width=3),
                               fill="tozeroy", fillcolor="rgba(212,175,55,.15)"))
    fig.update_layout(template="plotly_dark", height=380, yaxis_title="% of SWIFT global payments",
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
    source_note("SWIFT RMB Tracker (monthly PDF, swift.com) — update monthly.")

with tab3:
    st.dataframe(load_csv("cbdc_tracker.csv"), use_container_width=True, hide_index=True)
    source_note("Cross-check vs Atlantic Council CBDC Tracker (atlanticcouncil.org/cbdctracker).")