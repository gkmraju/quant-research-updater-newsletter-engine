"""Configuration loading for the quant research updater."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class QueryConfig:
    """One arXiv search query to poll."""

    name: str
    query: str
    max_results: int = 25
    weight: float = 1.0


@dataclass(slots=True)
class AppConfig:
    """Top-level app configuration."""

    queries: list[QueryConfig]
    lookback_days: int = 7
    max_digest_items: int = 10
    output_dir: Path = Path("output")
    state_db: Path = Path(".data/quant_updates.sqlite3")
    topic_keywords: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str | Path) -> "AppConfig":
        """Load config from JSON."""
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        queries = [QueryConfig(**item) for item in raw["queries"]]
        return cls(
            queries=queries,
            lookback_days=raw.get("lookback_days", 7),
            max_digest_items=raw.get("max_digest_items", 10),
            output_dir=Path(raw.get("output_dir", "output")),
            state_db=Path(raw.get("state_db", ".data/quant_updates.sqlite3")),
            topic_keywords=raw.get("topic_keywords", {}),
        )
