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

All three team members contributed to the final notebook report sections and final submission verification.

## Project Requirements

| Requirement | Implementation |
|---|---|
| Plans research steps for a stock | `src/planner.py` (decides steps from the available data), notebook 04 |
| Uses tools (APIs, datasets) | API ingestion modules (notebook 00); each specialist agent reads its own dataset (notebook 04) |
| Self-reflects on output quality | `src/evaluator.py`, notebooks 05 and 06 |
| Learns across runs | `src/memory.py`, notebook 05 |
| Prompt chaining workflow | Notebooks 00-03: ingest, preprocess, classify, extract, summarize |
| Routing workflow | `src/router.py` and `src/orchestrator.py`, notebook 04 |
| Evaluator-optimizer workflow | `src/eval_opt_workflow.py`, notebooks 05 and 06 |

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
        |
04 Planner -> Router -> News / Market / Insider -> Synthesis
        |
06 Draft report from the agent results
        |
05 Evaluator <-> Optimizer, with memory across runs
```

Notebook 04 tests the agents, notebook 05 tests the evaluator-optimizer and memory, and
notebook 06 connects them so the whole system runs as one flow.

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
| `06_full_research_workflow.ipynb` | Run the full flow: agents, draft report, evaluate, refine, memory | `data/processed/memory_store.json` |

Data files are not committed to the repository, so notebooks 00-03 need to be run (or the
processed files shared) before notebooks 04-06.

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
| Planner | Checks how much news, market, and insider data the ticker has, skips sources with no data, and saves the reason for each decision |
| Router | Assigns each step to a specialist and records the reason; unrecognized tasks go to synthesis |
| News agent | Article count and category breakdown from `news_research_results.csv` |
| Market agent | Date range, latest close, average daily return and volume from `market_data_clean.csv` |
| Insider agent | Number of transactions, insiders, acquisitions, dispositions, and total value from `sec_form4_clean.csv` |
| Synthesis agent | Rule-based combination of the specialist results into risks and catalysts |
| Orchestrator | Runs the full sequence with `orchestrate_research(ticker)` and only calls the agents the plan needs |

The notebook includes tests for each component, including unknown tasks and tickers with no
data.

### 05 Evaluator-Optimizer and Memory

- The evaluator scores a draft from 1 to 10 on factual grounding, completeness, and clarity.
  A draft passes when the overall score and factual grounding are both 8 or higher.
- Evaluator runs on a hybrid model of coded strict guidelines and using an LLM as a judge only if guidelines pass.
- The optimizer rewrites the draft using the evaluator's feedback and the raw evidence.
- The workflow repeats evaluation and refinement up to three times or until the draft passes.
- Each run's score and notes are saved by ticker and used as context in later runs.

### 06 Full Research Workflow

Connects notebook 04 to notebook 05. `src/research_pipeline.py` turns the orchestrator's results
into a written draft, collects the raw evidence, and runs the evaluate-and-refine loop with
memory using `run_full_research(ticker)`.

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
| `evaluator.py` | Hybrid LLM-based quality evaluation |
| `optimizer.py` | LLM-based refinement |
| `eval_opt_workflow.py` | Evaluation and refinement loop with memory |
| `memory.py` | Run history stored per ticker |
| `research_pipeline.py` | Connects the orchestrator to the evaluator-optimizer workflow |

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
# Investment Research Multi-Agent System

**AAI-520 Final Team Project · Team 9 · University of San Diego · MS in Applied Artificial Intelligence**

## Project overview

This project develops a multi-agent financial research assistant that collects market prices, SEC insider disclosures, and financial news for selected stock tickers. It prepares structured evidence, processes news through an explicit LLM prompt chain, dynamically plans and routes research tasks, synthesizes observations, and evaluates/refines draft reports with a feedback loop and persistent memory.

**Purpose:** educational research and demonstration. It does not execute trades, provide personalized investment recommendations, or guarantee financial accuracy.

## Team contributions

| Team member | Responsibility | Contributions |
|---|---|---|
| Keana Gindlesperger | Data and research pipeline | API ingestion, preprocessing, relevance filtering, evidence assembly, news classification → extraction → summarization, data quality checks |
| Rajni Massoun | Agentic AI core | Planner, router, market/news/insider specialist agents, orchestration, evidence-based synthesis |
| Jasmine Duong | Evaluation and memory | Evaluator, optimizer, iterative quality assessment, persistent per-ticker research memory, integration testing |

The final single-notebook integration brings these components together while preserving the team's original functional boundaries.

## Deliverables and how to run

**Recommended final submission:** `notebooks/Investment_Research_Multi_Agent_System_Final.ipynb` — a **self-contained notebook containing the implementations of all 17 `src` modules as visible executable cells**, followed by the integrated workflow. It does not import a separate local `src/` package; `src/` remains available in the original repository for reuse and inspection.

The seven development notebooks are documented in `notebooks/README.md`. The original modular layout may be retained in the team's repository; the standalone notebook is the easiest entry point for demonstration.

### Requirements

- Python 3.12 and JupyterLab (the team uses [`uv`](https://docs.astral.sh/uv/))
- Libraries supplied by the project's `pyproject.toml`/lockfile where available; commonly `pandas`, `numpy`, `requests`, `python-dotenv`, `openai`, `pydantic`, `yfinance`, `ipykernel`, and Jupyter
- Network access and valid provider credentials **only** when fetching data or running the LLM stages
- Adequate OpenRouter/provider credits and an appropriate supported chat model

For a cloned original repository:

```bash
uv sync
uv run jupyter lab
```

If `yfinance` is not declared in the dependency manifest, add it to the project dependencies before running ingestion (`uv add yfinance`). Open the final notebook at the **repository root** so that relative `data/` outputs are created in the expected location. Select the project's Python environment kernel.

### Environment variables

Create `.env` in the project root, copying `.env.example` if present. Never commit real keys.

```dotenv
TARGET_TICKERS=AAPL
SEC_USER_AGENT=Investment-Research-Multi-Agent-System contact@example.com
ALPHA_VANTAGE_API_KEY=your_key
MARKETAUX_API_KEY=your_key
LLM_API_KEY=your_openrouter_or_other_provider_key
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4.1-mini
FORCE_REFRESH=false
FORCE_NEWS_CHAIN=false
NEWS_CHAIN_LIMIT=10
```

The model shown is a **configuration example**, not a guarantee of availability, provider compatibility, or identical results. Other optional limits include `SEC_FORM4_LIMIT`, `NEWS_LIMIT_PER_TICKER`, and `MARKETAUX_PAGE_SIZE`.

### Execution

1. Open `notebooks/Investment_Research_Multi_Agent_System_Final.ipynb` in JupyterLab (working directory should resolve to the project root).
2. Confirm the `.env` file, provider keys, network connectivity, and ticker settings.
3. **Restart Kernel → Run All Cells** in order. Source implementations must be defined before workflow cells.
4. Review preprocessing quality checks, article-level prompt-chain results, routing decisions, evaluation scores, revised reports, and saved outputs.
5. For reruns, keep `FORCE_REFRESH=false` and `FORCE_NEWS_CHAIN=false` to reuse saved data and limit API costs; turn either on only when intentionally refreshing its stage.

A fresh run without saved data requires functioning upstream APIs; a cached run requires the corresponding `data/raw/` and `data/processed/` CSV files. Evaluation/refinement still uses paid or rate-limited LLM calls.

## Architecture

```text
SEC EDGAR (Form 4)     Alpha Vantage / yfinance     Marketaux (news)
          \                    |                      /
                   Ingestion (00)
                        |
          Preprocessing + relevance filtering (01)
                        |
            Daily evidence assembly (02)
                        |
    News prompt chain: classify → extract → summarize (03)
                        |
       Planner → Router → Specialist agents (04)
                        |
                Research synthesis
                        |
                 Draft generation (06)
                        |
      Evaluator ⇄ Optimizer (05), per-ticker memory
                        |
               Final research report
```

The project demonstrates **prompt chaining**, **routing**, and **evaluator–optimizer** agentic patterns. The planner selects steps based on available evidence; the router dispatches those steps to specialized analytic functions. The evaluator uses programmatic gates alongside an LLM-based quality assessment, and the optimizer revises drafts until the threshold or iteration limit is reached.

## Saved data and outputs

| File | Purpose |
|---|---|
| `data/raw/sec_form4.csv` | Original SEC Form 4 transaction data |
| `data/raw/market_data.csv` | Market OHLCV data |
| `data/raw/news.csv` | Financial-news articles |
| `data/processed/sec_form4_clean.csv` | Clean insider transactions |
| `data/processed/market_data_clean.csv` | Clean market data, including derived returns |
| `data/processed/news_clean.csv` | Relevant and cleaned news |
| `data/processed/daily_evidence.csv` | Ticker/date-aligned multi-source evidence |
| `data/processed/news_research_results.csv` | Classified, extracted, summarized articles |
| `data/processed/preprocessing_manifest.json` | Preprocessing audit information |
| `data/processed/memory_store.json` | Cross-run evaluator scores/notes per ticker (where configured) |

Actual files are generated when stages execute. The repository may omit source data or results to protect credentials, respect source terms, and keep submission size manageable.

## Reliability, cost, and limitations

- **Bounded evidence for the LLM:** the final notebook samples up to **12 recent daily records** and **10 recent news records**, truncates individual text fields, and caps formatted evidence at approximately **25,000 characters** to control prompt size. Full CSV datasets remain on disk. This is a *sampled evaluation context*, not exhaustive verification of every raw record.
- **Token-budget controls:** the news chain and evaluator/optimizer use output limits to reduce OpenRouter errors and costs. Models can still exhaust reasoning tokens or refuse/return empty content; live success depends on provider and configuration.
- **Refinement limit:** development settings use a bounded iteration count (commonly 2). Quality passing is not guaranteed.
- **Evidence provenance:** article URLs and dates are retained; generated analysis should be verified against the primary source before use.
- **Data recency and coverage:** free-tier limits, API outages, incomplete SEC coverage, and filtering can affect results. No trading, prediction guarantee, or investment advice is provided.
- **Validation status:** notebook structure and parsing checks are not a substitute for a full end-to-end live run with all credentials. Do not represent live integration as confirmed without a successful recorded run.

## Documentation

- [`notebooks/README.md`](notebooks/README.md) — notebook execution sequence, standalone/development distinction
- [`src/README.md`](src/README.md) — modular source components and boundaries
- [`docs/handoff.md`](docs/handoff.md) — output contracts, team integration, reproduction checklist
- [`docs/decisions.md`](docs/decisions.md) — technical decisions, including final integration updates

## Academic and responsible-use note

This is a course demonstration, not a financial advisory product. An LLM evaluation score is an internal rubric output rather than independent proof that the report is accurate. API credentials and private data should never be committed to version control.
