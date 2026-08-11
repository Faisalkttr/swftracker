import feedparser, streamlit as st, urllib.parse

QUERIES = {
    "Central Bank Reserves": "central bank foreign reserves dollar diversification",
    "Gold": "central bank gold purchases reserves",
    "Sovereign Wealth Funds": "sovereign wealth fund investment AI semiconductors",
    "Energy Settlement": "oil settlement yuan rubles BRICS currency",
    "Payment Rails": "BRICS payment system mBridge CIPS SWIFT alternative",
    "Bond Markets": "US Treasury issuance foreign holdings yields",
    "Institutional Bitcoin": "bank custody Bitcoin ETF tokenization",
}

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_news(topic: str, limit: int = 8):
    q = urllib.parse.quote(QUERIES.get(topic, topic))
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    try:
        feed = feedparser.parse(url)
        items = []
        for e in feed.entries[:limit]:
            items.append({"title": e.get("title", ""), "source": e.get("source", {}).get("title", ""),
                          "published": e.get("published", ""), "link": e.get("link", "")})
        return items
    except Exception:
        return []