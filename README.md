# Investment Research Multi-Agent System

AAI-520 Final Team Project, Team 9 (University of San Diego, MS in Applied Artificial Intelligence)

This project builds an investment research agent for a given stock ticker. It collects SEC
Form 4 insider transactions, daily market data, and financial news, processes the news with an
LLM prompt chain, plans and routes research tasks to specialist agents, and evaluates and
refines its written analysis using feedback and memory from earlier runs.

The project is for coursework and research purposes only. It does not make trades or give
financial advice.

## Team

| Member | Area | Main work |
|---|---|---|
| Keana Gindlesperger | Data and research pipeline | Data retrieval, preprocessing, evidence assembly, news prompt chain (notebooks 00-03) |
| Rajni Massoun | Agent core | Planner, router, specialist agents, orchestration (notebook 04) |
| Jasmine Duong | Evaluation and memory | Evaluator-optimizer workflow, quality scoring, memory across runs (notebook 05) |

## Project Requirements

| Requirement | Implementation |
|---|---|
| Plans research steps for a stock | `src/planner.py`, notebook 04 |
| Uses tools (APIs, datasets) | API ingestion modules (notebook 00); each specialist agent reads its own dataset (notebook 04) |
| Self-reflects on output quality | `src/evaluator.py`, notebook 05 |
| Learns across runs | `src/memory.py`, notebook 05 |
| Prompt chaining workflow | Notebooks 00-03: ingest, preprocess, classify, extract, summarize |
| Routing workflow | `src/router.py` and `src/orchestrator.py`, notebook 04 |
| Evaluator-optimizer workflow | `src/eval_opt_workflow.py`, notebook 05 |

## Architecture

```text
SEC EDGAR, Alpha Vantage (yfinance fallback), Marketaux
        |
00 Data Ingestion
        |
01 Data Preprocessing
        |
02 Evidence Assembly
        |
03 News Processing Chain (classify -> extract -> summarize)
        |
        +-----------------------------+
        |                             |
04 Planner -> Router               05 Evaluator <-> Optimizer
   -> News / Market / Insider         + memory across runs
   -> Synthesis (risks, catalysts)
```

Notebooks 04 and 05 both read the processed data from notebooks 01-03. Notebook 05 currently
tests the evaluator-optimizer loop on draft reports written in the notebook; connecting the
output of the notebook 04 orchestrator to the notebook 05 workflow is the next step.

## Notebooks

Run the notebooks in order. Each notebook reads the files saved by the earlier ones.

| Notebook | Purpose | Output |
|---|---|---|
| `00_data_ingestion.ipynb` | Retrieve insider transactions, market data, and news | `data/raw/*.csv` |
| `01_data_preprocessing.ipynb` | Clean and validate each source, filter news by relevance | `data/processed/*_clean.csv` |
| `02_evidence_assembly.ipynb` | Combine the three sources by ticker and date | `data/processed/daily_evidence.csv` |
| `03_news_processing_chain.ipynb` | Classify, extract facts from, and summarize each article with an LLM | `data/processed/news_research_results.csv` |
| `04_planner_router_orchestration.ipynb` | Plan, route, run specialist agents, synthesize, and test each component | Displayed results |
| `05_evaluator_optimizer_workflow.ipynb` | Evaluate and refine draft reports, store run history | `data/processed/memory_store.json` |

Data files are not committed to the repository, so notebooks 00-03 need to be run (or the
processed files shared) before notebooks 04 and 05.

### 00 Data Ingestion

| Source | Data |
|---|---|
| SEC EDGAR | Form 4 insider transactions |
| Alpha Vantage | Daily open, high, low, close, volume |
| yfinance | Used for market data if the Alpha Vantage request fails or hits its rate limit |
| Marketaux | Financial news articles |

Existing raw files are reused unless `FORCE_REFRESH=true`.

### 01 Data Preprocessing

Standardizes columns, tickers, dates, and numeric fields, removes duplicates, and calculates
insider transaction values, daily returns, and volume changes. News articles get a relevance
score:

```text
2 = company name or ticker in the title
1 = company name or ticker in the description or content
0 = no direct reference (removed)
```

### 02 Evidence Assembly

Joins market, insider, and news data on `ticker + date`, keeping dates that appear in only one
source.

### 03 News Processing Chain

Each relevant article goes through three LLM steps:

1. Classify into `earnings`, `product_service`, `management`, `regulation_legal`,
   `merger_acquisition`, `analyst_investor`, `macro_market`, or `other`
2. Extract the event, key facts, people, organizations, and financial numbers
3. Summarize into a research note

Articles that were already processed are skipped unless `FORCE_NEWS_CHAIN=true`.

### 04 Planner, Router, and Orchestration

| Component | Role |
|---|---|
| Planner | Creates a six-step plan: news, market, insider, risk, catalyst, and final synthesis |
| Router | Assigns each step to a specialist and records the reason; unrecognized tasks go to synthesis |
| News agent | Article count and category breakdown from `news_research_results.csv` |
| Market agent | Date range, latest close, average daily return and volume from `market_data_clean.csv` |
| Insider agent | Number of transactions, insiders, acquisitions, dispositions, and total value from `sec_form4_clean.csv` |
| Synthesis agent | Rule-based combination of the specialist results into risks and catalysts |
| Orchestrator | Runs the full sequence with `orchestrate_research(ticker)` |

The notebook includes tests for each component, including unknown tasks and tickers with no
data.

### 05 Evaluator-Optimizer and Memory

- The evaluator scores a draft from 1 to 10 on factual grounding, completeness, and clarity.
  A draft passes when the overall score and factual grounding are both 8 or higher.
- The optimizer rewrites the draft using the evaluator's feedback and the raw evidence.
- The workflow repeats evaluation and refinement up to three times or until the draft passes.
- Each run's score and notes are saved by ticker and used as context in later runs.

## Source Modules

| Module | Purpose |
|---|---|
| `shared.py` | Paths, settings, and target tickers |
| `sec_ingestion.py` | SEC Form 4 retrieval and parsing |
| `alpha_vantage_ingestion.py` | Market data retrieval |
| `marketaux_ingestion.py` | News retrieval |
| `evidence.py` | Daily evidence assembly |
| `planner.py` | Planner agent |
| `router.py` | Router agent |
| `news_agent.py`, `market_agent.py`, `insider_agent.py` | Specialist agents |
| `synthesis_agent.py` | Risks and catalysts from specialist results |
| `orchestrator.py` | Planner, router, and specialist workflow |
| `evaluator.py` | LLM-based quality evaluation |
| `optimizer.py` | LLM-based refinement |
| `eval_opt_workflow.py` | Evaluation and refinement loop with memory |
| `memory.py` | Run history stored per ticker |

## Setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/jazz1416/Investment-Research-Multi-Agent-System.git
cd Investment-Research-Multi-Agent-System
uv sync
uv add yfinance
```

`yfinance` is used by notebook 00 but is not yet listed in `pyproject.toml`.

Copy `.env.example` to `.env` and add your own values. Do not commit `.env`.

| Variable | Used in | Description |
|---|---|---|
| `TARGET_TICKERS` | 00 | Comma-separated tickers, e.g. `AAPL` |
| `SEC_USER_AGENT` | 00 | Project name and contact email, required by the SEC |
| `ALPHA_VANTAGE_API_KEY` | 00 | Alpha Vantage key |
| `MARKETAUX_API_KEY` | 00 | Marketaux key |
| `SEC_FORM4_LIMIT`, `NEWS_LIMIT_PER_TICKER`, `MARKETAUX_PAGE_SIZE` | 00 | Ingestion limits |
| `FORCE_REFRESH` | 00 | Set to `true` to download new raw data |
| `LLM_API_KEY`, `LLM_MODEL` | 03, 05 | LLM key and model name |
| `LLM_BASE_URL` | 03, 05 | Leave blank for OpenAI; set it for another OpenAI-compatible provider |
| `NEWS_CHAIN_LIMIT` | 03 | Number of articles processed per run |
| `FORCE_NEWS_CHAIN` | 03 | Set to `true` to reprocess saved articles |

## Development

```bash
uv run ruff format .
uv run ruff check .
```

Code follows PEP 8. Changes go through pull requests into `main`.
