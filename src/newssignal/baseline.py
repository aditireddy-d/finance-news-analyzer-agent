"""
Simple baselines the multi-agent pipeline must beat to be worth anything.
Without this, there's no way to know if the fancy pipeline is actually
adding value or just producing confident-sounding noise.
"""

import random
from .schemas import Direction, NewsItem
from .agents import _heuristic_stance
from .schemas import ScoredEvidence


def random_baseline_signal() -> Direction:
    """The dumbest possible baseline: coin flip (with neutral as a 3rd option)."""
    return random.choice([Direction.BULLISH, Direction.BEARISH, Direction.NEUTRAL])


def keyword_sentiment_baseline(news_items: list[NewsItem]) -> Direction:
    """
    A simple baseline: just count bullish/bearish keywords across all
    headlines, no retrieval scoring, no credibility weighting, no
    skeptic pass. This is what most naive sentiment tools do.
    """
    if not news_items:
        return Direction.NEUTRAL

    bull = bear = 0
    for item in news_items:
        # Wrap in a throwaway ScoredEvidence just to reuse the stance logic
        stance = _heuristic_stance(
            ScoredEvidence(
                item=item, relevance_score=0, recency_score=0,
                credibility_score=0, combined_score=0,
            )
        )
        if stance == Direction.BULLISH:
            bull += 1
        elif stance == Direction.BEARISH:
            bear += 1

    if bull > bear:
        return Direction.BULLISH
    if bear > bull:
        return Direction.BEARISH
    return Direction.NEUTRAL
