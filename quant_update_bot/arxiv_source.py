"""Minimal arXiv poller using the public Atom API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from socket import timeout as SocketTimeout
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from quant_update_bot.config import QueryConfig

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
USER_AGENT = "QuantNewsUpdater/0.1 (research digest prototype)"
DEFAULT_TIMEOUT_SECONDS = 8
MAX_RESULT_FALLBACK = 6


class ArxivFetchError(RuntimeError):
    """Raised when all fetch strategies fail for a query."""


@dataclass(slots=True)
class ArxivPaper:
    """Normalized paper record."""

    arxiv_id: str
    title: str
    summary: str
    published_at: datetime
    updated_at: datetime
    url: str
    pdf_url: str
    authors: list[str]
    query_name: str
    query_text: str


def fetch_recent_papers(query: QueryConfig) -> list[ArxivPaper]:
    """Fetch recent papers for one query.

    The fetch path intentionally gets more conservative as failures happen:
    try the full query first, then a smaller page size, then split broad `OR`
    expressions into smaller independent requests.
    """
    attempts = _build_attempts(query)
    errors: list[str] = []
    collected: dict[str, ArxivPaper] = {}
    for search_query, max_results in attempts:
        try:
            batch = _fetch_query_batch(
                search_query=search_query,
                max_results=max_results,
                query_name=query.name,
                original_query=query.query,
            )
        except ArxivFetchError as exc:
            errors.append(f"{search_query} [{max_results}]: {exc}")
            continue

        for paper in batch:
            collected.setdefault(paper.arxiv_id, paper)

        if collected:
            return sorted(
                collected.values(),
                key=lambda paper: paper.published_at,
                reverse=True,
            )

    joined = "; ".join(errors) if errors else "unknown error"
    raise ArxivFetchError(
        f"all strategies failed for query '{query.name}': {joined}"
    )


def _fetch_query_batch(
    *,
    search_query: str,
    max_results: int,
    query_name: str,
    original_query: str,
) -> list[ArxivPaper]:
    """Run one API request and parse it into normalized papers."""
    api_url = (
        "https://export.arxiv.org/api/query"
        f"?search_query={quote_plus(search_query)}"
        f"&start=0&max_results={max_results}"
        "&sortBy=submittedDate&sortOrder=descending"
    )
    xml_text = _download(api_url)
    root = ET.fromstring(xml_text)
    papers: list[ArxivPaper] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        entry_id = _text(entry, "atom:id")
        arxiv_id = entry_id.rsplit("/", 1)[-1]
        pdf_url = entry_id.replace("/abs/", "/pdf/") + ".pdf"
        papers.append(
            ArxivPaper(
                arxiv_id=arxiv_id,
                title=_clean(_text(entry, "atom:title")),
                summary=_clean(_text(entry, "atom:summary")),
                published_at=_parse_dt(_text(entry, "atom:published")),
                updated_at=_parse_dt(_text(entry, "atom:updated")),
                url=entry_id,
                pdf_url=pdf_url,
                authors=[
                    _clean(author.findtext("atom:name", "", ATOM_NS))
                    for author in entry.findall("atom:author", ATOM_NS)
                ],
                query_name=query_name,
                query_text=original_query,
            )
        )
    return papers


def _build_attempts(query: QueryConfig) -> list[tuple[str, int]]:
    """Build progressively lighter query attempts."""
    attempts: list[tuple[str, int]] = [(query.query, query.max_results)]
    clauses = [clause.strip() for clause in query.query.split(" OR ") if clause.strip()]
    if len(clauses) > 1:
        split_size = max(
            3,
            min(MAX_RESULT_FALLBACK, max(1, query.max_results // len(clauses))),
        )
        for clause in clauses:
            if (clause, split_size) not in attempts:
                attempts.append((clause, split_size))
    else:
        reduced = min(MAX_RESULT_FALLBACK, query.max_results)
        if reduced < query.max_results:
            attempts.append((query.query, reduced))
    return attempts


def _download(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    delays = (0, 2)
    for attempt, delay in enumerate((0, *delays), start=1):
        if delay:
            time.sleep(delay)
        try:
            with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
                return response.read().decode("utf-8")
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt > len(delays):
                raise ArxivFetchError(f"http {exc.code}: {exc.reason}") from exc
        except (TimeoutError, SocketTimeout) as exc:
            if attempt > len(delays):
                raise ArxivFetchError("request timed out") from exc
        except URLError as exc:
            if attempt > len(delays):
                raise ArxivFetchError(f"network error: {exc.reason}") from exc
    raise RuntimeError("unreachable retry state")


def _text(node: ET.Element, path: str) -> str:
    return node.findtext(path, "", ATOM_NS)


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _clean(value: str) -> str:
    return " ".join(value.split())
