# Notebook Pipeline

Saved files on disk are the handoff contract between stages. Downstream notebooks should load saved outputs rather than repeat upstream work.

## Pipeline

```text
00_data_ingestion.ipynb
-> 01_data_preprocessing.ipynb
-> 02_evidence_assembly.ipynb
-> 03_news_processing_chain.ipynb
-> 04_planner_router_orchestration.ipynb
-> 05_evaluator_optimizer_workflow.ipynb
-> 06_full_research_workflow.ipynb
```

## Notebook Handoff Table

| # | Notebook | Purpose | Reads | Writes |
|---|---|---|---|---|
| 00 | `00_data_ingestion.ipynb` | Retrieve external data | APIs | `data/raw/*.csv` |
| 01 | `01_data_preprocessing.ipynb` | Clean and validate data | `data/raw/*.csv` | cleaned datasets + manifest |
| 02 | `02_evidence_assembly.ipynb` | Align evidence by ticker/date | cleaned datasets | `daily_evidence.csv` |
| 03 | `03_news_processing_chain.ipynb` | Classify -> extract -> summarize | `news_clean.csv` | `news_research_results.csv` |
| 04 | `04_planner_router_orchestration.ipynb` | Test agent routing | cleaned datasets |
| 05 | `05_evaluator_optimizer_workflow.ipynb` | Memory -> Evaluate -> Optimize | cleaned datasets | `agent_memory.json` |
| 06 | `06_full_research_workflow.ipynb` | Generate -> Evaluate -> Optimize | cleaned datasets |

# 00 - Data Ingestion

Sources:

- SEC EDGAR
- Alpha Vantage
- Marketaux
- yfinance

Outputs:

```text
data/raw/sec_form4.csv
data/raw/market_data.csv
data/raw/news.csv
```

Use `FORCE_REFRESH=true` only when fresh source data is intentionally required.

# 01 - Data Preprocessing

SEC flow:

```text
normalize columns
-> normalize ticker
-> parse transaction dates
-> convert numeric fields
-> calculate transaction value
-> remove invalid rows
-> remove duplicates
```

Market flow:

```text
normalize columns
-> normalize ticker
-> parse date
-> convert OHLCV fields
-> remove duplicates
-> calculate daily_return
-> calculate volume_change
```

News flow:

```text
normalize columns
-> normalize ticker
-> parse published_at
-> clean text
-> remove duplicates
-> build combined text
-> assign relevance_score
-> remove score-0 articles
```

Relevance rule:

```text
2 = company/ticker appears in title
1 = company/ticker appears in description/content
0 = no direct company reference
```

Outputs:

```text
data/processed/sec_form4_clean.csv
data/processed/market_data_clean.csv
data/processed/news_clean.csv
data/processed/preprocessing_manifest.json
```

# 02 - Evidence Assembly

Uses `ticker + date` as the canonical daily key.

Outer-style joins preserve market-only, SEC-only, and news-only dates.

Output:

```text
data/processed/daily_evidence.csv
```

# 03 - News Processing Chain

Workflow:

```text
news_clean.csv
-> CLASSIFY
-> category
-> EXTRACT
-> structured facts
-> SUMMARIZE
-> research record
```

Supported categories:

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

Structured extraction fields:

```text
event
key_facts
people
organizations
financial_numbers
```

Output:

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

When `FORCE_NEWS_CHAIN=false`, already processed URLs are reused/skipped.

Quality checks include missing categories, missing summaries, missing URLs, duplicate URLs, invalid categories, and category distribution.

## 04 - Planner Router Orchestration
Tests planning and routing layers.

Workflow:

```text
PLAN
-> ROUTE
-> run specialist
-> synthesize
```


## 05 - Evaluator Optimizer Workflow
Tests Evaluator-Optimizer workflow and generates memory.

Workflow:

```text
draft
-> EVALUATE
-> OPTIMIZE till passes or `max_iterations` reached
-> save final draft and run history
-> output final draft
```


## 06 - Full Research Workflow
Test full workflow with initial draft generation

Workflow:

```text
plan
-> route
-> specialist agents
-> synthesis
-> build research draft
-> evaluate
-> refine
-> memory
```



## Handoff Boundary

Notebook 03 completes:

```text
ingest
-> preprocess
-> classify
-> extract
-> summarize
```

It does not implement Planner behavior, Router behavior, specialist coordination, evaluator refinement, or cross-run memory.

Notebook 04 completes:

```text
routing
planner
specialist coordinator
```
It does not implement Evaluator behavior, Optimizer behavior, or cross-run memory.

Notebook 05 completes:

```text
memory
evaluator
optimizer
```
It does not implement the creation of the initial draft.
