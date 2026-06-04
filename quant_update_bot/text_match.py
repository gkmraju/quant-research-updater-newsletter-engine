"""Small text matching helpers for topic tagging."""

from __future__ import annotations

import re


def contains_keyword(text: str, keyword: str) -> bool:
    """Match single words and phrases without accidental substring hits."""
    escaped = re.escape(keyword.lower())
    pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return re.search(pattern, text.lower()) is not None
