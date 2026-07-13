"""
LLM mode: swaps the rule-based Analyst/Skeptic for real LLM reasoning.

Supports two providers behind the same interface:
  - OpenAI (requires OPENAI_API_KEY + billing)
  - Groq (requires GROQ_API_KEY, genuinely free tier, no credit card --
    Groq's API is OpenAI-compatible, so this reuses the same openai
    Python client, just pointed at Groq's endpoint with a Llama model)

Falls back to heuristic mode with a clear warning if neither key is set --
it should never silently pretend to be using an LLM when it isn't.

Both modes return the same Signal object (see schemas.py), so nothing
downstream (UI, evaluator) needs to know which mode produced a signal.
This is what makes an honest head-to-head comparison between heuristic
and LLM mode possible later.
"""

import json
import os
from datetime import datetime, timezone

from .schemas import Direction, ScoredEvidence, Signal, VerifierFlag

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def _active_provider() -> str | None:
    """Returns 'groq', 'openai', or None depending on which key is set.
    Groq is checked first since it's free -- no reason to spend OpenAI
    credits if a free Groq key is available."""
    if os.environ.get("GROQ_API_KEY"):
        return "groq"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return None


def llm_mode_available() -> bool:
    return OpenAI is not None and _active_provider() is not None


def _client() -> "OpenAI":
    if OpenAI is None:
        raise RuntimeError("openai package not installed. Run: pip install openai")

    provider = _active_provider()
    if provider == "groq":
        return OpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
        )
    if provider == "openai":
        return OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    raise RuntimeError(
        "No LLM API key set. Set GROQ_API_KEY (free, console.groq.com) "
        "or OPENAI_API_KEY (paid) as an environment variable."
    )


def _model_name() -> str:
    """Picks the right model name for whichever provider is active."""
    return "llama-3.3-70b-versatile" if _active_provider() == "groq" else "gpt-4o-mini"


ANALYST_SYSTEM_PROMPT = """You are a financial news analyst. Given a list of \
news headlines and summaries about a stock, classify the overall stance of \
EACH item as "bullish", "bearish", or "neutral" with respect to the stock's \
near-term price. Be conservative: if a headline is ambiguous or unrelated to \
the company's fundamentals, mark it neutral rather than forcing a direction.

Respond ONLY with valid JSON: a list of objects like
[{"index": 0, "stance": "bullish"}, {"index": 1, "stance": "neutral"}, ...]
matching the order of the items given, one entry per item, no extra text."""

SKEPTIC_SYSTEM_PROMPT = """You are a skeptical financial risk reviewer. You \
are given a proposed stock signal along with the evidence behind it. Your \
job is to actively look for reasons to DOUBT the conclusion: thin evidence, \
low-credibility sources, contradictory coverage, stale news, or evidence \
that doesn't actually support the stated direction.

If you find no real concerns, say so plainly -- do not invent problems.

Respond ONLY with valid JSON: a list of objects like
[{"concern": "...", "severity": "low|medium|high"}], or an empty list []
if there are no real concerns."""


def analyst_agent_llm(scored_evidence: list[ScoredEvidence]) -> list[ScoredEvidence]:
    client = _client()
    items_payload = [
        {"index": i, "title": e.item.title, "summary": e.item.summary}
        for i, e in enumerate(scored_evidence)
    ]

    response = client.chat.completions.create(
        model=_model_name(),
        messages=[
            {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(items_payload)},
        ],
        response_format={"type": "json_object"} if False else None,
        temperature=0,
    )

    try:
        stances = json.loads(response.choices[0].message.content)
        stance_map = {s["index"]: s["stance"] for s in stances}
    except (json.JSONDecodeError, KeyError, TypeError):
        stance_map = {}

    for i, e in enumerate(scored_evidence):
        raw_stance = stance_map.get(i, "neutral")
        try:
            e.stance = Direction(raw_stance)
        except ValueError:
            e.stance = Direction.NEUTRAL

    return scored_evidence


def skeptic_agent_llm(scored_evidence: list[ScoredEvidence], technical: dict) -> list[VerifierFlag]:
    client = _client()
    payload = {
        "evidence": [
            {
                "title": e.item.title,
                "source": e.item.source,
                "stance": e.stance.value if e.stance else None,
                "credibility_score": e.credibility_score,
                "recency_score": e.recency_score,
            }
            for e in scored_evidence
        ],
        "technical_context": technical,
    }

    response = client.chat.completions.create(
        model=_model_name(),
        messages=[
            {"role": "system", "content": SKEPTIC_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload)},
        ],
        temperature=0,
    )

    try:
        raw_flags = json.loads(response.choices[0].message.content)
        return [
            VerifierFlag(concern=f["concern"], severity=f.get("severity", "medium"))
            for f in raw_flags
        ]
    except (json.JSONDecodeError, KeyError, TypeError):
        return [VerifierFlag(concern="LLM verifier response could not be parsed.", severity="medium")]


def run_llm_pipeline(ticker: str, scored_evidence: list[ScoredEvidence], technical: dict) -> Signal:
    """
    Runs the Analyst -> Skeptic -> Decision chain with real LLM calls for
    the reasoning steps. The Decision step reuses the same deterministic
    aggregation logic as heuristic mode (agents.decision_agent_heuristic)
    so that confidence scoring stays consistent and auditable rather than
    being another opaque LLM call.
    """
    from .agents import decision_agent_heuristic  # reuse deterministic aggregation

    scored_evidence = analyst_agent_llm(scored_evidence)
    flags = skeptic_agent_llm(scored_evidence, technical)
    signal = decision_agent_heuristic(ticker, scored_evidence, flags, technical)
    signal.mode = "llm"
    return signal
