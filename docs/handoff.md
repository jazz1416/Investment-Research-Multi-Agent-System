# Data and Research Pipeline Handoff

## Owner

Keana - Data + Preprocessing + Research Pipeline

## Purpose

This document explains what the data/research lane produces, what downstream teammates should consume, and what they should not repeat.

## Completed Pipeline

```text
external data
-> ingestion
-> preprocessing
-> relevance filtering
-> evidence assembly
-> news classification
-> fact extraction
-> research summarization
```

## Primary Downstream Files

### Combined Daily Evidence

```text
data/processed/daily_evidence.csv
```

Use this when an agent needs market, insider, and news evidence aligned by day.

Typical fields:

```text
ticker
date
open
high
low
close
volume
daily_return
volume_change
news_count
news_titles
news_urls
insider_transaction_count
insider_names
insider_total_value
```

### Structured News Research

```text
data/processed/news_research_results.csv
```

Use this when an agent needs preprocessed and LLM-structured news evidence.

Recommended downstream fields:

```text
ticker
published_at
category
event
key_facts
summary
source
url
```

## Recommended Planner / Router Input

Each news research record already contains:

```text
ticker
category
event
key_facts
summary
source
url
published_at
```

The Planner/Router should consume these fields directly rather than repeating ingestion, cleaning, relevance filtering, or article-level prompt chaining.

## Traceability

Every structured news record retains:

```text
source
url
published_at
title
```

This allows later agents and the Evaluator-Optimizer to trace generated analysis back to the originating article.

## Classification vs Routing

Notebook 03 produces a news-content category:

```text
earnings
product_service
management
regulation_legal
merger_acquisition
analyst_investor
macro_market
other
```

This describes what the article is about.

It does not decide which specialist agent should handle the item.

Routing remains Rajni's responsibility.

## Expected Downstream Flow

```text
news_research_results.csv
-> Planner
-> Router
-> specialist agent(s)
-> Evaluator-Optimizer
-> refinement
```

## Responsibility Boundaries

### Keana provides

- clean SEC data
- clean market data
- clean and relevance-filtered news
- daily combined evidence
- article classifications
- structured fact extraction
- research summaries
- source URLs for traceability
- quality checks

### Rajni owns

- Planner Agent behavior
- Router Agent behavior
- tool selection
- specialist-agent coordination
- autonomous routing decisions

### Jasmine owns

- evaluator scoring
- self-reflection
- refinement loops
- cross-run memory
- end-to-end workflow testing

## Reproducing Keana's Pipeline

If raw source files already exist:

```text
01_data_preprocessing.ipynb
-> 02_evidence_assembly.ipynb
-> 03_news_processing_chain.ipynb
```

Notebook 00 only needs to run when fresh external data is required.

## Environment

```bash
uv sync
uv run jupyter lab
```

VS Code/Jupyter interpreter:

```text
.venv\Scripts\python.exe
```

## LLM Configuration

Example for OpenRouter:

```text
LLM_API_KEY=your_openrouter_key
LLM_MODEL=your_model_slug
LLM_BASE_URL=https://openrouter.ai/api/v1
NEWS_CHAIN_LIMIT=10
FORCE_NEWS_CHAIN=false
```

Never commit the real `.env`.

## Refresh Guidance

For routine development:

```text
FORCE_REFRESH=false
FORCE_NEWS_CHAIN=false
```

Set either flag to `true` only when intentionally refreshing external data or regenerating LLM results.

## Handoff Checklist

- [ ] `01_data_preprocessing.ipynb` runs cleanly
- [ ] `02_evidence_assembly.ipynb` runs cleanly
- [ ] `03_news_processing_chain.ipynb` runs cleanly
- [ ] `news_clean.csv` contains `relevance_score`
- [ ] `daily_evidence.csv` contains no duplicate `ticker/date` rows
- [ ] `news_research_results.csv` exists
- [ ] article categories are valid
- [ ] summaries are populated
- [ ] source URLs are preserved
- [ ] Ruff passes
- [ ] no API keys are committed

## What Downstream Teammates Should Not Redo

Do not repeat raw news cleaning, duplicate removal, relevance filtering, article classification, fact extraction, or article summarization unless a downstream workflow explicitly needs to reevaluate those results.

The saved processed files are the handoff contract.
