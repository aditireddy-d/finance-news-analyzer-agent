"""
Forward-return evaluation.

This is the part of the project that actually proves (or disproves) whether
the multi-agent pipeline is worth anything. A signal is only useful if,
looking back, "bullish" calls were followed by the stock going up more often
than "bearish" calls -- and only interesting if it beats simple baselines.

Results here should be reported honestly, including when the system does
NOT beat the baseline -- that is itself a real, defensible finding, not a
failure to hide.
"""

import pandas as pd
from .schemas import Direction, EvalResult
from .technical_factors import get_price_history


def _price_on_or_after(hist: pd.DataFrame, target_date: pd.Timestamp) -> float | None:
    future = hist[hist.index >= target_date]
    if future.empty:
        return None
    return float(future["Close"].iloc[0])


def evaluate_signal(
    ticker: str,
    signal_date: pd.Timestamp,
    direction: Direction,
    confidence: float,
) -> EvalResult | None:
    """
    Given a past signal, look up what actually happened to the price
    5 and 20 trading days later, and score whether the direction was correct.
    """
    hist = get_price_history(ticker, period="1y")
    if hist.empty:
        return None

    hist = hist.tz_localize(None) if hist.index.tz is not None else hist
    signal_date = pd.Timestamp(signal_date).tz_localize(None)

    price_at_signal = _price_on_or_after(hist, signal_date)
    if price_at_signal is None:
        return None

    idx_after = hist.index[hist.index >= signal_date]
    if len(idx_after) < 2:
        return None

    price_5d = None
    price_20d = None
    positions = hist.index.get_indexer([idx_after[0]])
    start_pos = positions[0]
    if start_pos + 5 < len(hist):
        price_5d = float(hist["Close"].iloc[start_pos + 5])
    if start_pos + 20 < len(hist):
        price_20d = float(hist["Close"].iloc[start_pos + 20])

    return_5d = (price_5d / price_at_signal - 1) if price_5d else None
    return_20d = (price_20d / price_at_signal - 1) if price_20d else None

    def _direction_correct(ret: float | None) -> bool | None:
        if ret is None:
            return None
        if direction == Direction.BULLISH:
            return ret > 0
        if direction == Direction.BEARISH:
            return ret < 0
        return abs(ret) < 0.01  # "neutral" counted correct if roughly flat

    return EvalResult(
        ticker=ticker,
        signal_date=signal_date,
        direction=direction,
        confidence=confidence,
        price_at_signal=round(price_at_signal, 2),
        price_after_5d=round(price_5d, 2) if price_5d else None,
        price_after_20d=round(price_20d, 2) if price_20d else None,
        return_5d=round(return_5d, 4) if return_5d is not None else None,
        return_20d=round(return_20d, 4) if return_20d is not None else None,
        correct_5d=_direction_correct(return_5d),
        correct_20d=_direction_correct(return_20d),
    )


def summarize_eval_results(results: list[EvalResult]) -> dict:
    """Aggregate hit-rate stats across many evaluated signals."""
    valid_5d = [r for r in results if r.correct_5d is not None]
    valid_20d = [r for r in results if r.correct_20d is not None]

    return {
        "n_signals": len(results),
        "hit_rate_5d": round(sum(r.correct_5d for r in valid_5d) / len(valid_5d), 3) if valid_5d else None,
        "hit_rate_20d": round(sum(r.correct_20d for r in valid_20d) / len(valid_20d), 3) if valid_20d else None,
        "avg_return_5d": round(sum(r.return_5d for r in valid_5d if r.return_5d is not None) / len(valid_5d), 4) if valid_5d else None,
        "avg_return_20d": round(sum(r.return_20d for r in valid_20d if r.return_20d is not None) / len(valid_20d), 4) if valid_20d else None,
    }
