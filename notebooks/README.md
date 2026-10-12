# Notebooks — Final Submission and Development Workflow

## Primary final submission

Open **`Investment_Research_Multi_Agent_System_Final.ipynb`**. This notebook embeds the 17 originally modular `src` implementations directly as visible, executable Python cells and then executes the seven research workflow stages. It does **not** require `from src...` imports or hidden registration of the source code.

Run in cell order from the project repository root with Python 3.12 and the environment configured as described in the [root README](../README.md). The notebook writes files to `data/raw/` and `data/processed/`; those files are still used as handoffs within the integrated run.

## Original development notebooks (reference)

These seven separately maintained notebooks document the original team development process. They are **not required in addition to the standalone submission**.

| Original notebook | Stage | Main output |
|---|---|---|
| `00_data_ingestion.ipynb` | Ingest external APIs | `data/raw/{sec_form4,market_data,news}.csv` |
| `01_data_preprocessing.ipynb` | Clean, normalize, filter relevance | cleaned CSV files, manifest |
| `02_evidence_assembly.ipynb` | Merge sources on ticker/date | `daily_evidence.csv` |
| `03_news_processing_chain.ipynb` | Classify → extract → summarize | `news_research_results.csv` |
| `04_planner_router_orchestration.ipynb` | Plan, route, specialists, synthesize | in-notebook research results |
| `05_evaluator_optimizer_workflow.ipynb` | Score, refine, track memory | evaluation history and memory |
| `06_full_research_workflow.ipynb` | Integrate research and evaluation | final report and history |

For separate development notebooks, run **00 → 01 → 02 → 03 → 04 → 05 → 06**. The 06 notebook also performs full research integration and therefore may repeat some work performed during stage-specific testing; reserve stage 05 for isolated testing.

## Final notebook layout

1. Environment setup and 17 source implementation sections
2. Ingestion and snapshot reuse
3. Data preprocessing and quality checks
4. Daily evidence assembly
5. News LLM prompt chaining and resume behavior
6. Planner, router, specialist agents, and synthesis
7. Draft creation and source-grounded evidence
8. Evaluator–optimizer, final outputs, and memory

## Practical usage and limitations

- Ingestion calls SEC, Alpha Vantage (with yfinance fallback), and Marketaux; costs or rate limits may apply.
- Configure `.env` at the project root; never share API keys. With `FORCE_REFRESH=false`, previous raw snapshots are reused when present.
- With `FORCE_NEWS_CHAIN=false`, the news chain reuses already processed URLs where supported. Default `NEWS_CHAIN_LIMIT=10` reduces cost.
- The final integrated evidence context is **bounded** (12 daily rows, 10 news rows, ~25,000 characters). This makes API calls cheaper but means LLM fact-checking is not exhaustive.
- Keep the project kernel and working directory consistent. **Restart Kernel → Run All** after editing `.env` or code.
- The complete live run still requires source access and sufficient LLM credits. Distinguish notebook syntax validation from end-to-end runtime verification.

The persisted CSV files remain the interface between data processing, specialist agents, and evaluation even though the code is now visible inside a single notebook.
