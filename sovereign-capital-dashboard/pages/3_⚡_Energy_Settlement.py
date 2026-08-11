import streamlit as st, plotly.graph_objects as go
from utils.ui import page_config, quote, source_note
from utils.io import load_csv
from utils.market_data import history
page_config("Level 3 — Energy Settlement", "⚡")
st.title("⚡ Level 3 · Energy Settlement Currencies")
quote("Energy trade often drives monetary architecture. Follow the invoice currency.")

df = load_csv("energy_settlement.csv")
st.dataframe(df.sort_values("date", ascending=False), use_container_width=True, hide_index=True)

c1, c2 = st.columns(2)
with c1:
    mix = {"USD": 70, "CNY": 12, "EUR": 6, "INR": 4, "RUB": 3, "Other": 5}
    st.plotly_chart(go.Figure(go.Pie(labels=mix.keys(), values=mix.values(), hole=.55)),
                    use_container_width=True)
    source_note("Illustrative settlement mix estimate — replace with your own model / IEA-OPEC flow work.")
with c2:
    fig = go.Figure()
    for sym, label in [("CL=F", "WTI"), ("CNY=X", "USD/CNY"), ("INR=X", "USD/INR")]:
        d = history(sym, "2y")
        if d is not None:
            norm = d["Close"] / d["Close"].iloc[0] * 100
            fig.add_scatter(x=norm.index, y=norm.values, name=label)
    fig.update_layout(template="plotly_dark", title="Rebased (100) — oil vs importer currencies",
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=340)
    st.plotly_chart(fig, use_container_width=True)

st.sidebar.markdown("### Ask yourself")
st.sidebar.write("When oil is paid in dollars, yuan, rubles or local currencies — what does that imply for future reserve demand?")
source_note("Corridor statuses curated from trade ministry statements and press reporting; refresh monthly.")