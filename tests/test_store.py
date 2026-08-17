import unittest
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from quant_update_bot.arxiv_source import ArxivPaper
from quant_update_bot.store import StateStore


def make_paper(*, title: str = "Initial title") -> ArxivPaper:
    published_at = datetime(2026, 8, 16, tzinfo=UTC)
    return ArxivPaper(
        arxiv_id="2608.00001",
        title=title,
        summary="A deterministic abstract.",
        published_at=published_at,
        updated_at=published_at,
        url="https://arxiv.org/abs/2608.00001",
        pdf_url="https://arxiv.org/pdf/2608.00001.pdf",
        authors=["Ada Analyst"],
        query_name="signals",
        query_text='all:"factor"',
    )


class StateStoreTests(unittest.TestCase):
    def test_upsert_marks_only_first_observation_as_new(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = StateStore(Path(temp_dir) / "state.sqlite3")

            first = store.upsert_papers([make_paper()])
            second = store.upsert_papers([make_paper(title="Updated title")])

        self.assertTrue(first[0].is_new)
        self.assertFalse(second[0].is_new)
        self.assertEqual(second[0].paper.title, "Updated title")


if __name__ == "__main__":
    unittest.main()
