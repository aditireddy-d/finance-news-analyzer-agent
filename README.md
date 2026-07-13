# Finance News Analyzer Agent

Multi-agent financial news analysis with retrieval grounding, source
credibility scoring, skeptical verification, and forward-return evaluation.

**This is an educational research project. It is not financial advice.**

*(Internally, the Python package is still named `newssignal` — renaming it
would mean touching imports across every file for no functional benefit,
so the package name and the project name differ. This is a normal thing to
mention if asked: "the repo is called Finance News Analyzer Agent, the
internal package is newssignal, an earlier working name.")*

## Why this exists

A positive headline doesn't automatically mean a stock will go up. Simple
sentiment scoring misses source credibility, recency, and counter-evidence.
This project tests a narrower question: can a small multi-agent pipeline
that explicitly retrieves evidence, scores it, and actively looks for
disagreement produce a more honest, defensible signal than a naive
keyword-sentiment approach — and does it actually beat that baseline when
checked against real forward returns?

## Architecture — 7-agent LangGraph pipeline

```
Ticker
  |
  v
1. Retriever            -- pulls news (yfinance + Google News RSS)
  |
  v
2. Evidence Selector     -- BM25/TF-IDF scoring + ticker-mention relevance filter
  |
  v
3. Market Context        -- price/technical snapshot (SMA, volatility, recent returns)
  |
  v
4. Analyst                -- assigns bullish/bearish/neutral stance per evidence item
  |          heuristic: keyword rules | llm: gpt-4o-mini classification
  v
5. Skeptical Verifier     -- flags thin evidence, split coverage, low credibility, high volatility
  |
  v
6. Citation Auditor       -- checks every piece of evidence used actually has a
  |                          real title + source (catches corrupted/fabricated
  |                          evidence before it reaches a decision)
  v
7. Decision                -- final direction + confidence + catalyst, or abstains
                              outright if evidence is too thin/contradictory
```

Implemented via LangGraph (`graph_pipeline.py`) as an actual `StateGraph` with
7 named nodes sharing one `PipelineState` object -- not just 7 function calls
glued together. Run it directly:

```bash
python run_analysis.py --ticker NVDA --agents 7 --verbose
```

A simpler 3-node version (Analyst, Skeptic, Decision via direct calls, no
LangGraph) is also kept in `agents.py` / `llm_agents.py` for comparison:

```bash
python run_analysis.py --ticker NVDA --agents 3 --verbose
```

Two execution modes, both implemented, both returning the same `Signal`
object so they're directly comparable:

| Mode      | Cost      | What it uses                                          |
|-----------|-----------|--------------------------------------------------------|
| heuristic | Free      | Keyword rules, no API key required                     |
| llm       | API calls | Real LLM reasoning via Groq (free) or OpenAI (paid)     |

**Two ways to activate LLM mode** (`llm_agents.py` checks Groq first, since
it's free):

```bash
# Free option -- no credit card needed, sign up at console.groq.com
export GROQ_API_KEY="gsk_..."

# OR paid option
export OPENAI_API_KEY="sk-..."
```

Groq uses Llama 3.3 70B via an OpenAI-compatible endpoint (same `openai`
Python client, just pointed at Groq's servers) -- this is a real
capability, not a fallback stub, and it's genuinely free with no billing
required, unlike OpenAI's API.

## Project structure

```
newssignal/
├── app.py                      # Streamlit dashboard
├── run_analysis.py             # CLI: single-ticker analysis
├── requirements.txt
├── demo_data/                  # sample data for evaluation runs
├── docs/                       # write-ups (retrieval method choice, eval results)
└── src/newssignal/
    ├── schemas.py               # Pydantic data models (the shared contract)
    ├── news_ingester.py         # News retrieval (yfinance)
    ├── news_sources_rss.py      # Second free source (Google News RSS) + merge/dedupe
    ├── rag_pipeline.py          # Evidence scoring (BM25/TF-IDF + recency + credibility)
    ├── technical_factors.py     # Price/technical context
    ├── sectors.py               # Ticker -> sector tagging for filtering
    ├── agents.py                # Analyst, Skeptic, Decision agents (heuristic mode) + abstain logic
    ├── llm_agents.py            # Same agents, real gpt-4o-mini reasoning (llm mode)
    ├── market_scan.py           # Watchlist scan (volume / price-change ranking)
    ├── baseline.py              # Random + keyword-sentiment baselines
    ├── evaluation.py            # Forward-return evaluation (single signal)
    ├── backtest.py              # Aggregates evaluation across saved signals + baselines
    └── signal_store.py          # Persists signals to disk for later backtesting
```

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Command line, single ticker:

```bash
python run_analysis.py --ticker NVDA --verbose
```

Interactive dashboard:

```bash
streamlit run app.py
```

## Evaluation methodology

The whole point of this project is not to trust the pipeline just because
it sounds sophisticated. `evaluation.py` takes a past signal (ticker,
date, direction) and checks it against what the stock price actually did
5 and 20 trading days later, then reports a hit rate. This is run against
both the multi-agent pipeline's own historical signals and the two
baselines in `baseline.py` (random guess, naive keyword sentiment) so any
claimed improvement is measured, not assumed.

**Results should be reported honestly, including cases where the pipeline
does not beat the baseline.** A negative or mixed result on a noisy,
efficient-market problem like short-horizon stock prediction is a
legitimate, defensible finding — not something to hide.

## Current limitations

- Market Scan covers a curated ~30-ticker watchlist, not the full
  NASDAQ-100 + S&P 500 (~600 tickers) — that scale needs a paid data
  feed or careful rate-limit handling to run reliably.
- News sources are yfinance + Google News RSS (both free). No
  Bloomberg/CNBC/Benzinga direct feed integration (Bloomberg specifically
  requires a paid B-PIPE subscription).
- Source credibility list is a small, manually maintained set — not
  learned or comprehensive.
- Evaluation only checks direction (up/down), not magnitude.
- LLM mode calls gpt-4o-mini per evidence batch — no caching yet, so
  repeated runs on the same ticker cost real API tokens each time.

## What's implemented (vs. still a stretch goal)

| Feature                                   | Status                          |
|--------------------------------------------|----------------------------------|
| 7-agent LangGraph pipeline                  | ✅ Implemented (tested end-to-end) |
| BM25/TF-IDF evidence retrieval + reranking | ✅ Implemented                   |
| Source credibility + recency scoring       | ✅ Implemented                   |
| Ticker/company relevance filter            | ✅ Implemented (fixed a real bug: off-topic articles were polluting evidence) |
| Heuristic agent mode (free)                 | ✅ Implemented                   |
| LLM agent mode (gpt-4o-mini)                | ✅ Implemented (needs API key)   |
| Citation Auditor agent                      | ✅ Implemented                   |
| Abstain-on-weak-evidence                    | ✅ Implemented                   |
| Multi-source news (yfinance + Google RSS)   | ✅ Implemented                   |
| Sector/theme tagging                        | ✅ Implemented                   |
| Forward-return backtest vs. baselines       | ✅ Implemented                   |
| Market scan (curated watchlist)             | ✅ Implemented                   |
| Citation card UI                            | ✅ Implemented                   |
| Confidence calibration (coverage-weighted)  | ✅ Implemented (fixed a real bug: 1 non-neutral article among 8 was producing 90% confidence) |
| Market Monitor tab                          | ✅ Implemented (tracks saved-signal tickers) |
| Sector filter dropdown                      | ✅ Implemented |
| AI Theme Analysis panel                     | ✅ Implemented (runs 7-agent pipeline across a sector's tickers) |
| Wider market scan (~501 real tickers, batched) | ✅ Implemented — real S&P 500 (487) + NASDAQ-100 (102) tickers sourced from slickcharts.com, not an approximation |
| Full *live* official membership feed          | ❌ This is a sourced snapshot as of the fetch date, not a continuously-updating official feed |
| Bloomberg B-PIPE integration                | ❌ Requires paid subscription    |

## Planned next steps

1. Add response caching for LLM mode so repeated runs don't re-spend tokens.
2. Migrate agent orchestration to LangGraph for clearer state management.
3. Expand the watchlist and add basic rate-limit-aware batching for a
   larger scan universe.
4. Build a real evaluation report once enough saved signals have aged
   past their 20-day window.
