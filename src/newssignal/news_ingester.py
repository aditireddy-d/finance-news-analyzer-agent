"""
Pulls raw news for a ticker. Starts with yfinance (free, no API key),
with room to add RSS feeds via feedparser later for more coverage.
"""

from datetime import datetime
import yfinance as yf
from .schemas import NewsItem


def fetch_news_yfinance(ticker: str, limit: int = 20) -> list[NewsItem]:
    """
    Pull recent news for a ticker using yfinance's built-in news feed.
    No API key required. Coverage is decent for large/liquid tickers.
    """
    stock = yf.Ticker(ticker)
    raw_items = stock.news or []

    items: list[NewsItem] = []
    for raw in raw_items[:limit]:
        # yfinance news items are nested under a "content" key in recent versions
        content = raw.get("content", raw)
        title = content.get("title", "")
        if not title:
            continue

        summary = content.get("summary", "") or content.get("description", "")
        provider = content.get("provider", {})
        source = provider.get("displayName", "Unknown") if isinstance(provider, dict) else "Unknown"

        pub_date = content.get("pubDate")
        published_at = None
        if pub_date:
            try:
                published_at = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                published_at = None

        url = ""
        click_through = content.get("clickThroughUrl") or content.get("canonicalUrl")
        if isinstance(click_through, dict):
            url = click_through.get("url", "")

        items.append(
            NewsItem(
                title=title,
                summary=summary,
                source=source,
                url=url,
                published_at=published_at,
                ticker=ticker,
            )
        )

    return items


def fetch_news_for_universe(tickers: list[str], limit_per_ticker: int = 20) -> dict[str, list[NewsItem]]:
    """Convenience wrapper to pull news for several tickers at once."""
    return {t: fetch_news_yfinance(t, limit_per_ticker) for t in tickers}
