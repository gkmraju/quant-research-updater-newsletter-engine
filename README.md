# Quant News Updater

QuantNews Updater is a lightweight quant research monitor that polls arXiv,
tracks what is new, ranks papers by your interests, and turns them into a
digest you can use as an internal update feed or the first draft of a public
newsletter.

This repo started after reviewing
[`LLMQuant/quant-mind`](https://github.com/LLMQuant/quant-mind). QuantMind is a
good extraction framework; this project is the delivery layer on top of that
idea: polling, dedupe, ranking, and digest generation.

## What it does

- Polls arXiv for quant-focused searches
- Stores seen papers in SQLite so each run highlights deltas
- Scores papers by freshness, topic keywords, and query weight
- Builds structured paper cards with:
  - summary
  - why it matters
  - method snapshot
  - evidence / claim
  - market relevance
- Writes a markdown digest ready for internal research sharing

## Why this repo exists

QuantMind already has useful extraction primitives, but it does not yet ship a
finished “update us every day” product loop. This repo focuses on that loop:

- recurring polling
- source resilience
- seen-state and dedupe
- digest selection
- newsletter-style formatting

## Quick Start

```bash
python -m quant_update_bot.main --config config.example.json
```

That writes the default digest to `output/latest_digest.md`.

To generate a richer demo from recently seen papers too:

```bash
python -m quant_update_bot.main --config config.example.json --include-seen --output output/enriched_digest.md
```

## How it works

1. Source polling
   `quant_update_bot/arxiv_source.py` fetches recent matches from arXiv with
   fallback strategies for fragile searches.

2. Stateful dedupe
   `quant_update_bot/store.py` persists seen paper IDs in SQLite.

3. Ranking
   `quant_update_bot/digest.py` scores items by freshness, topic matches, and
   per-query weighting.

4. Structured summary
   `quant_update_bot/summary.py` turns title + abstract into an editorial card.

5. Delivery
   `quant_update_bot/digest.py` renders the final markdown digest.

## Repo Layout

```text
quant_update_bot/
  arxiv_source.py
  config.py
  digest.py
  main.py
  store.py
  summary.py
  text_match.py
config.example.json
docs/
```

## Newsletter Path

The fastest path to a real newsletter is:

1. Keep the current markdown digest as the canonical source.
2. Add one editorial pass before publishing.
3. Push the final output to email, Beehiiv, Substack, Ghost, Slack, or Telegram.

Suggested sections:

- Top Reads
- Alpha / Forecasting
- Execution / Microstructure
- Risk / Market Structure
- One Paper To Actually Read

There is a fuller editorial playbook in
[newsletter-playbook.md](/C:/Users/RAJU/Documents/QuantNews/docs/newsletter-playbook.md)
and a repo comparison in
[quantmind-analysis.md](/C:/Users/RAJU/Documents/QuantNews/docs/quantmind-analysis.md).

## GitHub Actions

This repo includes a scheduled workflow at
[daily-digest.yml](/C:/Users/RAJU/Documents/QuantNews/.github/workflows/daily-digest.yml)
that can generate a digest on a timer and upload it as an artifact.

## Next Upgrades

- Swap metadata-only summaries for full-paper extraction on the top N results
- Add RSS, blogs, SEC, and SSRN as sources
- Send digests to Slack, Telegram, or email
- Add feedback signals to improve ranking over time
- Replace keyword scoring with embeddings or LLM-based relevance ranking
