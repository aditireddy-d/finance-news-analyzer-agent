"""
AI Theme Analysis: aggregates signals across every ticker in a sector to
give a sector-level read, instead of one ticker at a time. Reuses the
existing 7-agent pipeline per ticker -- this module just runs it across a
sector's tickers and summarizes the results.
"""

from collections import Counter
import pandas as pd

from .sectors import tickers_in_sector
from .graph_pipeline import run_full_pipeline


def analyze_theme(sector: str, mode: str = "heuristic", max_tickers: int = 8) -> dict:
    """
    Runs the full 7-agent pipeline for up to `max_tickers` in the given
    sector and aggregates the results. Capped by default since running
    the full pipeline (news fetch + scoring + agents) per ticker is not
    free in wall-clock time -- 8 tickers is a reasonable balance for an
    interactive UI button.
    """
    tickers = tickers_in_sector(sector)[:max_tickers]
    if not tickers:
        return {"sector": sector, "tickers_analyzed": [], "results": [], "summary": None}

    results = []
    for t in tickers:
        try:
            state = run_full_pipeline(t, mode=mode, use_multi_source=False, top_k=8)
            signal = state["signal"]
            results.append({
                "ticker": t,
                "direction": signal.direction.value,
                "confidence": signal.confidence,
                "abstained": signal.abstained,
                "catalyst": signal.catalyst,
            })
        except Exception as e:
            results.append({"ticker": t, "direction": "error", "confidence": 0.0, "abstained": True, "catalyst": str(e)})

    direction_counts = Counter(r["direction"] for r in results if not r["abstained"])
    dominant = direction_counts.most_common(1)[0][0] if direction_counts else "neutral"

    summary = {
        "dominant_direction": dominant,
        "bullish_count": direction_counts.get("bullish", 0),
        "bearish_count": direction_counts.get("bearish", 0),
        "neutral_count": direction_counts.get("neutral", 0),
        "abstained_count": sum(1 for r in results if r["abstained"]),
        "avg_confidence": round(
            sum(r["confidence"] for r in results if not r["abstained"]) /
            max(sum(1 for r in results if not r["abstained"]), 1), 3
        ),
    }

    return {"sector": sector, "tickers_analyzed": tickers, "results": results, "summary": summary}


def theme_results_to_df(theme_result: dict) -> pd.DataFrame:
    return pd.DataFrame(theme_result["results"])
