"""CLI entrypoint for the quant research updater."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

from quant_update_bot.arxiv_source import fetch_recent_papers
from quant_update_bot.config import AppConfig
from quant_update_bot.digest import rank_papers, select_digest_items, write_digest
from quant_update_bot.store import StateStore


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="config.example.json",
        help="Path to the updater config JSON file.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional explicit markdown output path.",
    )
    parser.add_argument(
        "--include-seen",
        action="store_true",
        help="Include recent already-seen papers in the digest output.",
    )
    return parser


def run(
    config_path: str,
    output_path: str | None = None,
    *,
    include_seen: bool = False,
) -> Path:
    """Execute one digest run and return the output path."""
    config = AppConfig.from_file(config_path)
    papers = []
    for index, query in enumerate(config.queries):
        if index:
            time.sleep(1)
        try:
            papers.extend(fetch_recent_papers(query))
        except Exception as exc:
            print(f"warning: query '{query.name}' failed: {exc}", file=sys.stderr)

    store = StateStore(config.state_db)
    stored = store.upsert_papers(papers)
    ranked = rank_papers(stored, config)
    digest_items = select_digest_items(
        ranked,
        lookback_days=config.lookback_days,
        limit=config.max_digest_items,
        include_seen=include_seen,
    )

    destination = (
        Path(output_path)
        if output_path is not None
        else config.output_dir / "latest_digest.md"
    )
    write_digest(
        digest_items,
        config,
        destination,
        include_seen=include_seen,
    )
    return destination


def main() -> None:
    """Console-script entrypoint."""
    parser = build_parser()
    args = parser.parse_args()
    output_path = run(
        args.config,
        args.output,
        include_seen=args.include_seen,
    )
    print(output_path)


if __name__ == "__main__":
    main()
