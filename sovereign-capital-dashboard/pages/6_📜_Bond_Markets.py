import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.ui import page_config, quote, source_note
from utils.io import load_csv
from utils.fred import fred_series, fred_status, fred_series_with_fallback

page_config("Level 6 — Bond Markets", "📜")
st.title("📜 Level 6 · Sovereign Bond Markets")
quote("Governments reveal their stress through debt issuance. Money follows debt.")

# ----------------------------------------------------------------------
# FRED availability check with exact diagnostics
# ----------------------------------------------------------------------
ok, msg = fred_status()

if not ok:
    st.warning(f"FRED data unavailable: {msg}")
    st.info(
        "**Fix:** Manage app → Settings → Secrets, add exactly this TOML line, "
        "then **Restart app**:\n\n"
        '`FRED_API_KEY = "your_key_here"`\n\n'
        "Free key: https://fred.stlouisfed.org/docs/api/api_key.html"
    )
else:
    st.caption(f"✅ {msg}")

    col1, col2 = st.columns(2)

    # ------------------------------------------------------------------
    # Left: US Treasury yields + 10Y/2Y spread
    # ------------------------------------------------------------------
    with col1:
        st.subheader("US Treasury yields")
        d10 = fred_series("DGS10")
        d2 = fred_series("DGS2")

        if d10 is not None and d2 is not None:
            # Yield curves chart
            fig = go.Figure()
            fig.add_scatter(x=d10.index, y=d10["value"], name="10Y",
                            line=dict(color="#D4AF37", width=2))
            fig.add_scatter(x=d2.index, y=d2["value"], name="2Y",
                            line=dict(color="#5ee08a", width=1.5))
            fig.update_layout(template="plotly_dark", height=320,
                              yaxis_title="%",
                              paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fig, use_container_width=True)

            # Spread chart
            spread = pd.concat([d10["value"], d2["value"]], axis=1).dropna()
            spread.columns = ["y10", "y2"]
            spread["spread"] = spread["y10"] - spread["y2"]

            fig2 = go.Figure()
            fig2.add_scatter(x=spread.index, y=spread["spread"],
                             fill="tozeroy", fillcolor="rgba(212,175,55,0.15)",
                             line=dict(color="#D4AF37", width=1.5), name="10Y−2Y")
            fig2.add_hline(y=0, line_dash="dash", line_color="gray")
            fig2.update_layout(template="plotly_dark", height=280,
                               title="10Y − 2Y spread", yaxis_title="pp",
                               paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("Could not load Treasury yield data.")

    # ------------------------------------------------------------------
    # Right: Foreign official holdings of US Treasuries (with fallback)
    # ------------------------------------------------------------------
    with col2:
        st.subheader("Foreign holdings of US Treasuries")

        cust, used_series = fred_series_with_fallback([
            "WRESCRTREAS",   # original
            "WTREGEN",       # Foreign Holdings of US Treasuries
            "FDHBFIN",       # Foreign & International Monetary Authority Holdings
            "WFRESTUS",      # Foreign Official Assets
        ])

        if cust is not None and not cust.empty:
            # Auto-detect units (millions vs billions)
            val = cust["value"].iloc[-1]
            scale_label = "($B)"
            if val > 1e6:  # likely in millions
                cust_display = cust.copy()
                cust_display["value"] = cust_display["value"] / 1e6
            else:
                cust_display = cust

            fig3 = go.Figure()
            fig3.add_scatter(x=cust_display.index, y=cust_display["value"],
                             fill="tozeroy", fillcolor="rgba(212,175,55,0.1)",
                             line=dict(color="#D4AF37", width=2.5))
            fig3.update_layout(template="plotly_dark", height=320,
                               title=f"{used_series}",
                               yaxis_title=scale_label,
                               paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig3, use_container_width=True)

            latest_val = cust_display["value"].iloc[-1]
            prev_val = cust_display["value"].iloc[-2] if len(cust_display) > 1 else latest_val
            delta = latest_val - prev_val
            st.metric("Latest reading", f"${latest_val:,.0f}B", f"{delta:+,.0f}B vs prior")
        else:
            st.warning(
                "Foreign Treasury holdings series not available from FRED. "
                "This may be a temporary API issue or the series may have been retired."
            )

    st.divider()

    # ------------------------------------------------------------------
    # Fiscal stress map
    # ------------------------------------------------------------------
    st.subheader("Fiscal stress map")
    fiscal = load_csv("bonds_fiscal.csv")
    st.dataframe(fiscal, use_container_width=True, hide_index=True)

    st.divider()

    # ------------------------------------------------------------------
    # Watch questions
    # ------------------------------------------------------------------
    st.subheader("Questions I ask")
    cols = st.columns(3)
    with cols[0]:
        st.write("• Are foreign official holdings rising or falling?")
        st.write("• Is the 10Y−2Y curve inverted (recession signal)?")
    with cols[1]:
        st.write("• Which countries are issuing the most debt?")
        st.write("• Are bond yields rising faster than growth?")
    with cols[2]:
        st.write("• Is the Fed balance sheet expanding or contracting?")
        st.write("• Are emerging markets refinancing in USD or local currency?")

source_note(
    "Live: FRED API (Treasury yields, foreign holdings). "
    "Curated: bonds_fiscal.csv (IMF Fiscal Monitor) — update semi-annually."
)
