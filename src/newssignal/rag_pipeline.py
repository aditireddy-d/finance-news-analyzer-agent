"""
Evidence Selector: scores and ranks retrieved news for a ticker.

Deliberately lexical (BM25 + TF-IDF fallback) rather than embeddings/vector
DB -- this keeps the pipeline fast, free to run, and easy to explain in an
interview ("why BM25 over embeddings here?" has a real answer: headlines are
short, ticker/company names matter more than semantic similarity, and lexical
methods are cheap enough to rerun on every query with no vector store to
maintain).
"""

from datetime import datetime, timezone
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .schemas import NewsItem, ScoredEvidence

# A small, explicit credibility map. In a real system this would be a config
# file or a maintained table; keeping it inline here so the scoring logic
# is fully visible in one place.
SOURCE_CREDIBILITY = {
    "reuters": 1.0,
    "bloomberg": 1.0,
    "the wall street journal": 0.95,
    "cnbc": 0.85,
    "yahoo finance": 0.75,
    "motley fool": 0.55,
    "seeking alpha": 0.5,
}
DEFAULT_CREDIBILITY = 0.4

# yfinance's per-ticker news feed frequently returns loosely-tagged, generic
# market news (a PayPal article showing up under an NVDA query, etc.) --
# this was confirmed by testing on real tickers, not a hypothetical. A hard
# mention filter is a simple, honest fix: if the ticker or company name
# doesn't actually appear in the title/summary, it's dropped before scoring
# rather than just reranked lower.
TICKER_ALIASES = {
    "NVDA": ["nvda", "nvidia"],
    "AAPL": ["aapl", "apple"],
    "MSFT": ["msft", "microsoft"],
    "GOOGL": ["googl", "google", "alphabet"],
    "GOOG": ["goog", "google", "alphabet"],
    "AMZN": ["amzn", "amazon"],
    "META": ["meta", "facebook"],
    "TSLA": ["tsla", "tesla"],
    "AMD": ["amd"],
    "AVGO": ["avgo", "broadcom"],
    "NFLX": ["nflx", "netflix"],
    "COIN": ["coin", "coinbase"],
    "PLTR": ["pltr", "palantir"],
    "SMCI": ["smci", "super micro"],
}


def _mentions_ticker(item: NewsItem) -> bool:
    """True if the article's title/summary actually references this ticker or company."""
    aliases = TICKER_ALIASES.get(item.ticker.upper(), [item.ticker.lower()])
    text = f"{item.title} {item.summary}".lower()
    return any(alias in text for alias in aliases)


def filter_relevant(news_items: list[NewsItem]) -> list[NewsItem]:
    """Drops articles that don't actually mention the ticker/company at all."""
    return [item for item in news_items if _mentions_ticker(item)]


def _tokenize(text: str) -> list[str]:
    return text.lower().replace(",", " ").replace(".", " ").split()


def _credibility_for(source: str) -> float:
    return SOURCE_CREDIBILITY.get(source.strip().lower(), DEFAULT_CREDIBILITY)


def _recency_score(published_at, now=None) -> float:
    """Linear decay: full score at 0 days old, ~0 by 14 days old."""
    if published_at is None:
        return 0.3  # unknown recency -- don't reward, don't punish too hard
    now = now or datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age_days = max((now - published_at).total_seconds() / 86400, 0)
    return max(0.0, 1.0 - age_days / 14)


def score_evidence(
    news_items: list[NewsItem],
    query: str,
    weights: dict[str, float] | None = None,
    require_ticker_mention: bool = True,
) -> list[ScoredEvidence]:
    """
    Rank news items against a query (typically the ticker + company name)
    using BM25, falling back to TF-IDF cosine similarity if BM25 can't be
    built (e.g. too few documents), then blend in recency + credibility.

    If require_ticker_mention is True (default), articles that don't
    actually reference the ticker/company are dropped before scoring --
    this is what stops off-topic market news (a PayPal story under an
    NVDA query, etc.) from ranking highly just because it's recent and
    from a credible source.
    """
    if require_ticker_mention:
        news_items = filter_relevant(news_items)

    weights = weights or {"relevance": 0.5, "recency": 0.25, "credibility": 0.25}

    if not news_items:
        return []

    corpus = [f"{n.title} {n.summary}" for n in news_items]
    tokenized_corpus = [_tokenize(doc) for doc in corpus]
    tokenized_query = _tokenize(query)

    relevance_scores: list[float]
    try:
        bm25 = BM25Okapi(tokenized_corpus)
        raw_scores = bm25.get_scores(tokenized_query)
        max_score = max(raw_scores) if max(raw_scores) > 0 else 1.0
        relevance_scores = [s / max_score for s in raw_scores]
    except (ZeroDivisionError, ValueError):
        # Fallback: TF-IDF cosine similarity
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus + [query])
        sims = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
        relevance_scores = list(sims)

    scored: list[ScoredEvidence] = []
    for item, rel_score in zip(news_items, relevance_scores):
        recency = _recency_score(item.published_at)
        credibility = _credibility_for(item.source)
        combined = (
            weights["relevance"] * rel_score
            + weights["recency"] * recency
            + weights["credibility"] * credibility
        )
        scored.append(
            ScoredEvidence(
                item=item,
                relevance_score=round(float(rel_score), 3),
                recency_score=round(recency, 3),
                credibility_score=round(credibility, 3),
                combined_score=round(combined, 3),
            )
        )

    scored.sort(key=lambda e: e.combined_score, reverse=True)
    return scored


def top_evidence(scored: list[ScoredEvidence], k: int = 8) -> list[ScoredEvidence]:
    return scored[:k]
