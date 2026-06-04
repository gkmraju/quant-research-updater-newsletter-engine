"""QuantMind-style structured paper cards built from paper metadata."""

from __future__ import annotations

from dataclasses import dataclass
import re

from typing import TYPE_CHECKING

from quant_update_bot.text_match import contains_keyword

if TYPE_CHECKING:
    from quant_update_bot.digest import RankedPaper

_METHOD_HINTS = (
    "we propose",
    "we introduce",
    "we develop",
    "we present",
    "this paper",
    "our method",
    "framework",
    "model",
    "approach",
)
_RESULT_HINTS = (
    "outperform",
    "improve",
    "improvement",
    "results show",
    "experiments show",
    "demonstrate",
    "achieve",
    "reduces",
    "increase",
)
_RISK_HINTS = (
    "volatility",
    "risk",
    "drawdown",
    "tail",
    "liquidity",
    "systemic",
)
_ALPHA_HINTS = (
    "factor",
    "momentum",
    "alpha",
    "forecast",
    "prediction",
    "signal",
)
_EXECUTION_HINTS = (
    "execution",
    "order book",
    "market impact",
    "microstructure",
    "vwap",
)
_LLM_HINTS = (
    "llm",
    "large language model",
    "retrieval",
    "rag",
    "chatgpt",
)


@dataclass(slots=True)
class PaperCard:
    """A lightweight structured note for one paper."""

    headline: str
    angle: str
    method: str
    evidence: str
    market_relevance: str
    tags: list[str]


def build_paper_card(item: RankedPaper) -> PaperCard:
    """Create a structured card from title, abstract, and topic matches."""
    paper = item.stored.paper
    sentences = _split_sentences(paper.summary)
    headline = sentences[0] if sentences else paper.summary
    method = _pick_sentence(sentences, _METHOD_HINTS) or headline
    evidence = _pick_sentence(sentences, _RESULT_HINTS) or (
        sentences[1] if len(sentences) > 1 else headline
    )
    tags = _derive_tags(item)
    return PaperCard(
        headline=_trim(headline),
        angle=_build_angle(item, tags),
        method=_trim(method),
        evidence=_trim(evidence),
        market_relevance=_build_market_relevance(item, tags),
        tags=tags,
    )


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    return [part.strip() for part in parts if part.strip()]


def _pick_sentence(sentences: list[str], hints: tuple[str, ...]) -> str | None:
    for sentence in sentences:
        lower = sentence.lower()
        if any(contains_keyword(lower, hint) for hint in hints):
            return sentence
    return None


def _derive_tags(item: RankedPaper) -> list[str]:
    text = f"{item.stored.paper.title} {item.stored.paper.summary}".lower()
    tags = list(item.topics)
    if any(contains_keyword(text, hint) for hint in _ALPHA_HINTS) and "alpha" not in tags:
        tags.append("alpha")
    if any(contains_keyword(text, hint) for hint in _EXECUTION_HINTS) and "execution" not in tags:
        tags.append("execution")
    if any(contains_keyword(text, hint) for hint in _RISK_HINTS) and "risk" not in tags:
        tags.append("risk")
    if any(contains_keyword(text, hint) for hint in _LLM_HINTS) and "llm" not in tags:
        tags.append("llm")
    return tags or ["general"]


def _build_angle(item: RankedPaper, tags: list[str]) -> str:
    primary = tags[0]
    title = item.stored.paper.title
    if primary == "alpha":
        return f"This looks relevant for signal discovery or return forecasting work around {title}."
    if primary == "execution":
        return "This looks relevant for trade execution, market impact, or order-book modeling."
    if primary == "risk":
        return "This looks relevant for risk modeling, volatility monitoring, or stress scenarios."
    if primary == "llm":
        return "This looks relevant for AI-assisted quant research workflows or finance-specific LLM usage."
    return "This looks like a general quant research paper worth a quick scan."


def _build_market_relevance(item: RankedPaper, tags: list[str]) -> str:
    paper = item.stored.paper
    if "execution" in tags:
        return "Most useful if we care about execution quality, slippage, or intraday market structure."
    if "alpha" in tags:
        return "Most useful if we are screening for tradable signals, cross-sectional effects, or forecast edges."
    if "risk" in tags:
        return "Most useful if we are improving portfolio risk controls or tail-awareness."
    if "llm" in tags:
        return "Most useful if we are building research automation, retrieval, or model-assisted analysis."
    return f"Most useful as a background research input for the `{paper.query_name}` theme."


def _trim(text: str, limit: int = 260) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
