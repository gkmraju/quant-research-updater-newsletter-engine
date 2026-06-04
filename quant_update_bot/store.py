"""SQLite state for dedupe and digest history."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from quant_update_bot.arxiv_source import ArxivPaper


@dataclass(slots=True)
class StoredPaper:
    """Paper plus newness state."""

    paper: ArxivPaper
    is_new: bool


class StateStore:
    """Persistent seen-state for papers."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS papers (
                    arxiv_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    url TEXT NOT NULL,
                    pdf_url TEXT NOT NULL,
                    authors TEXT NOT NULL,
                    query_name TEXT NOT NULL,
                    query_text TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                )
                """
            )

    def upsert_papers(self, papers: list[ArxivPaper]) -> list[StoredPaper]:
        """Insert unseen papers and refresh timestamps for known ones."""
        now = datetime.now(UTC).isoformat()
        results: list[StoredPaper] = []
        with self._connect() as conn:
            for paper in papers:
                row = conn.execute(
                    "SELECT 1 FROM papers WHERE arxiv_id = ?",
                    (paper.arxiv_id,),
                ).fetchone()
                is_new = row is None
                if is_new:
                    conn.execute(
                        """
                        INSERT INTO papers (
                            arxiv_id, title, summary, published_at, updated_at,
                            url, pdf_url, authors, query_name, query_text,
                            first_seen_at, last_seen_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            paper.arxiv_id,
                            paper.title,
                            paper.summary,
                            paper.published_at.isoformat(),
                            paper.updated_at.isoformat(),
                            paper.url,
                            paper.pdf_url,
                            " | ".join(paper.authors),
                            paper.query_name,
                            paper.query_text,
                            now,
                            now,
                        ),
                    )
                else:
                    conn.execute(
                        """
                        UPDATE papers
                        SET title = ?, summary = ?, published_at = ?, updated_at = ?,
                            url = ?, pdf_url = ?, authors = ?, query_name = ?,
                            query_text = ?, last_seen_at = ?
                        WHERE arxiv_id = ?
                        """,
                        (
                            paper.title,
                            paper.summary,
                            paper.published_at.isoformat(),
                            paper.updated_at.isoformat(),
                            paper.url,
                            paper.pdf_url,
                            " | ".join(paper.authors),
                            paper.query_name,
                            paper.query_text,
                            now,
                            paper.arxiv_id,
                        ),
                    )
                results.append(StoredPaper(paper=paper, is_new=is_new))
        return results
