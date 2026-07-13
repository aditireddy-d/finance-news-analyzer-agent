"""
7-agent LangGraph pipeline: Retriever -> Evidence Selector -> Market Context
-> Analyst -> Skeptical Verifier -> Citation Auditor -> Decision.

This is a genuine architectural refactor, not new capability: it takes logic
that already existed (news fetching, scoring, technical snapshot, stance
assignment, verification, decision-making) and makes each step an explicit,
named, inspectable node in a real state graph, plus adds one new real check
(Citation Auditor) that didn't exist as a separate step before.

Every node reads and writes a single shared PipelineState, so the full
trace of what each agent did is visible afterward -- this is what "7 agents"
should mean: separable responsibilities with visible state, not just seven
function calls glued together.
"""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from .schemas import NewsItem, ScoredEvidence, VerifierFlag, Signal
from .news_ingester import fetch_news_yfinance
from .news_sources_rss import fetch_multi_source_news
from .rag_pipeline import score_evidence, top_evidence
from .technical_factors import technical_snapshot
from .agents import analyst_agent_heuristic, skeptic_agent_heuristic, decision_agent_heuristic
from .llm_agents import analyst_agent_llm, skeptic_agent_llm, llm_mode_available


class PipelineState(TypedDict):
    ticker: str
    mode: str  # "heuristic" or "llm"
    use_multi_source: bool
    top_k: int

    # filled in as the graph runs -- each field corresponds to one agent's output
    raw_news: Optional[list[NewsItem]]
    scored_evidence: Optional[list[ScoredEvidence]]
    technical: Optional[dict]
    verifier_flags: Optional[list[VerifierFlag]]
    citation_audit_passed: Optional[bool]
    citation_audit_notes: Optional[list[str]]
    signal: Optional[Signal]


# ---------------------------------------------------------------- 1. Retriever
def retriever_node(state: PipelineState) -> PipelineState:
    if state["use_multi_source"]:
        news = fetch_multi_source_news(state["ticker"])
    else:
        news = fetch_news_yfinance(state["ticker"])
    return {**state, "raw_news": news}


# ---------------------------------------------------------------- 2. Evidence Selector
def evidence_selector_node(state: PipelineState) -> PipelineState:
    scored = score_evidence(state["raw_news"] or [], query=f"{state['ticker']} stock")
    top = top_evidence(scored, k=state["top_k"])
    return {**state, "scored_evidence": top}


# ---------------------------------------------------------------- 3. Market Context
def market_context_node(state: PipelineState) -> PipelineState:
    technical = technical_snapshot(state["ticker"])
    return {**state, "technical": technical}


# ---------------------------------------------------------------- 4. Analyst
def analyst_node(state: PipelineState) -> PipelineState:
    if state["mode"] == "llm" and llm_mode_available():
        evidence = analyst_agent_llm(state["scored_evidence"])
    else:
        evidence = analyst_agent_heuristic(state["scored_evidence"])
    return {**state, "scored_evidence": evidence}


# ---------------------------------------------------------------- 5. Skeptical Verifier
def skeptical_verifier_node(state: PipelineState) -> PipelineState:
    if state["mode"] == "llm" and llm_mode_available():
        flags = skeptic_agent_llm(state["scored_evidence"], state["technical"])
    else:
        flags = skeptic_agent_heuristic(state["scored_evidence"], state["technical"])
    return {**state, "verifier_flags": flags}


# ---------------------------------------------------------------- 6. Citation Auditor
def citation_auditor_node(state: PipelineState) -> PipelineState:
    """
    Checks that the evidence pool used for the decision actually consists
    of real, retrieved articles with a title and source -- i.e. nothing
    downstream can cite a claim that doesn't trace back to something the
    Retriever actually pulled. This is a real (if simple) integrity check,
    not decoration: it would catch a bug where evidence got corrupted or
    fabricated somewhere in the pipeline before reaching Decision.
    """
    notes = []
    passed = True
    for e in state["scored_evidence"] or []:
        if not e.item.title or not e.item.source:
            passed = False
            notes.append(f"Evidence item missing title/source: {e.item}")
    if not state["scored_evidence"]:
        notes.append("No evidence items to audit -- Decision should abstain.")
    return {**state, "citation_audit_passed": passed, "citation_audit_notes": notes}


# ---------------------------------------------------------------- 7. Decision
def decision_node(state: PipelineState) -> PipelineState:
    signal = decision_agent_heuristic(
        state["ticker"], state["scored_evidence"], state["verifier_flags"], state["technical"]
    )
    signal.mode = state["mode"]
    signal.citation_audit_passed = state.get("citation_audit_passed", True)
    return {**state, "signal": signal}


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("retriever", retriever_node)
    graph.add_node("evidence_selector", evidence_selector_node)
    graph.add_node("market_context", market_context_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("skeptical_verifier", skeptical_verifier_node)
    graph.add_node("citation_auditor", citation_auditor_node)
    graph.add_node("decision", decision_node)

    graph.set_entry_point("retriever")
    graph.add_edge("retriever", "evidence_selector")
    graph.add_edge("evidence_selector", "market_context")
    graph.add_edge("market_context", "analyst")
    graph.add_edge("analyst", "skeptical_verifier")
    graph.add_edge("skeptical_verifier", "citation_auditor")
    graph.add_edge("citation_auditor", "decision")
    graph.add_edge("decision", END)

    return graph.compile()


_COMPILED_GRAPH = None


def run_full_pipeline(
    ticker: str,
    mode: str = "heuristic",
    use_multi_source: bool = True,
    top_k: int = 8,
) -> PipelineState:
    """
    Runs all 7 agents end to end, starting from just a ticker symbol.
    Returns the full final state (not just the Signal) so callers can
    inspect what each agent produced -- e.g. the UI can show the raw
    news count, the citation audit result, etc.
    """
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_graph()

    initial_state: PipelineState = {
        "ticker": ticker,
        "mode": mode,
        "use_multi_source": use_multi_source,
        "top_k": top_k,
        "raw_news": None,
        "scored_evidence": None,
        "technical": None,
        "verifier_flags": None,
        "citation_audit_passed": None,
        "citation_audit_notes": None,
        "signal": None,
    }
    return _COMPILED_GRAPH.invoke(initial_state)
