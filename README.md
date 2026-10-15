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
