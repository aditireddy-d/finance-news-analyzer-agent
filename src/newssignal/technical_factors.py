"""
Pulls price history and computes a few simple technical signals.
Gives the Analyst agent context beyond just "the headline sounds positive" --
e.g. a bullish headline on a stock already up 30% this month reads
differently than the same headline after a big drop.
"""

import yfinance as yf
import pandas as pd


def get_price_history(ticker: str, period: str = "3mo") -> pd.DataFrame:
    return yf.Ticker(ticker).history(period=period)


def technical_snapshot(ticker: str) -> dict:
    """A small set of interpretable technical facts, not a black-box score."""
    hist = get_price_history(ticker, period="3mo")
    if hist.empty:
        return {"error": f"No price history for {ticker}"}

    last_close = hist["Close"].iloc[-1]
    change_1d = (last_close / hist["Close"].iloc[-2] - 1) * 100 if len(hist) > 1 else 0.0
    change_5d = (last_close / hist["Close"].iloc[-6] - 1) * 100 if len(hist) > 5 else 0.0
    change_1mo = (last_close / hist["Close"].iloc[0] - 1) * 100

    sma_20 = hist["Close"].rolling(20).mean().iloc[-1]
    above_sma_20 = bool(last_close > sma_20) if pd.notna(sma_20) else None

    volatility = hist["Close"].pct_change().std() * (252 ** 0.5)  # annualized

    return {
        "ticker": ticker,
        "last_close": round(float(last_close), 2),
        "change_1d_pct": round(float(change_1d), 2),
        "change_5d_pct": round(float(change_5d), 2),
        "change_1mo_pct": round(float(change_1mo), 2),
        "above_sma_20": above_sma_20,
        "annualized_volatility": round(float(volatility), 3) if pd.notna(volatility) else None,
    }
