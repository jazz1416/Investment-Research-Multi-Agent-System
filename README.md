# Investment Research Multi-Agent System

## Project Overview

This project builds an agentic financial research system that combines structured and unstructured financial evidence to support multi-agent analysis.

The system integrates SEC Form 4 insider transaction data, daily stock market price and volume data, financial news, LLM-based news classification/fact extraction/summarization, Planner and Router agents, specialist research agents, Evaluator-Optimizer refinement, and memory across workflow runs.

The system is designed for financial research and educational analysis. It does not execute trades or guarantee investment outcomes.

## Team Responsibilities

### Keana - Data + Preprocessing + Research Pipeline

- Retrieve SEC, market, and financial-news data
- Clean and preprocess source data
- Normalize dates, tickers, and numeric fields
- Remove duplicate records
- Apply basic financial-news relevance filtering
- Build combined daily evidence
- Build the news prompt chain: classify -> extract -> summarize
- Test data quality and research outputs
- Produce standardized handoff files for downstream agents
- Document the data and research pipeline

### Rajni - Agentic AI Core

- Build the Planner Agent
- Build the Router Agent
- Implement tool selection
- Coordinate specialist agents
- Connect agent workflows
- Demonstrate autonomous planning and routing
- Document the agent architecture

### Jasmine - Workflow + Evaluation + Memory

- Implement the Evaluator-Optimizer workflow
- Build self-reflection and quality scoring
- Refine outputs using evaluator feedback
- Implement memory across workflow runs
- Test end-to-end workflows
- Document evaluation results

## System Architecture

```text
SEC EDGAR -----------+
Alpha Vantage -------+--> 00 Data Ingestion
Marketaux -----------+
                         |
                         v
                  01 Data Preprocessing
                         |
                         v
                News Relevance Filtering
                         |
                         v
                  02 Evidence Assembly
                         |
                         v
             03 News Processing Chain
                         |
                         v
              classify -> extract -> summarize
                         |
                         v
               Structured Research Evidence
                         |
                         v
                    Planner Agent
                         |
                         v
                     Router Agent
                         |
                         v
                Specialist Agent(s)
                         |
                         v
                 Evaluator-Optimizer
                         |
                         v
                    Refined Output
```

## Data Sources

| Source | Purpose | Raw Output |
|---|---|---|
| SEC EDGAR | Form 4 insider transactions | `data/raw/sec_form4.csv` |
| Alpha Vantage | Daily OHLCV market data | `data/raw/market_data.csv` |
| Marketaux | Financial news | `data/raw/news.csv` |

## Notebook Pipeline

```text
00_data_ingestion.ipynb
-> 01_data_preprocessing.ipynb
-> 02_evidence_assembly.ipynb
-> 03_news_processing_chain.ipynb
```

Notebook 00 only needs to be rerun when fresh external data is required.

### 00 Data Ingestion

Outputs:

```text
data/raw/sec_form4.csv
data/raw/market_data.csv
data/raw/news.csv
```

When `FORCE_REFRESH=false`, existing raw snapshots are reused.

### 01 Data Preprocessing

Major steps:

- normalize column names
- normalize tickers
- parse timestamps
- convert numeric fields
- remove duplicates
- calculate SEC transaction values
- calculate market returns and volume changes
- build combined news text
- apply basic news relevance filtering
- run data-quality checks

Outputs:

```text
data/processed/sec_form4_clean.csv
data/processed/market_data_clean.csv
data/processed/news_clean.csv
data/processed/preprocessing_manifest.json
```

### 02 Evidence Assembly

Aligns SEC, market, and news evidence using `ticker + date`.

Output:

```text
data/processed/daily_evidence.csv
```

### 03 News Processing Chain

Implements:

```text
relevant article
-> classify
-> extract
-> summarize
```

Output:

```text
data/processed/news_research_results.csv
```

## News Relevance Filtering

```text
2 = company name or ticker appears in the title
1 = company name or ticker appears in description/content
0 = no direct company reference
```

Articles scoring 0 are excluded from the cleaned news dataset.

## News Research Categories

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

These labels describe article content. They are not Router Agent decisions.

## Key Processed Outputs

```text
data/processed/sec_form4_clean.csv
data/processed/market_data_clean.csv
data/processed/news_clean.csv
data/processed/daily_evidence.csv
data/processed/news_research_results.csv
data/processed/preprocessing_manifest.json
```

Primary downstream handoffs:

```text
data/processed/daily_evidence.csv
data/processed/news_research_results.csv
```

## Environment Setup

```bash
uv sync
uv run jupyter lab
```

In VS Code, select:

```text
.venv\Scripts\python.exe
```

## Environment Variables

Create `.env` from `.env.example`. Never commit `.env`.

Current configuration includes:

```text
TARGET_TICKERS
ALPHA_VANTAGE_API_KEY
MARKETAUX_API_KEY
SEC_USER_AGENT
SEC_FORM4_LIMIT
NEWS_LIMIT_PER_TICKER
MARKETAUX_PAGE_SIZE
FORCE_REFRESH
LLM_API_KEY
LLM_MODEL
LLM_BASE_URL
NEWS_CHAIN_LIMIT
FORCE_NEWS_CHAIN
```

## Development Commands

```bash
uv run ruff format .
uv run ruff check .
```

## Reproducibility

If raw source files already exist:

```text
01_data_preprocessing.ipynb
-> 02_evidence_assembly.ipynb
-> 03_news_processing_chain.ipynb
```

is the normal development sequence.

## Security

Never commit `.env`, API keys, passwords, or access tokens.

## Project Scope

The system supports structured financial research and demonstrates agentic AI workflows. It does not execute trades, automatically place investments, guarantee returns, or replace professional financial advice.
