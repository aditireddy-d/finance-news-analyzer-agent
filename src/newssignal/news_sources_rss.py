"""
Google News RSS ingester. Free, no API key. Adds a second real source
on top of yfinance so evidence isn't coming from one feed only.
"""

from datetime import datetime, timezone
import feedparser
from .schemas import NewsItem

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}+stock&hl=en-US&gl=US&ceid=US:en"


def fetch_news_google_rss(ticker: str, company_name: str = "", limit: int = 15) -> list[NewsItem]:
    """
    Pull recent news for a ticker from Google News RSS. Using the company
    name (when available) in addition to the ticker meaningfully improves
    hit quality, since "AAPL" alone is a weaker search term than "AAPL Apple".
    """
    query = f"{ticker} {company_name}".strip().replace(" ", "+")
    feed = feedparser.parse(GOOGLE_NEWS_RSS.format(query=query))

    items: list[NewsItem] = []
    for entry in feed.entries[:limit]:
        published_at = None
        if getattr(entry, "published_parsed", None):
            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

        source = "Google News"
        if hasattr(entry, "source") and hasattr(entry.source, "title"):
            source = entry.source.title

        items.append(
            NewsItem(
                title=entry.title,
                summary=getattr(entry, "summary", ""),
                source=source,
                url=entry.link,
                published_at=published_at,
                ticker=ticker,
            )
        )
    return items


def fetch_multi_source_news(ticker: str, company_name: str = "", limit_per_source: int = 15) -> list[NewsItem]:
    """Combines yfinance + Google News RSS into one evidence pool."""
    from .news_ingester import fetch_news_yfinance

    yf_items = fetch_news_yfinance(ticker, limit=limit_per_source)
    google_items = fetch_news_google_rss(ticker, company_name, limit=limit_per_source)

    # De-duplicate by title (case-insensitive) since the same story often
    # shows up on both feeds.
    seen_titles = set()
    combined = []
    for item in yf_items + google_items:
        key = item.title.strip().lower()
        if key not in seen_titles:
            seen_titles.add(key)
            combined.append(item)

    return combined
