# Quant News Updater

QuantNews Updater is a quant research monitor and newsletter generator. It
polls arXiv, tracks what is new, ranks papers by your themes, and turns them
into structured digests you can share internally or publish externally.

This repo started after reviewing
[`LLMQuant/quant-mind`](https://github.com/LLMQuant/quant-mind). QuantMind is a
good extraction framework; this project is the application layer on top of that
idea: polling, dedupe, ranking, digest generation, and delivery.

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
- Writes a markdown digest ready for newsletter use
- Optionally delivers the digest to Telegram or email

## Why this repo exists

QuantMind already has useful extraction primitives, but it does not yet ship a
finished “update us every day” product loop. This repo focuses on that loop:

- recurring polling
- source resilience
- seen-state and dedupe
- digest selection
- newsletter-style formatting
- lightweight distribution

## Quick Start

Generate a default digest:

```bash
python -m quant_update_bot.main --config config.example.json
```

Generate a richer demo from recently seen papers too:

```bash
python -m quant_update_bot.main --config config.example.json --include-seen --output output/enriched_digest.md
```

Send a digest to Telegram:

```bash
python -m quant_update_bot.main --config config.example.json --deliver telegram
```

Send a digest by email:

```bash
python -m quant_update_bot.main --config config.example.json --deliver email --subject "Quant Research Digest"
```

Set delivery secrets with environment variables. A starter file is included at
[.env.example](/C:/Users/RAJU/Documents/QuantNews/.env.example).

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
   `quant_update_bot/digest.py` renders the markdown digest and
   `quant_update_bot/delivery.py` optionally pushes it to Telegram or email.

## Repo Layout

```text
quant_update_bot/
  arxiv_source.py
  config.py
  delivery.py
  digest.py
  main.py
  store.py
  summary.py
  text_match.py
config.example.json
templates/
docs/
```

## Newsletter Path

The fastest path to a real newsletter is:

1. Keep the markdown digest as the canonical source.
2. Add one editorial pass before publishing.
3. Publish to email, Beehiiv, Substack, Ghost, Slack, or Telegram.

Suggested sections:

- Top Reads
- Alpha / Forecasting
- Execution / Microstructure
- Risk / Market Structure
- One Paper To Actually Read

Helpful supporting docs:

- [newsletter-playbook.md](/C:/Users/RAJU/Documents/QuantNews/docs/newsletter-playbook.md)
- [launch-pack.md](/C:/Users/RAJU/Documents/QuantNews/docs/launch-pack.md)
- [quantmind-analysis.md](/C:/Users/RAJU/Documents/QuantNews/docs/quantmind-analysis.md)
- [public-newsletter-template.md](/C:/Users/RAJU/Documents/QuantNews/templates/public-newsletter-template.md)

## GitHub Actions

This repo includes a scheduled workflow at
[daily-digest.yml](/C:/Users/RAJU/Documents/QuantNews/.github/workflows/daily-digest.yml)
that can generate a digest on a timer and upload it as an artifact.

## Next Upgrades

- Swap metadata-only summaries for full-paper extraction on the top N results
- Add RSS, blogs, SEC, and SSRN as sources
- Add Slack, Beehiiv, or Substack publishing
- Add thumbs-up/down feedback to improve ranking over time
- Replace keyword scoring with embeddings or LLM-based relevance ranking
