"""
NewsSignal — Streamlit dashboard.

Run with: streamlit run app.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import pandas as pd
import plotly.express as px

from newssignal.news_ingester import fetch_news_yfinance
from newssignal.rag_pipeline import score_evidence, top_evidence
from newssignal.technical_factors import technical_snapshot
from newssignal.agents import run_heuristic_pipeline
from newssignal.baseline import random_baseline_signal, keyword_sentiment_baseline
from newssignal.backtest import run_backtest
from newssignal.signal_store import save_signal, load_signals
from newssignal.news_sources_rss import fetch_multi_source_news
from newssignal.llm_agents import run_llm_pipeline, llm_mode_available
from newssignal.graph_pipeline import run_full_pipeline
from newssignal.sectors import sector_for, all_sectors, tickers_in_sector
from newssignal.market_scan import scan_watchlist, scan_full_universe, DEFAULT_WATCHLIST
from newssignal.tickers_universe import universe_size
from newssignal.theme_analysis import analyze_theme, theme_results_to_df

st.set_page_config(page_title="Finance News Analyzer Agent", layout="wide")

st.markdown("""
<style>
    /* Overall app background */
    .stApp {
        background-color: #FFFFFF;
    }

    /* Main title styling */
    h1 {
        color: #1F2937;
        font-weight: 700;
    }
    h2, h3 {
        color: #1F2937;
        font-weight: 600;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #F5F7FA;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 14px 16px;
    }

    /* Buttons */
    .stButton > button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        padding: 0.5rem 1.2rem;
    }
    .stButton > button:hover {
        background-color: #1D4ED8;
        color: white;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #F5F7FA;
        border-radius: 8px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: #4B5563;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
        color: #2563EB !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    /* Containers / citation cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FAFAFA;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
    }

    /* Dataframes */
    div[data-testid="stDataFrame"] {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
    }

    /* Sidebar-style inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 1px solid #D1D5DB;
    }

    /* Caption text */
    .stCaption, small {
        color: #6B7280 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📰 Finance News Analyzer Agent — Multi-Agent Financial News Analysis")
st.caption("Educational / research project. Not investment advice. All results below come from real data — nothing is simulated or invented.")

tab_live, tab_scan, tab_monitor, tab_evidence, tab_eval = st.tabs(
    ["Live Analysis", "Market Scan", "Market Monitor", "Evidence Audit", "Evaluation"]
)

if "last_signal" not in st.session_state:
    st.session_state.last_signal = None
if "last_top_evidence" not in st.session_state:
    st.session_state.last_top_evidence = None
if "last_technical" not in st.session_state:
    st.session_state.last_technical = None


with tab_live:
    col_input, col_spacer = st.columns([1, 3])
    with col_input:
        ticker = st.text_input("Ticker", value="NVDA", key="live_ticker").upper()
        top_k = st.slider("Evidence items to use", 3, 15, 8, key="live_topk")
        use_multi_source = st.checkbox("Use multi-source news (yfinance + Google News RSS)", value=True)

        llm_ready = llm_mode_available()
        mode = st.radio(
            "Agent mode",
            ["Heuristic (free, no API key)", "LLM (Groq free tier or OpenAI)"],
            index=0,
            disabled=not llm_ready and False,
        )
        if mode.startswith("LLM") and not llm_ready:
            st.warning(
                "No LLM key set. Set GROQ_API_KEY (free, console.groq.com) "
                "or OPENAI_API_KEY (paid) in your environment."
            )

        use_langgraph = st.checkbox("Orchestrate via LangGraph (7-agent pipeline)", value=True)

        st.caption(f"Sector: {sector_for(ticker)}")
        run_clicked = st.button("Run Analysis", type="primary")

    if run_clicked:
        run_mode = "llm" if (mode.startswith("LLM") and llm_ready) else "heuristic"

        if use_langgraph:
            with st.spinner("Running 7-agent LangGraph pipeline (Retriever -> Evidence Selector -> Market Context -> Analyst -> Skeptical Verifier -> Citation Auditor -> Decision)..."):
                final_state = run_full_pipeline(
                    ticker, mode=run_mode, use_multi_source=use_multi_source, top_k=top_k
                )
            signal = final_state["signal"]
            top = final_state["scored_evidence"]
            technical = final_state["technical"]
            st.session_state.citation_audit_notes = final_state.get("citation_audit_notes", [])
        else:
            with st.spinner(f"Fetching news for {ticker}..."):
                if use_multi_source:
                    news_items = fetch_multi_source_news(ticker)
                else:
                    news_items = fetch_news_yfinance(ticker)

            if not news_items:
                st.error(f"No news found for {ticker}.")
                signal = top = technical = None
            else:
                with st.spinner("Scoring evidence and running agent pipeline..."):
                    scored = score_evidence(news_items, query=f"{ticker} stock")
                    top = top_evidence(scored, k=top_k)
                    technical = technical_snapshot(ticker)
                    if run_mode == "llm":
                        signal = run_llm_pipeline(ticker, top, technical)
                    else:
                        signal = run_heuristic_pipeline(ticker, top, technical)
                st.session_state.citation_audit_notes = []

        if signal is not None:
            st.session_state.last_signal = signal
            st.session_state.last_top_evidence = top
            st.session_state.last_technical = technical

    signal = st.session_state.last_signal
    top = st.session_state.last_top_evidence
    technical = st.session_state.last_technical

    if signal:
        if signal.abstained:
            st.info(f"🚫 **Abstained** — {signal.abstain_reason}")
        else:
            color = {"bullish": "green", "bearish": "red", "neutral": "gray"}[signal.direction.value]
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"### Direction: :{color}[{signal.direction.value.upper()}]")
            c2.metric("Confidence", f"{signal.confidence:.0%}")
            c3.metric("Evidence items used", len(top))
            st.caption(f"Mode: {signal.mode}")

        st.markdown(f"**Catalyst:** {signal.catalyst}")

        audit_notes = st.session_state.get("citation_audit_notes", [])
        if signal.citation_audit_passed:
            st.caption("✅ Citation audit passed — all evidence traces to real retrieved articles.")
        else:
            st.error("❌ Citation audit failed: " + "; ".join(audit_notes))

        if signal.verifier_flags:
            st.warning("**Skeptical Verifier flags:**")
            for f in signal.verifier_flags:
                st.write(f"- [{f.severity.upper()}] {f.concern}")
        else:
            st.success("No verifier concerns raised.")

        if st.button("Save this signal for later backtesting"):
            save_signal({
                "ticker": signal.ticker,
                "date": signal.as_of,
                "multi_agent_direction": signal.direction,
                "multi_agent_confidence": signal.confidence,
                "sentiment_baseline_direction": keyword_sentiment_baseline(
                    [e.item for e in top]
                ),
                "random_baseline_direction": random_baseline_signal(),
            })
            st.success(
                "Saved. Come back in 5-20 trading days and this will show up "
                "in the Evaluation tab with real forward-return results."
            )
    else:
        st.info("Enter a ticker and click **Run Analysis**.")


with tab_scan:
    st.subheader("Market Scan")

    scan_scope = st.radio(
        "Scan scope",
        [f"Curated watchlist (~{len(DEFAULT_WATCHLIST)} tickers, fast)",
         f"Full universe (~{universe_size()} tickers, slower, batched)"],
        index=0,
    )
    sector_filter = st.selectbox("Filter by sector (optional)", ["All"] + all_sectors())
    rank_by = st.selectbox("Rank by", ["volume", "price_change"])

    if st.button("Run Scan"):
        if scan_scope.startswith("Curated"):
            with st.spinner("Pulling market data..."):
                df = scan_watchlist(DEFAULT_WATCHLIST, rank_by=rank_by)
        else:
            with st.spinner(f"Scanning ~{universe_size()} tickers in batches (this takes a bit longer)..."):
                df = scan_full_universe(rank_by=rank_by)

        if df.empty:
            st.error("No data returned — check your internet connection.")
        else:
            if sector_filter != "All":
                sector_tickers = set(tickers_in_sector(sector_filter))
                df = df[df["ticker"].isin(sector_tickers)]
            st.caption(f"{len(df)} tickers shown" + (f" (filtered to {sector_filter})" if sector_filter != "All" else ""))
            st.dataframe(df, use_container_width=True)

    st.divider()
    st.subheader("🤖 AI Theme Analysis")
    st.caption("Runs the full 7-agent pipeline across up to 8 tickers in a chosen sector and aggregates the result.")
    theme_sector = st.selectbox("Sector / theme", all_sectors(), key="theme_sector")
    if st.button("Analyze Sector"):
        with st.spinner(f"Running 7-agent pipeline across {theme_sector} tickers..."):
            theme_result = analyze_theme(theme_sector, mode="heuristic", max_tickers=8)

        if not theme_result["tickers_analyzed"]:
            st.warning("No tickers mapped to this sector.")
        else:
            summary = theme_result["summary"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Dominant direction", summary["dominant_direction"].upper())
            c2.metric("Bullish", summary["bullish_count"])
            c3.metric("Bearish", summary["bearish_count"])
            c4.metric("Avg confidence", f"{summary['avg_confidence']:.0%}")
            st.dataframe(theme_results_to_df(theme_result), use_container_width=True)


with tab_monitor:
    st.subheader("Market Monitor")
    st.caption("Live price snapshot for every ticker you've saved a signal for.")

    saved_signals = load_signals()
    monitored_tickers = sorted(set(s["ticker"] for s in saved_signals))

    if not monitored_tickers:
        st.info(
            "No tickers being monitored yet — save a signal in the Live Analysis "
            "tab first, and it'll show up here."
        )
    else:
        if st.button("Refresh prices"):
            with st.spinner("Fetching current prices..."):
                df = scan_watchlist(monitored_tickers, rank_by="volume")
            if df.empty:
                st.error("Could not fetch prices.")
            else:
                st.dataframe(df, use_container_width=True)
        else:
            st.caption(f"Monitoring {len(monitored_tickers)} ticker(s): {', '.join(monitored_tickers)}")
            st.info("Click **Refresh prices** to pull the current snapshot.")


with tab_evidence:
    st.subheader("Evidence Ledger")
    if top:
        view = st.radio("View", ["Citation Cards", "Table"], horizontal=True)

        if view == "Citation Cards":
            for e in top:
                stance_color = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(
                    e.stance.value if e.stance else "neutral", "⚪"
                )
                with st.container(border=True):
                    st.markdown(f"{stance_color} **{e.item.title}**")
                    st.caption(f"Source: {e.item.source} · Credibility: {e.credibility_score:.0%} · Recency: {e.recency_score:.0%}")
                    if e.item.summary:
                        st.write(e.item.summary[:200] + ("..." if len(e.item.summary) > 200 else ""))
                    if e.item.url:
                        st.markdown(f"[Read source →]({e.item.url})")
                    st.caption(f"Combined relevance score: {e.combined_score}")
        else:
            rows = [
                {
                    "Title": e.item.title,
                    "Source": e.item.source,
                    "Stance": e.stance.value if e.stance else None,
                    "Relevance": e.relevance_score,
                    "Recency": e.recency_score,
                    "Credibility": e.credibility_score,
                    "Combined": e.combined_score,
                }
                for e in top
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

        st.subheader("Price / Technical Context")
        st.json(technical)
    else:
        st.info("Run an analysis in the Live Analysis tab first.")


with tab_eval:
    st.subheader("Backtest Diagnostics")
    saved = load_signals()
    st.caption(f"{len(saved)} signal(s) saved so far.")

    if len(saved) == 0:
        st.info(
            "No saved signals yet. Go to **Live Analysis**, run a few tickers, "
            "and click **Save this signal for later backtesting**. Come back "
            "after 5-20 trading days have passed so real forward returns exist."
        )
    else:
        summary = run_backtest(saved)
        if summary.empty:
            st.warning(
                "Signals are saved but not old enough yet for 5-day/20-day "
                "forward returns to exist. Check back later."
            )
        else:
            st.dataframe(summary, use_container_width=True)

            fig = px.bar(
                summary, x="method", y="hit_rate", color="horizon", barmode="group",
                title="Directional hit rate by method and horizon",
                labels={"hit_rate": "Hit rate (%)"},
            )
            st.plotly_chart(fig, use_container_width=True)

            st.caption(
                "Hit rate = % of signals where the predicted direction matched "
                "the actual price movement. Compare Multi-Agent Heuristic against "
                "both baselines — if it isn't clearly beating them, that is a "
                "real and worth-reporting finding, not a failure to hide."
            )
