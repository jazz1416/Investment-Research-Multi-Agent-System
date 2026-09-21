# Project Decisions

This file records team-approved technical and workflow decisions for the **Investment Research Multi-Agent System**. Update this document whenever a shared convention, data contract, provider, model, or workflow changes.

---

## 2026-09-20 — Project Structure and Handoff Contract

### Decision

Use a notebook pipeline with saved files as the contract between stages:

```text
00_data_ingestion.ipynb
-> 01_data_preprocessing.ipynb
-> 02_evidence_assembly.ipynb
-> 03_news_processing_chain.ipynb
-> Planner / Router / Specialist Agents
-> Evaluator-Optimizer
```

### Rationale

Notebook files can be difficult to merge and are owned by different team members. Persisting outputs to disk lets downstream teammates use completed upstream work without rerunning or editing another person's notebook.

### Handoff Files

```text
data/processed/daily_evidence.csv
data/processed/news_research_results.csv
```

Downstream agents should consume these files rather than repeating ingestion or preprocessing.

---

## 2026-09-20 — Team Responsibility Boundaries

### Decision

Use the following ownership split.

**Keana — Data + Preprocessing + Research Pipeline**

- data ingestion
- data cleaning and preprocessing
- news relevance filtering
- evidence assembly
- news prompt chain: classify -> extract -> summarize
- data and prompt-chain quality checks
- structured handoff outputs

**Rajni — Agentic AI Core**

- Planner Agent
- Router Agent
- tool selection
- specialist-agent coordination
- autonomous routing decisions

**Jasmine — Workflow + Evaluation + Memory**

- Evaluator-Optimizer
- self-reflection
- quality scoring
- refinement loops
- memory across runs
- full-workflow testing

### Rationale

The split minimizes overlapping implementation and gives each contributor a clear deliverable.

---

## 2026-09-20 — Environment and Dependency Management

### Decision

Use **Python 3.12** and **uv** exclusively for project dependency and environment management.

Commands:

```bash
uv sync
uv run jupyter lab
uv run ruff format .
uv run ruff check .
```

The VS Code/Jupyter interpreter should use:

```text
.venv\Scripts\python.exe
```

### Rationale

Using one dependency manager and a committed lockfile improves reproducibility across team machines.

---

## 2026-09-20 — Shared Preprocessing Conventions

### Decision

Use shared preprocessing rules across all evidence sources:

- `SEED = 42`
- lowercase/normalized column names
- uppercase ticker symbols
- UTC timestamps where possible
- explicit numeric conversion
- explicit missing-value handling
- duplicate removal
- row-count reporting
- processed-dataset fingerprints
- no manual modification of raw source files

### Rationale

All agents should analyze the same standardized evidence.

---

## 2026-09-20 — Data Providers

### Decision

Use separate providers for each evidence type:

| Evidence | Provider |
|---|---|
| Insider transactions | SEC EDGAR |
| Daily market OHLCV | Alpha Vantage |
| Financial news | Marketaux |

### Rationale

Alpha Vantage's free request limits made it inefficient to use for both market data and news. Marketaux is used specifically for news while Alpha Vantage remains the market-data provider.

---

## 2026-09-20 — SEC Form 4 Retrieval

### Decision

Retrieve SEC Form 4 data using the issuer CIK and the filing directory's `index.json`, then locate and parse the raw ownership XML.

Do not guess a transformed XML URL.

### Rationale

SEC filing pages can expose transformed document paths. Reading the actual filing directory is more reliable and avoids failed XML parsing.

### SEC Access Requirement

`SEC_USER_AGENT` must identify the application and include contact information.

Example placeholder:

```text
SEC_USER_AGENT=Investment-Research-Multi-Agent-System your-email@example.com
```

---

## 2026-09-20 — Raw Data Preservation

### Decision

Notebook 00 saves source-shaped data to:

```text
data/raw/sec_form4.csv
data/raw/market_data.csv
data/raw/news.csv
```

Raw files should not be manually cleaned or edited.

### Refresh Behavior

```text
FORCE_REFRESH=false
```

is the normal development setting.

Set it to `true` only when fresh external data is intentionally required.

### Rationale

Preserving raw snapshots makes preprocessing reproducible and avoids unnecessary API usage.

---

## 2026-09-20 — Market Data Schema

### Decision

Use Alpha Vantage `TIME_SERIES_DAILY` for daily market data.

Expected market fields:

```text
ticker
date
open
high
low
close
volume
```

Derived during preprocessing:

```text
daily_return
volume_change
```

Drop `adj_close` if it is completely empty.

### Rationale

The selected endpoint does not provide adjusted close, so carrying an all-null column adds no value.

---

## 2026-09-20 — News Provider and Schema

### Decision

Use Marketaux for financial-news ingestion.

Raw news should preserve:

```text
ticker
published_at
title
description
content
source
url
```

### Rationale

Marketaux provides ticker-oriented financial news while keeping the news provider independent from the market-data API.

---

## 2026-09-20 — Basic News Relevance Filtering

### Decision

Apply a lightweight and explainable relevance rule during preprocessing.

```text
2 = target company/ticker appears in the title
1 = target company/ticker appears in description/content
0 = no direct company reference
```

Articles scoring `0` are removed from `news_clean.csv`.

Keep `relevance_score` in the processed news output.

### Rationale

Ticker-oriented APIs can still return weakly related stories. Basic filtering reduces noise before LLM processing without introducing a complex relevance model.

### Boundary

This is a preprocessing quality rule, not a Router Agent decision.

---

## 2026-09-20 — Evidence Assembly

### Decision

Use one canonical daily key:

```text
ticker + date
```

Normalize market dates, SEC transaction dates, and news publication dates to day level before merging.

Use outer-style merges so source-only dates are preserved.

### Final Behavior

- market-only dates are retained
- SEC-only dates are retained
- news-only dates are retained
- `news_count` is `0`, not `NaN`, when no news exists
- duplicate `ticker/date` rows are not allowed

### Output

```text
data/processed/daily_evidence.csv
```

### Rationale

Agents need a complete evidence timeline without silently losing events that do not coincide across all data sources.

---

## 2026-09-20 — News Prompt-Chaining Workflow

### Decision

Implement the news research workflow as three explicit sequential LLM stages:

```text
classify
-> extract
-> summarize
```

Do not collapse the three steps into one prompt.

### Rationale

The assignment requires prompt chaining, and explicit stages make intermediate outputs inspectable and testable.

---

## 2026-09-20 — News Classification Categories

### Decision

Use the following controlled categories:

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

### Important Boundary

The `category` describes **article content**.

It does not decide which specialist agent should receive the evidence. Routing remains the Router Agent's responsibility.

---

## 2026-09-20 — Structured Fact Extraction

### Decision

The extraction stage should produce structured evidence fields:

```text
event
key_facts
people
organizations
financial_numbers
```

The LLM must be instructed to use only information supported by the article and return empty lists when evidence is absent.

### Rationale

Structured evidence is easier for downstream agents and evaluators to inspect than free-form article summaries.

---

## 2026-09-20 — Research Summarization

### Decision

The summarization stage receives the structured extraction from the previous stage rather than independently rereading the task from scratch.

Summaries should:

- identify the main event
- include supported key facts
- explain why the event may matter for company research
- avoid unsupported conclusions
- avoid buy/sell recommendations

### Rationale

This preserves prompt-chain dependency and reduces unsupported generation.

---

## 2026-09-20 — LLM Provider Compatibility

### Decision

Use the OpenAI Python client with an **OpenAI-compatible endpoint** so the project is provider-flexible.

Current development configuration supports OpenRouter:

```text
LLM_API_KEY=your_key
LLM_MODEL=your_model_slug
LLM_BASE_URL=https://openrouter.ai/api/v1
```

### Rationale

This allows the team to change models/providers without rewriting the prompt-chain notebook.

---

## 2026-09-20 — LLM Cost and Resume Controls

### Decision

Use:

```text
NEWS_CHAIN_LIMIT=10
FORCE_NEWS_CHAIN=false
```

during normal development.

Existing results should be reused by URL when possible.

Set `FORCE_NEWS_CHAIN=true` only when intentionally regenerating LLM outputs.

### Rationale

Prompt-chain runs should be resumable and should avoid repeated API cost.

---

## 2026-09-20 — News Research Handoff Schema

### Decision

Save prompt-chain output to:

```text
data/processed/news_research_results.csv
```

Expected fields:

```text
ticker
published_at
title
source
url
relevance_score
category
classification_reason
event
key_facts
people
organizations
financial_numbers
summary
```

### Rationale

This file is the primary structured news handoff to the Planner and Router.

---

## 2026-09-20 — Traceability

### Decision

Preserve the original article `source`, `url`, `title`, and publication time in downstream research records.

### Rationale

The Planner, specialist agents, and Evaluator-Optimizer need to be able to trace generated analysis back to the source evidence.

---

## 2026-09-20 — Quality Checks

### Decision

Preprocessing and prompt-chain notebooks should report validation results.

Minimum data checks include:

- row counts
- missing required fields
- duplicate records
- valid timestamps
- valid relevance scores
- duplicate `ticker/date` evidence rows

Minimum news-chain checks include:

- valid classification categories
- missing categories
- missing events
- missing summaries
- missing URLs
- duplicate URLs
- category distribution
- manual review of a small output sample

### Rationale

Successful code execution alone is not sufficient evidence of pipeline quality.

---

## 2026-09-20 — Documentation and Handoff

### Decision

Maintain:

```text
README.md
notebooks/README.md
data/README.md
src/README.md
docs/handoff.md
docs/decisions.md
```

### Rationale

Each file has a distinct purpose:

- root README: system overview and setup
- notebooks README: execution and handoff order
- data README: data contracts
- src README: reusable modules
- handoff.md: teammate-facing downstream contract
- decisions.md: team-approved technical decisions

---

## 2026-09-20 — Security

### Decision

Never commit `.env` or real API credentials.

Commit `.env.example` with placeholders only.

### Rationale

The repository should remain safe to share and review.

---

## Future Decisions to Record

Add entries here when the team finalizes:

- exact Planner Agent implementation
- exact Router Agent routing rules
- specialist-agent definitions
- evaluator scoring rubric
- evaluator refinement threshold
- memory implementation
- final production LLM model
- final ticker universe
- final end-to-end evaluation design
