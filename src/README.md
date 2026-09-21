# Source Modules

The `src/` directory contains reusable project logic.

Notebooks should orchestrate workflows and display results. Reusable ingestion, transformation, and agent-support logic should live here when it needs to be imported by multiple components.

## `shared.py`

Shared project configuration and utilities.

Common imports may include:

```python
PATHS
SEED
ensure_directories
get_target_tickers
```

## `sec_ingestion.py`

Handles SEC EDGAR Form 4 retrieval and parsing.

Primary function:

```python
fetch_form4_transactions(...)
```

Flow:

```text
ticker
-> issuer CIK
-> recent Form 4 filings
-> filing directory
-> ownership XML
-> parsed transactions
```

## `alpha_vantage_ingestion.py`

Handles market-data retrieval from Alpha Vantage.

Primary function:

```python
fetch_daily_market_data(...)
```

Expected output:

```text
ticker
date
open
high
low
close
volume
```

## `marketaux_ingestion.py`

Handles financial-news retrieval from Marketaux.

Primary function:

```python
fetch_financial_news(...)
```

Expected output:

```text
ticker
published_at
title
description
content
source
url
```

Relevance filtering occurs later during preprocessing.

## `evidence.py`

Primary function:

```python
assemble_daily_evidence(...)
```

Responsibilities:

- normalize source dates
- align by `ticker + date`
- aggregate news by date
- aggregate insider transactions by date
- preserve source-only dates
- fill `news_count` with zero when no news exists
- sort the final evidence table

Primary output:

```text
data/processed/daily_evidence.csv
```

## `news_pipeline.py`

Recommended reusable module for the news prompt chain.

Recommended functions:

```python
classify_article(...)
extract_article_facts(...)
summarize_article(...)
run_news_chain(...)
```

`run_news_chain(...)` should coordinate:

```text
classify
-> extract
-> summarize
```

# Architecture Principle

Reusable logic should live in `src/`.

Notebooks should primarily:

```text
load
-> call reusable functions
-> validate
-> display
-> save
```

This lets Planner, Router, specialist, and Evaluator components reuse the same functions.

# Responsibility Boundary

Planner, Router, specialist coordination, evaluator-optimizer logic, and memory should remain in their own modules rather than being added to ingestion files.
