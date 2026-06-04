# QuantMind Review

Repository reviewed: [LLMQuant/quant-mind](https://github.com/LLMQuant/quant-mind)

## What is already real in the repo

- `quantmind.flows.paper_flow` can fetch arXiv, URLs, or local files and turn
  them into a structured `Paper` object with the OpenAI Agents SDK.
- `quantmind.preprocess.fetch` and `quantmind.preprocess.format` already give
  us solid low-level utilities for fetching PDFs/HTML and converting them into
  LLM-friendly text.
- `quantmind.flows.batch_run` is a useful concurrency primitive for processing
  a batch of papers once we decide which ones matter.
- `quantmind.knowledge` defines clean Pydantic schemas for papers and news.

## What is still mostly roadmap or design-doc territory

- No shipped `news_flow` yet. There is config/schema support for news, but not
  the extraction flow itself.
- No working memory/store layer in this branch. The README and storage docs
  describe it, but the code path is not present here yet.
- No alerting loop: no polling scheduler, dedupe rules, ranking, digest
  generation, or delivery channels.
- No production retrieval layer for embeddings, semantic search, or alert-time
  relevance ranking.

## Best way to build "a thing to update us"

Start narrow and align with what QuantMind already does well:

1. Poll sources.
   Start with arXiv because the repo already has paper-specific plumbing.

2. Track seen items.
   Store paper IDs and timestamps locally so each run only surfaces deltas.

3. Rank before deep extraction.
   Use query-level filters plus cheap scoring to decide which new papers deserve
   full-text extraction.

4. Extract only the top slice.
   For the highest-ranked papers, call `paper_flow` to create structured notes.

5. Deliver a digest.
   Publish markdown locally first, then push the same digest to Slack, email,
   or Telegram.

## Recommended product shape

- Tier 1: metadata monitor
  Cheap, fast, runs often, catches new items quickly.

- Tier 2: deep paper extraction
  Runs only on selected papers because this is the expensive LLM step.

- Tier 3: human-facing digest
  One daily or twice-daily summary with links, rationale, and topic labels.

## What I built in this workspace

- `quant_update_bot/`: a lightweight updater MVP
- `config.example.json`: configurable arXiv searches and topic keywords
- `output/latest_digest.md`: digest target file produced by each run

This gives us a practical base now, and we can later swap in QuantMind's
`paper_flow` for the deep-extraction stage.
