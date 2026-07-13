"""
Market Scan: pulls a price/volume snapshot for ranking.

Two modes:
- scan_watchlist(): a small curated list, one ticker at a time (fine for ~30)
- scan_full_universe(): the larger NASDAQ-100 + S&P 500 major-constituents
  list (see tickers_universe.py), using batched yf.download calls instead
  of one request per ticker -- this is what makes scanning ~150 tickers
  actually practical on the free tier without hammering rate limits.
"""

import time
import yfinance as yf
import pandas as pd

from .tickers_universe import FULL_UNIVERSE

DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA",
    "AMD", "AVGO", "NFLX", "COIN", "PLTR", "SMCI", "CRM", "ORCL",
    "ADBE", "INTC", "QCOM", "TXN", "MU", "UBER", "SHOP", "SQ",
    "PYPL", "SNOW", "CRWD", "PANW", "NOW", "INTU", "BKNG", "COST",
]
# Note: this is a curated ~30-ticker universe, not the full NASDAQ-100 +
# S&P 500 (~600 tickers). A full-index scan is technically possible with
# free yfinance calls but becomes slow and rate-limit-prone at that scale --
# expanding this list further is a matter of adding tickers, not new code.


def scan_watchlist(tickers: list[str] | None = None, rank_by: str = "volume") -> pd.DataFrame:
    """
    Pull a 5-day snapshot for each ticker in the watchlist and rank by
    either trading volume or absolute price change -- mirroring the
    reference app's "Rank by: Trading Volume (absolute)" control.
    """
    tickers = tickers or DEFAULT_WATCHLIST
    rows = []

    for t in tickers:
        try:
            hist = yf.Ticker(t).history(period="5d")
            if hist.empty or len(hist) < 2:
                continue
            last_close = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2]
            change_pct = (last_close / prev_close - 1) * 100
            avg_volume = hist["Volume"].mean()

            rows.append({
                "ticker": t,
                "last_close": round(float(last_close), 2),
                "change_pct": round(float(change_pct), 2),
                "avg_volume_5d": int(avg_volume),
            })
        except Exception:
            continue

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    if rank_by == "volume":
        df = df.sort_values("avg_volume_5d", ascending=False)
    else:  # "price_change"
        df["abs_change"] = df["change_pct"].abs()
        df = df.sort_values("abs_change", ascending=False).drop(columns="abs_change")

    return df.reset_index(drop=True)


def scan_full_universe(
    rank_by: str = "volume", batch_size: int = 25, sleep_between_batches: float = 1.0
) -> pd.DataFrame:
    """
    Scans the larger ticker universe (~150 tickers, see tickers_universe.py)
    using batched yf.download calls -- one HTTP request per batch of
    `batch_size` tickers, not one request per ticker. This is what keeps a
    ~150-ticker scan practical on the free tier: 150 individual calls would
    be slow and likely to hit rate limits; ~6 batched calls is manageable.

    This is still NOT the same as a paid real-time full-market data feed --
    yfinance data can lag, and this is a snapshot, not a live stream.
    """
    rows = []
    tickers = FULL_UNIVERSE

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            data = yf.download(
                batch, period="5d", group_by="ticker", progress=False, threads=True
            )
        except Exception:
            continue

        for t in batch:
            try:
                if len(batch) == 1:
                    hist = data
                else:
                    hist = data[t]
                hist = hist.dropna(how="all")
                if hist.empty or len(hist) < 2:
                    continue
                last_close = hist["Close"].iloc[-1]
                prev_close = hist["Close"].iloc[-2]
                change_pct = (last_close / prev_close - 1) * 100
                avg_volume = hist["Volume"].mean()
                rows.append({
                    "ticker": t,
                    "last_close": round(float(last_close), 2),
                    "change_pct": round(float(change_pct), 2),
                    "avg_volume_5d": int(avg_volume) if pd.notna(avg_volume) else 0,
                })
            except Exception:
                continue

        if i + batch_size < len(tickers):
            time.sleep(sleep_between_batches)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    if rank_by == "volume":
        df = df.sort_values("avg_volume_5d", ascending=False)
    else:
        df["abs_change"] = df["change_pct"].abs()
        df = df.sort_values("abs_change", ascending=False).drop(columns="abs_change")

    return df.reset_index(drop=True)
