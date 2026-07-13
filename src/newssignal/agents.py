"""
The reasoning agents. Two modes, same interface, matching the friend's
project's design:

  - "heuristic" mode: rule-based, zero cost, zero API key, runs anywhere.
    Good for demos and for generating the bulk of eval data cheaply.
  - "llm" mode: swaps the Analyst/Verifier logic for real LLM calls when
    an API key is available, for richer reasoning on individual tickers.

Both modes return the same Signal object, so the rest of the app (UI,
evaluator) never needs to know which mode produced a given signal.
"""

from datetime import datetime, timezone
from .schemas import Direction, ScoredEvidence, Signal, VerifierFlag

BULLISH_WORDS = {
    "beat", "beats", "surge", "soar", "record", "upgrade", "growth",
    "strong", "outperform", "rally", "raises", "expansion", "profit",
}
BEARISH_WORDS = {
    "miss", "misses", "plunge", "fall", "falls", "downgrade", "lawsuit",
    "recall", "layoffs", "investigation", "decline", "weak", "cut", "loss",
}


def _heuristic_stance(evidence: ScoredEvidence) -> Direction:
    text = f"{evidence.item.title} {evidence.item.summary}".lower()
    bull_hits = sum(1 for w in BULLISH_WORDS if w in text)
    bear_hits = sum(1 for w in BEARISH_WORDS if w in text)
    if bull_hits > bear_hits:
        return Direction.BULLISH
    if bear_hits > bull_hits:
        return Direction.BEARISH
    return Direction.NEUTRAL


def analyst_agent_heuristic(scored_evidence: list[ScoredEvidence]) -> list[ScoredEvidence]:
    """Assigns a stance to each piece of evidence using keyword heuristics."""
    for e in scored_evidence:
        e.stance = _heuristic_stance(e)
    return scored_evidence


def skeptic_agent_heuristic(
    scored_evidence: list[ScoredEvidence], technical: dict
) -> list[VerifierFlag]:
    """
    Looks for reasons to doubt the emerging conclusion. This is a rules-based
    stand-in for the LLM 'skeptical verifier' -- the goal is the same:
    actively hunt for disagreement rather than only confirming the majority view.
    """
    flags: list[VerifierFlag] = []

    stances = [e.stance for e in scored_evidence if e.stance]
    bullish_count = stances.count(Direction.BULLISH)
    bearish_count = stances.count(Direction.BEARISH)

    if bullish_count and bearish_count and min(bullish_count, bearish_count) / max(bullish_count, bearish_count) > 0.4:
        flags.append(
            VerifierFlag(
                concern="Evidence is split -- meaningful bullish AND bearish coverage exists.",
                severity="medium",
            )
        )

    low_cred = [e for e in scored_evidence if e.credibility_score < 0.5]
    if len(low_cred) > len(scored_evidence) / 2:
        flags.append(
            VerifierFlag(
                concern="Majority of retrieved evidence is from lower-credibility sources.",
                severity="medium",
            )
        )

    vol = technical.get("annualized_volatility")
    if vol and vol > 0.6:
        flags.append(
            VerifierFlag(
                concern=f"High annualized volatility ({vol}) -- signal confidence should be discounted.",
                severity="high",
            )
        )

    if len(scored_evidence) < 3:
        flags.append(
            VerifierFlag(
                concern="Fewer than 3 evidence items retrieved -- signal is based on thin evidence.",
                severity="high",
            )
        )

    return flags


def decision_agent_heuristic(
    ticker: str,
    scored_evidence: list[ScoredEvidence],
    verifier_flags: list[VerifierFlag],
    technical: dict,
    top_k: int = 8,
) -> Signal:
    """Combines everything into one final structured Signal."""
    top = scored_evidence[:top_k]
    supporting = [e for e in top if e.stance == Direction.BULLISH]
    challenging = [e for e in top if e.stance == Direction.BEARISH]

    # Abstain rather than force a call when evidence is too thin or too
    # uniformly low-credibility to trust. Citing "not enough to say" is a
    # legitimate output, not a failure -- forcing a confident-sounding
    # direction from bad evidence is worse than admitting uncertainty.
    high_severity_flags = [f for f in verifier_flags if f.severity == "high"]
    if len(top) < 2:
        return Signal(
            ticker=ticker, as_of=datetime.now(timezone.utc), direction=Direction.NEUTRAL,
            confidence=0.0, catalyst="Abstained -- insufficient evidence.",
            supporting_evidence=[], challenging_evidence=[], verifier_flags=verifier_flags,
            mode="heuristic", abstained=True,
            abstain_reason=f"Only {len(top)} evidence item(s) retrieved; too thin to call.",
        )
    if len(high_severity_flags) >= 2:
        return Signal(
            ticker=ticker, as_of=datetime.now(timezone.utc), direction=Direction.NEUTRAL,
            confidence=0.0, catalyst="Abstained -- multiple high-severity verifier concerns.",
            supporting_evidence=supporting, challenging_evidence=challenging,
            verifier_flags=verifier_flags, mode="heuristic", abstained=True,
            abstain_reason="; ".join(f.concern for f in high_severity_flags),
        )

    if len(supporting) > len(challenging):
        direction = Direction.BULLISH
    elif len(challenging) > len(supporting):
        direction = Direction.BEARISH
    else:
        direction = Direction.NEUTRAL

    # Base confidence on how lopsided the evidence is, discounted by how
    # much of the total evidence pool actually has a directional stance.
    # Without this second factor, 1 bearish item out of 8 mostly-neutral
    # items would score the same lopsidedness (100%) as 4 bearish vs 0
    # bullish out of 4 total -- but those are very different amounts of
    # actual signal. This was found by testing: a real run returned 90%
    # confidence off a single non-neutral article among 8 retrieved.
    total_directional = len(supporting) + len(challenging)
    total_evidence = len(top) or 1
    lean = abs(len(supporting) - len(challenging)) / max(total_directional, 1)
    coverage = total_directional / total_evidence  # what fraction of evidence actually took a side
    base_confidence = 0.4 + 0.5 * lean * coverage

    high_severity_flags = sum(1 for f in verifier_flags if f.severity == "high")
    medium_severity_flags = sum(1 for f in verifier_flags if f.severity == "medium")
    confidence = base_confidence - 0.15 * high_severity_flags - 0.07 * medium_severity_flags
    confidence = max(0.05, min(0.95, confidence))

    if direction == Direction.BULLISH and supporting:
        catalyst = supporting[0].item.title
    elif direction == Direction.BEARISH and challenging:
        catalyst = challenging[0].item.title
    else:
        catalyst = "No clear directional catalyst in retrieved evidence."

    return Signal(
        ticker=ticker,
        as_of=datetime.now(timezone.utc),
        direction=direction,
        confidence=round(confidence, 3),
        catalyst=catalyst,
        supporting_evidence=supporting,
        challenging_evidence=challenging,
        verifier_flags=verifier_flags,
        mode="heuristic",
    )


def run_heuristic_pipeline(
    ticker: str, scored_evidence: list[ScoredEvidence], technical: dict
) -> Signal:
    """Runs the full Analyst -> Skeptic -> Decision chain in heuristic mode."""
    scored_evidence = analyst_agent_heuristic(scored_evidence)
    flags = skeptic_agent_heuristic(scored_evidence, technical)
    return decision_agent_heuristic(ticker, scored_evidence, flags, technical)
