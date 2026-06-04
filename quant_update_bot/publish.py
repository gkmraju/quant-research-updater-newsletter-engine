"""Branded HTML and PDF newsletter rendering."""

from __future__ import annotations

import html
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from jinja2 import Template

from quant_update_bot.digest import RankedPaper
from quant_update_bot.summary import build_paper_card

_HTML_TEMPLATE = Template(
    """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>{{ brand_name }} - {{ issue_date }}</title>
    <style>
      @page {
        size: A4;
        margin: 18mm 14mm 18mm 14mm;
      }
      :root {
        --ink: #171717;
        --muted: #5b5b5b;
        --line: #d9d0c4;
        --paper: #f6f1e8;
        --accent: #bb5a2a;
        --accent-soft: #f1d4bf;
        --card: #fffdf9;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, #f7dfc9 0%, transparent 25%),
          linear-gradient(180deg, #f8f4ed 0%, #efe4d7 100%);
        font-family: Georgia, "Times New Roman", serif;
        line-height: 1.45;
      }
      .page {
        width: 100%;
      }
      .hero {
        border: 1px solid var(--line);
        background: linear-gradient(140deg, rgba(255,253,249,.95), rgba(246,236,223,.92));
        border-radius: 24px;
        padding: 28px 28px 24px 28px;
        margin-bottom: 18px;
      }
      .eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 11px;
        color: var(--accent);
        margin-bottom: 10px;
        font-family: Arial, sans-serif;
      }
      h1 {
        margin: 0 0 8px 0;
        font-size: 30px;
        line-height: 1.05;
      }
      .subtitle {
        color: var(--muted);
        font-size: 14px;
        margin-bottom: 14px;
      }
      .signature {
        color: var(--muted);
        font-size: 11px;
        letter-spacing: 0.08em;
        text-transform: lowercase;
        margin-bottom: 14px;
        font-family: Arial, sans-serif;
      }
      .hero-grid {
        display: grid;
        grid-template-columns: 1.6fr 1fr;
        gap: 18px;
      }
      .hero-panel {
        border-top: 1px solid var(--line);
        padding-top: 12px;
      }
      .hero-panel h2 {
        margin: 0 0 8px 0;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-family: Arial, sans-serif;
      }
      .hero-panel p, .hero-panel li {
        font-size: 13px;
        color: var(--muted);
        margin: 0;
      }
      .hero-panel ul {
        padding-left: 16px;
        margin: 0;
      }
      .section-title {
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--accent);
        margin: 22px 0 10px 0;
        font-family: Arial, sans-serif;
      }
      .card {
        background: rgba(255,253,249,.95);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 10px 24px rgba(50,25,12,.05);
        break-inside: avoid;
      }
      .rank {
        display: inline-block;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        padding: 4px 10px;
        font-size: 11px;
        font-family: Arial, sans-serif;
        text-transform: uppercase;
        letter-spacing: .08em;
        margin-bottom: 8px;
      }
      .card h3 {
        margin: 0 0 8px 0;
        font-size: 22px;
        line-height: 1.18;
      }
      .meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 14px;
        margin-bottom: 10px;
        color: var(--muted);
        font-size: 12px;
        font-family: Arial, sans-serif;
      }
      .lede {
        font-size: 14px;
        margin-bottom: 10px;
      }
      .label {
        font-weight: bold;
      }
      .grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px 16px;
        margin-top: 8px;
      }
      .mini {
        font-size: 13px;
      }
      .abstract {
        margin-top: 10px;
        color: var(--muted);
        font-size: 12px;
      }
      .links a, .footer a {
        color: var(--accent);
        text-decoration: none;
      }
      .topics {
        margin-top: 10px;
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
      }
      .tag {
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 3px 9px;
        font-size: 11px;
        color: var(--muted);
        background: #fff;
        font-family: Arial, sans-serif;
      }
      .footer {
        margin-top: 20px;
        color: var(--muted);
        font-size: 12px;
        border-top: 1px solid var(--line);
        padding-top: 10px;
        font-family: Arial, sans-serif;
      }
    </style>
  </head>
  <body>
    <div class="page">
      <section class="hero">
        <div class="eyebrow">{{ brand_name }}</div>
        <h1>{{ title }}</h1>
        <div class="signature">by twisted_arrow</div>
        <div class="subtitle">
          {{ issue_date }} · {{ mode_label }} · Curated by {{ signature_name }}
        </div>
        <div class="hero-grid">
          <div class="hero-panel">
            <h2>Editorial Frame</h2>
            <p>
              Fresh quant research, ranked for practical relevance and packaged
              into a shareable digest with a clear house style.
            </p>
          </div>
          <div class="hero-panel">
            <h2>From</h2>
            <ul>
              <li>{{ github_signature }}</li>
              <li>{{ source_note }}</li>
              <li>{{ issue_count }} papers in this issue</li>
            </ul>
          </div>
        </div>
      </section>

      <div class="section-title">Top Reads</div>
      {% for item in items %}
      <article class="card">
        <div class="rank">#{{ loop.index }} · Score {{ "%.2f"|format(item.score) }}</div>
        <h3>{{ item.title }}</h3>
        <div class="meta">
          <div>{{ item.published }}</div>
          <div>{{ item.query_name }}</div>
          <div>{{ item.status }}</div>
          <div>{{ item.authors }}</div>
        </div>
        <div class="lede"><span class="label">Summary:</span> {{ item.headline }}</div>
        <div class="mini"><span class="label">Why it matters:</span> {{ item.angle }}</div>
        <div class="grid">
          <div class="mini"><span class="label">Method:</span> {{ item.method }}</div>
          <div class="mini"><span class="label">Evidence:</span> {{ item.evidence }}</div>
        </div>
        <div class="mini" style="margin-top: 8px;"><span class="label">Market relevance:</span> {{ item.market_relevance }}</div>
        <div class="topics">
          {% for tag in item.tags %}
          <span class="tag">{{ tag }}</span>
          {% endfor %}
        </div>
        <div class="abstract">{{ item.abstract }}</div>
        <div class="links mini" style="margin-top: 10px;">
          <a href="{{ item.url }}">Abstract</a> ·
          <a href="{{ item.pdf_url }}">PDF</a> ·
          <span>arXiv {{ item.arxiv_id }}</span>
        </div>
      </article>
      {% endfor %}

      <div class="footer">
        Built with QuantNews Updater · {{ github_signature }}
      </div>
    </div>
  </body>
</html>
"""
)


@dataclass(slots=True)
class PublicationArtifacts:
    """Output paths for branded publication assets."""

    html_path: Path
    pdf_path: Path | None


def render_publication(
    items: list[RankedPaper],
    *,
    output_base: Path,
    include_seen: bool,
) -> PublicationArtifacts:
    """Render branded HTML and, when possible, PDF output."""
    output_base = output_base.resolve()
    output_base.parent.mkdir(parents=True, exist_ok=True)
    html_path = output_base.with_suffix(".html")
    pdf_path = output_base.with_suffix(".pdf")
    html_path.write_text(
        _render_html(items, include_seen=include_seen),
        encoding="utf-8",
    )
    rendered_pdf = _render_pdf(html_path, pdf_path)
    return PublicationArtifacts(
        html_path=html_path,
        pdf_path=pdf_path if rendered_pdf else None,
    )


def _render_html(items: list[RankedPaper], *, include_seen: bool) -> str:
    brand_name = os.getenv("QUANTNEWS_BRAND_NAME", "Quant Research Digest")
    signature_name = os.getenv("QUANTNEWS_SIGNATURE_NAME", brand_name)
    github_signature = os.getenv(
        "QUANTNEWS_GITHUB_URL",
        "https://github.com/gkmraju/quant-research-updater-newsletter-engine",
    )
    issue_date = datetime.now(UTC).strftime("%Y-%m-%d")
    mode_label = "Recent Papers" if include_seen else "New Papers"
    cards = []
    for item in items:
        paper = item.stored.paper
        card = build_paper_card(item)
        authors = ", ".join(paper.authors[:4])
        if len(paper.authors) > 4:
            authors += ", et al."
        cards.append(
            {
                "score": item.score,
                "title": _escape(paper.title),
                "published": paper.published_at.date().isoformat(),
                "query_name": _escape(paper.query_name),
                "status": "new" if item.stored.is_new else "seen before",
                "authors": _escape(authors),
                "headline": _escape(card.headline),
                "angle": _escape(card.angle),
                "method": _escape(card.method),
                "evidence": _escape(card.evidence),
                "market_relevance": _escape(card.market_relevance),
                "tags": [_escape(tag) for tag in card.tags],
                "abstract": _escape(card_text(paper.summary, 900)),
                "url": paper.url,
                "pdf_url": paper.pdf_url,
                "arxiv_id": paper.arxiv_id,
            }
        )
    return _HTML_TEMPLATE.render(
        title=brand_name,
        brand_name=brand_name,
        issue_date=issue_date,
        mode_label=mode_label,
        signature_name=signature_name,
        github_signature=github_signature,
        source_note="Sources: arXiv + QuantNews Updater ranking",
        issue_count=len(cards),
        items=cards,
    )


def _render_pdf(html_path: Path, pdf_path: Path) -> bool:
    browser = _find_browser()
    if browser is None:
        return False
    html_path = html_path.resolve()
    pdf_path = pdf_path.resolve()
    file_url = f"file:///{quote(str(html_path).replace(chr(92), '/'), safe=':/')}"
    with tempfile.TemporaryDirectory(prefix="quantnews-pdf-") as temp_dir:
        command = [
            browser,
            "--headless",
            "--disable-gpu",
            f"--user-data-dir={temp_dir}",
            f"--print-to-pdf={pdf_path}",
            file_url,
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    return result.returncode == 0 and pdf_path.exists()


def _find_browser() -> str | None:
    candidates = (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def card_text(value: str, limit: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."
