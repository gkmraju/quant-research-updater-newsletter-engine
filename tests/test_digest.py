import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from quant_update_bot.arxiv_source import ArxivPaper
from quant_update_bot.config import AppConfig, QueryConfig
from quant_update_bot.digest import rank_papers, select_digest_items, write_digest
from quant_update_bot.store import StoredPaper


NOW = datetime(2026, 8, 17, 6, 30, tzinfo=UTC)


def make_stored_paper(
    *,
    arxiv_id: str = "2608.00001",
    age_days: int = 1,
    title: str = "Factor signal forecasting",
    summary: str = "We propose a factor model. Results show improved forecasts.",
    is_new: bool = True,
) -> StoredPaper:
    published_at = NOW - timedelta(days=age_days)
    return StoredPaper(
        paper=ArxivPaper(
            arxiv_id=arxiv_id,
            title=title,
            summary=summary,
            published_at=published_at,
            updated_at=published_at,
            url=f"https://arxiv.org/abs/{arxiv_id}",
            pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            authors=["Ada Analyst"],
            query_name="signals",
            query_text='all:"factor"',
        ),
        is_new=is_new,
    )


def make_config() -> AppConfig:
    return AppConfig(
        queries=[QueryConfig(name="signals", query='all:"factor"', weight=1.5)],
        lookback_days=7,
        max_digest_items=5,
        topic_keywords={"alpha": ["factor"]},
    )


class RankingTests(unittest.TestCase):
    def test_rank_is_deterministic_for_an_explicit_clock(self) -> None:
        ranked = rank_papers([make_stored_paper()], make_config(), now=NOW)

        self.assertEqual(ranked[0].topics, ["alpha"])
        self.assertEqual(ranked[0].score, 14.5)

    def test_rank_orders_higher_scoring_papers_first(self) -> None:
        older_seen = make_stored_paper(
            arxiv_id="2608.00002",
            age_days=4,
            title="General research note",
            summary="A descriptive market study.",
            is_new=False,
        )
        ranked = rank_papers([older_seen, make_stored_paper()], make_config(), now=NOW)

        self.assertEqual(ranked[0].stored.paper.arxiv_id, "2608.00001")

    def test_selection_respects_newness_lookback_and_limit(self) -> None:
        items = rank_papers(
            [
                make_stored_paper(),
                make_stored_paper(arxiv_id="2608.00002", is_new=False),
                make_stored_paper(arxiv_id="2608.00003", age_days=8),
            ],
            make_config(),
            now=NOW,
        )

        selected = select_digest_items(
            items,
            lookback_days=7,
            limit=1,
            include_seen=False,
            now=NOW,
        )

        self.assertEqual(
            [item.stored.paper.arxiv_id for item in selected],
            ["2608.00001"],
        )

    def test_digest_output_uses_explicit_generation_time(self) -> None:
        ranked = rank_papers([make_stored_paper()], make_config(), now=NOW)
        with TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "digest.md"
            write_digest(
                ranked,
                make_config(),
                destination,
                include_seen=False,
                generated_at=NOW,
            )
            rendered = destination.read_text(encoding="utf-8")

        self.assertIn("Generated at 2026-08-17 06:30 UTC", rendered)
        self.assertIn("## 1. Factor signal forecasting", rendered)


if __name__ == "__main__":
    unittest.main()
