"""
Backtest runner: generates the comparison table for the Evaluation tab.

Unlike demo_data/eval_results_template.csv (which is an empty placeholder),
everything produced here comes from actually running the pipeline and
baselines against real historical news and real historical prices via
evaluation.evaluate_signal(). Nothing in this file invents numbers --
if you have zero valid signals, you get zero rows, not a fabricated
hit rate.
"""

from datetime import datetime, timezone
import pandas as pd

from .news_ingester import fetch_news_yfinance
from .rag_pipeline import score_evidence, top_evidence
from .technical_factors import technical_snapshot
from .agents import run_heuristic_pipeline
from .baseline import random_baseline_signal, keyword_sentiment_baseline
from .evaluation import evaluate_signal
from .schemas import Direction


def generate_signal_for_ticker_now(ticker: str) -> dict:
    """
    Generates all three signals (multi-agent, sentiment baseline, random
    baseline) for a ticker using CURRENT news. Useful for populating new
    rows to backtest once enough time has passed for forward returns to
    exist.
    """
    news_items = fetch_news_yfinance(ticker)
    scored = score_evidence(news_items, query=f"{ticker} stock")
    top = top_evidence(scored, k=8)
    technical = technical_snapshot(ticker)

    multi_agent_signal = run_heuristic_pipeline(ticker, top, technical)

    return {
        "ticker": ticker,
        "date": datetime.now(timezone.utc),
        "multi_agent_direction": multi_agent_signal.direction,
        "multi_agent_confidence": multi_agent_signal.confidence,
        "sentiment_baseline_direction": keyword_sentiment_baseline(news_items),
        "random_baseline_direction": random_baseline_signal(),
    }


def run_backtest(saved_signals: list[dict]) -> pd.DataFrame:
    """
    Takes a list of previously-saved signal dicts (from
    generate_signal_for_ticker_now, saved to disk with their date), and
    grades each one -- for the multi-agent pipeline AND both baselines --
    against what the price actually did afterward.

    saved_signals must be old enough that 5d/20d forward prices exist.
    """
    rows = []

    methods = {
        "Multi-Agent Heuristic": "multi_agent_direction",
        "Sentiment Baseline": "sentiment_baseline_direction",
        "Random Baseline": "random_baseline_direction",
    }

    for sig in saved_signals:
        ticker = sig["ticker"]
        signal_date = pd.Timestamp(sig["date"])

        for method_name, field in methods.items():
            direction = sig[field]
            if isinstance(direction, str):
                direction = Direction(direction)

            result = evaluate_signal(
                ticker=ticker,
                signal_date=signal_date,
                direction=direction,
                confidence=sig.get("multi_agent_confidence", 0.5),
            )
            if result is None:
                continue

            for horizon, correct_field, return_field in [
                ("5d", "correct_5d", "return_5d"),
                ("20d", "correct_20d", "return_20d"),
            ]:
                correct = getattr(result, correct_field)
                ret = getattr(result, return_field)
                if correct is None:
                    continue
                rows.append({
                    "method": method_name,
                    "horizon": horizon,
                    "ticker": ticker,
                    "correct": correct,
                    "return": ret,
                })

    if not rows:
        return pd.DataFrame(
            columns=["method", "horizon", "signals", "hit_rate", "avg_return", "signal_coverage"]
        )

    df = pd.DataFrame(rows)
    summary = (
        df.groupby(["method", "horizon"])
        .agg(signals=("correct", "count"), hit_rate=("correct", "mean"), avg_return=("return", "mean"))
        .reset_index()
    )
    summary["hit_rate"] = (summary["hit_rate"] * 100).round(1)
    summary["avg_return"] = (summary["avg_return"] * 100).round(2)
    return summary
