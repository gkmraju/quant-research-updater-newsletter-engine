"""Ranking and digest rendering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from quant_update_bot.config import AppConfig
from quant_update_bot.store import StoredPaper
from quant_update_bot.summary import build_paper_card
from quant_update_bot.text_match import contains_keyword


@dataclass(slots=True)
class RankedPaper:
    """Stored paper with derived score and labels."""

    stored: StoredPaper
    score: float
    topics: list[str]


def rank_papers(
    items: list[StoredPaper],
    config: AppConfig,
    *,
    now: datetime | None = None,
) -> list[RankedPaper]:
    """Score papers by freshness and keyword density."""
    now = now or datetime.now(UTC)
    query_weights = {query.name: query.weight for query in config.queries}
    ranked: list[RankedPaper] = []
    for item in items:
        text = f"{item.paper.title} {item.paper.summary}".lower()
        topics = [
            topic
            for topic, keywords in config.topic_keywords.items()
            if any(contains_keyword(text, keyword) for keyword in keywords)
        ]
        age_days = max((now - item.paper.published_at).total_seconds() / 86400, 0.0)
        freshness = max(config.lookback_days - age_days, 0.0)
        topic_bonus = float(len(topics)) * 2.0
        new_bonus = 5.0 if item.is_new else 0.0
        query_bonus = query_weights.get(item.paper.query_name, 1.0)
        score = freshness + topic_bonus + new_bonus + query_bonus
        ranked.append(RankedPaper(stored=item, score=score, topics=topics))
    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked


def select_digest_items(
    items: list[RankedPaper],
    lookback_days: int,
    limit: int,
    *,
    include_seen: bool,
    now: datetime | None = None,
) -> list[RankedPaper]:
    """Keep recent papers inside the lookback window."""
    cutoff = (now or datetime.now(UTC)) - timedelta(days=lookback_days)
    recent = [
        item
        for item in items
        if item.stored.paper.published_at >= cutoff
        and (include_seen or item.stored.is_new)
    ]
    return recent[:limit]


def write_digest(
    items: list[RankedPaper],
    config: AppConfig,
    destination: Path,
    *,
    include_seen: bool,
    generated_at: datetime | None = None,
) -> None:
    """Render a markdown digest to disk."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    mode_label = "recent papers" if include_seen else "new papers"
    timestamp = (generated_at or datetime.now(UTC)).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Quant Research Digest",
        "",
        f"Generated at {timestamp}",
        f"Digest mode: {mode_label}",
        "",
    ]
    if not items:
        lines.append(f"No {mode_label} matched the configured searches.")
    for index, item in enumerate(items, start=1):
        paper = item.stored.paper
        card = build_paper_card(item)
        topics = ", ".join(item.topics) if item.topics else "general"
        authors = ", ".join(paper.authors[:4])
        if len(paper.authors) > 4:
            authors += ", et al."
        lines.extend(
            [
                f"## {index}. {paper.title}",
                "",
                f"- arXiv: `{paper.arxiv_id}`",
                f"- Published: {paper.published_at.date().isoformat()}",
                f"- Query: {paper.query_name}",
                f"- Topics: {topics}",
                f"- Score: {item.score:.2f}",
                f"- Status: {'new' if item.stored.is_new else 'seen before'}",
                f"- Authors: {authors}",
                f"- Links: [abstract]({paper.url}) | [pdf]({paper.pdf_url})",
                "",
                f"**Summary**: {card.headline}",
                "",
                f"**Why it matters**: {card.angle}",
                "",
                f"**Method snapshot**: {card.method}",
                "",
                f"**Evidence / claim**: {card.evidence}",
                "",
                f"**Market relevance**: {card.market_relevance}",
                "",
                f"**Tags**: {', '.join(card.tags)}",
                "",
                "**Abstract**",
                "",
                paper.summary,
                "",
            ]
        )
    destination.write_text("\n".join(lines), encoding="utf-8")
