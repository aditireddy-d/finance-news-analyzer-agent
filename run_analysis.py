"""
CLI entry point: generate a signal for a single ticker.

Usage:
    python run_analysis.py --ticker NVDA --verbose
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from newssignal.news_ingester import fetch_news_yfinance
from newssignal.rag_pipeline import score_evidence, top_evidence
from newssignal.technical_factors import technical_snapshot
from newssignal.agents import run_heuristic_pipeline
from newssignal.graph_pipeline import run_full_pipeline


def main():
    parser = argparse.ArgumentParser(description="Generate a news-based signal for a ticker.")
    parser.add_argument("--ticker", required=True, help="Stock ticker, e.g. NVDA")
    parser.add_argument("--top-k", type=int, default=8, help="Number of evidence items to use")
    parser.add_argument(
        "--agents", choices=["3", "7"], default="7",
        help="'7' runs the full LangGraph pipeline (Retriever, Evidence Selector, "
             "Market Context, Analyst, Skeptical Verifier, Citation Auditor, Decision). "
             "'3' runs the simpler direct-call pipeline (Analyst, Skeptic, Decision)."
    )
    parser.add_argument(
        "--mode", choices=["heuristic", "llm"], default="heuristic",
        help="'llm' uses Groq (free, if GROQ_API_KEY is set) or OpenAI "
             "(if OPENAI_API_KEY is set) for the Analyst/Skeptic agents."
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    ticker = args.ticker.upper()

    if args.agents == "7":
        print(f"Running 7-agent LangGraph pipeline for {ticker} (mode={args.mode})...")
        state = run_full_pipeline(ticker, mode=args.mode, use_multi_source=True, top_k=args.top_k)
        signal = state["signal"]
        top = state["scored_evidence"]
        technical = state["technical"]
        print(f"  -> {len(state['raw_news'])} articles retrieved, {len(top)} kept after relevance filter + scoring")
        print(f"  -> Citation audit passed: {signal.citation_audit_passed}")
    else:
        print(f"Fetching news for {ticker}...")
        news_items = fetch_news_yfinance(ticker)
        print(f"  -> {len(news_items)} articles retrieved")
        print("Scoring evidence (BM25 + recency + credibility)...")
        scored = score_evidence(news_items, query=f"{ticker} stock")
        top = top_evidence(scored, k=args.top_k)
        print("Pulling technical/price context...")
        technical = technical_snapshot(ticker)
        print("Running agent pipeline (heuristic mode)...")
        signal = run_heuristic_pipeline(ticker, top, technical)

    print("\n=== SIGNAL ===")
    print(f"Ticker:     {signal.ticker}")
    print(f"Direction:  {signal.direction.value.upper()}")
    print(f"Confidence: {signal.confidence}")
    print(f"Catalyst:   {signal.catalyst}")
    print(f"\nSupporting evidence: {len(signal.supporting_evidence)}")
    print(f"Challenging evidence: {len(signal.challenging_evidence)}")
    print(f"\nVerifier flags ({len(signal.verifier_flags)}):")
    for f in signal.verifier_flags:
        print(f"  [{f.severity.upper()}] {f.concern}")

    if args.verbose:
        print("\n=== TOP EVIDENCE ===")
        for e in top:
            print(f"- ({e.stance}) [{e.combined_score}] {e.item.title}  <{e.item.source}>")
        print("\n=== TECHNICAL SNAPSHOT ===")
        for k, v in technical.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
