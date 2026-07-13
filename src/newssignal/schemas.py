"""
Core data models for NewsSignal.

Every piece of evidence and every signal the system produces is represented
as one of these structured objects. This is what makes the pipeline
explainable: instead of an LLM just returning a paragraph, it returns
data that fits these shapes, so the UI and the evaluator can always point
to exactly which evidence supported which conclusion.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Direction(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class NewsItem(BaseModel):
    """A single raw news item pulled from a source, before scoring."""
    title: str
    summary: str = ""
    source: str
    url: str = ""
    published_at: Optional[datetime] = None
    ticker: str


class ScoredEvidence(BaseModel):
    """
    A news item after the retrieval/reranking step.

    The score breakdown is kept explicit (not just one number) so the
    evidence ledger in the UI can show *why* something ranked highly.
    """
    item: NewsItem
    relevance_score: float = Field(..., description="Lexical match score (BM25/TF-IDF)")
    recency_score: float = Field(..., description="0-1, higher = more recent")
    credibility_score: float = Field(..., description="0-1, based on source reputation")
    combined_score: float = Field(..., description="Weighted blend of the above")
    stance: Optional[Direction] = Field(
        None, description="Does this piece of evidence support or challenge the eventual signal?"
    )


class VerifierFlag(BaseModel):
    """A single concern raised by the Skeptical Verifier agent."""
    concern: str
    severity: str  # "low" | "medium" | "high"
    related_evidence_url: Optional[str] = None


class Signal(BaseModel):
    """
    The final structured output of the pipeline for one ticker on one date.

    This is deliberately NOT just a text blob -- every field here is
    something the evaluator can check later against real price movement,
    and something the UI can render as a distinct piece of the decision.
    """
    ticker: str
    as_of: datetime
    direction: Direction
    confidence: float = Field(..., ge=0.0, le=1.0)
    catalyst: str = Field(..., description="One-sentence reason for the call")
    supporting_evidence: list[ScoredEvidence] = Field(default_factory=list)
    challenging_evidence: list[ScoredEvidence] = Field(default_factory=list)
    verifier_flags: list[VerifierFlag] = Field(default_factory=list)
    mode: str = Field(..., description="'heuristic' or 'llm'")
    abstained: bool = Field(
        False, description="True if evidence was too weak/contradictory to issue a real call"
    )
    abstain_reason: Optional[str] = None
    citation_audit_passed: bool = Field(
        True, description="True if every cited claim (catalyst, supporting/challenging evidence) traces to a real retrieved article"
    )


class EvalResult(BaseModel):
    """One row of the evaluation table: a past signal graded against reality."""
    ticker: str
    signal_date: datetime
    direction: Direction
    confidence: float
    price_at_signal: float
    price_after_5d: Optional[float] = None
    price_after_20d: Optional[float] = None
    return_5d: Optional[float] = None
    return_20d: Optional[float] = None
    correct_5d: Optional[bool] = None
    correct_20d: Optional[bool] = None
