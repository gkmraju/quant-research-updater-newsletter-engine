"""CLI entrypoint for the quant research updater."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
import time

from quant_update_bot.delivery import deliver_digest
from quant_update_bot.env import load_dotenv
from quant_update_bot.arxiv_source import fetch_recent_papers
from quant_update_bot.config import AppConfig
from quant_update_bot.digest import rank_papers, select_digest_items, write_digest
from quant_update_bot.publish import PublicationArtifacts, render_publication
from quant_update_bot.store import StateStore


@dataclass(slots=True)
class RunArtifacts:
    """Artifacts produced by one digest run."""

    markdown_path: Path
    publication: PublicationArtifacts | None


@dataclass(slots=True)
class FetchSummary:
    """High-level status for the upstream query fetch phase."""

    total_queries: int
    successful_queries: int
    failed_queries: int
    errors: list[str]


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
    parser.add_argument(
        "--deliver",
        choices=("none", "telegram", "email", "both"),
        default="none",
        help="Optional delivery target after generating the digest.",
    )
    parser.add_argument(
        "--subject",
        default=None,
        help="Optional email subject when using --deliver email or both.",
    )
    parser.add_argument(
        "--publication",
        choices=("none", "html", "pdf", "both"),
        default="both",
        help="Branded publication artifacts to render alongside markdown.",
    )
    return parser


def run(
    config_path: str,
    output_path: str | None = None,
    *,
    include_seen: bool = False,
) -> tuple[Path, list, FetchSummary]:
    """Execute one digest run and return the output path."""
    config = AppConfig.from_file(config_path)
    papers = []
    query_errors: list[str] = []
    successful_queries = 0
    for index, query in enumerate(config.queries):
        if index:
            time.sleep(1)
        try:
            papers.extend(fetch_recent_papers(query))
            successful_queries += 1
        except Exception as exc:
            error_text = f"query '{query.name}' failed: {exc}"
            query_errors.append(error_text)
            print(f"warning: {error_text}", file=sys.stderr)

    fetch_summary = FetchSummary(
        total_queries=len(config.queries),
        successful_queries=successful_queries,
        failed_queries=len(config.queries) - successful_queries,
        errors=query_errors,
    )
    if fetch_summary.total_queries and fetch_summary.successful_queries == 0:
        details = "; ".join(fetch_summary.errors) or "unknown upstream fetch failure"
        raise RuntimeError(f"Digest generation aborted because all source queries failed: {details}")

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
    return destination, digest_items, fetch_summary


def main() -> None:
    """Console-script entrypoint."""
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()
    output_path, digest_items, fetch_summary = run(
        args.config,
        args.output,
        include_seen=args.include_seen,
    )
    publication: PublicationArtifacts | None = None
    if args.publication != "none":
        publication = render_publication(
            digest_items,
            output_base=output_path.with_suffix(""),
            include_seen=args.include_seen,
        )
        if args.publication == "html":
            publication = PublicationArtifacts(
                html_path=publication.html_path,
                pdf_path=None,
            )
        elif args.publication == "pdf":
            publication = PublicationArtifacts(
                html_path=publication.html_path,
                pdf_path=publication.pdf_path,
            )
    if args.deliver != "none":
        delivered = deliver_digest(
            output_path,
            channel=args.deliver,
            subject=args.subject,
            pdf_path=None if publication is None else publication.pdf_path,
        )
        print(f"Delivered to: {', '.join(delivered)}", file=sys.stderr)
    if fetch_summary.failed_queries:
        print(
            "warning: completed with "
            f"{fetch_summary.failed_queries}/{fetch_summary.total_queries} query failures",
            file=sys.stderr,
        )
    print(output_path)


if __name__ == "__main__":
    main()
