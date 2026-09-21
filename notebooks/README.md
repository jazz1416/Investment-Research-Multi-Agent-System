# Notebook Pipeline

Saved files on disk are the handoff contract between stages. Downstream notebooks should load saved outputs rather than repeat upstream work.

## Pipeline

```text
00_data_ingestion.ipynb
-> 01_data_preprocessing.ipynb
-> 02_evidence_assembly.ipynb
-> 03_news_processing_chain.ipynb
-> Planner / Router / Specialist Agents
```

## Notebook Handoff Table

| # | Notebook | Purpose | Reads | Writes |
|---|---|---|---|---|
| 00 | `00_data_ingestion.ipynb` | Retrieve external data | APIs | `data/raw/*.csv` |
| 01 | `01_data_preprocessing.ipynb` | Clean and validate data | `data/raw/*.csv` | cleaned datasets + manifest |
| 02 | `02_evidence_assembly.ipynb` | Align evidence by ticker/date | cleaned datasets | `daily_evidence.csv` |
| 03 | `03_news_processing_chain.ipynb` | Classify -> extract -> summarize | `news_clean.csv` | `news_research_results.csv` |

# 00 - Data Ingestion

Sources:

- SEC EDGAR
- Alpha Vantage
- Marketaux

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
