# Source Modules — Investment Research Multi-Agent System

`src/` is the **modular development implementation** of this project. The final team submission also includes the same 17 component implementations as **visible executable cells** in `notebooks/Investment_Research_Multi_Agent_System_Final.ipynb` so the notebook can run without importing local `src` files.

## Module reference

| Module | Responsibility | Key interface |
|---|---|---|
| `shared.py` | Project paths, seeds, environment configuration | `PATHS`, `ensure_directories()`, `get_target_tickers()` |
| `sec_ingestion.py` | SEC Form 4 discovery, XML parsing | `fetch_form4_transactions(...)` |
| `alpha_vantage_ingestion.py` | OHLCV ingestion | `fetch_daily_market_data(...)` |
| `marketaux_ingestion.py` | Ticker-oriented financial news ingestion | `fetch_financial_news(...)` |
| `evidence.py` | Ticker/day outer-join evidence table | `assemble_daily_evidence(...)` |
| `memory.py` | Persistent per-ticker run history | `ResearchMemoryStore` |
| `planner.py` | Select research steps based on available sources | `generate_research_plan(...)` |
| `router.py` | Route tasks to agent names | `route_step(...)` |
| `market_agent.py` | Market metrics specialist | `analyze_market(...)` |
| `news_agent.py` | Structured news specialist | `analyze_news(...)` |
| `insider_agent.py` | SEC insider specialist | `analyze_insider_activity(...)` |
| `synthesis_agent.py` | Combine specialist signals into risks and catalysts | `synthesize_research(...)` |
| `orchestrator.py` | Execute planner/router/selected specialists | `orchestrate_research(...)` |
| `evaluator.py` | Hard gates and LLM-based evaluation | `evaluate_draft(...)`, `EvaluationResult` |
| `optimizer.py` | Evidence-guided LLM report revision | `optimize_draft(...)` |
| `eval_opt_workflow.py` | Evaluate–refine loop and memory | `run_evaluator_optimizer_workflow(...)` |
| `research_pipeline.py` | Draft/evidence assembly and end-to-end connection | `build_research_draft(...)`, `build_raw_evidence(...)`, `run_full_research(...)` |

The **news classify → extract → summarize** prompt chain and the source-specific preprocessing transformations are implemented in the original notebooks and embedded workflow cells; they are not all separate `src` modules.

## Inputs and handoffs

The specialist agents read files from `data/processed/`:

- `market_data_clean.csv`: market OHLCV plus calculated returns and volume changes
- `sec_form4_clean.csv`: insider transactions and derived values
- `news_research_results.csv`: categorized articles, structured facts, summaries, original URLs

The evidence assembly stage saves `daily_evidence.csv`; the evaluator and optimizer use formatted ticker-specific evidence, and memory writes per-ticker run history when configured. See [`docs/handoff.md`](../docs/handoff.md).

## Agent separation

**Planner** selects the analysis stages based on available evidence. **Router** selects the specialist function; the news *classification category* describes article content and does **not** determine tool routing. **Specialists** compute evidence-based summaries; **Synthesis** combines them. **Evaluator** measures report quality using checks and an LLM; **Optimizer** revises the draft in response to feedback, with iteration limits and memory.

## Standalone integration notes

- Do not import `src` from the final notebook. Its implementations are defined directly in cells, in dependency order.
- The integrated notebook uses adjusted internal names where necessary to avoid collisions between module-level globals. If you edit the modular implementation, make the same intentional change in the standalone notebook to avoid divergence.
- The final notebook bounds evidence sent to LLMs for cost reasons. This sampling is an integration choice; **it does not replace the complete persisted evidence tables**.
- Configure API keys and models through `.env` and never commit credentials.
- End-to-end LLM execution requires provider access and credits; passing Python syntax checks does not prove report correctness.

The root README documents setup; `notebooks/README.md` explains the final notebook and original seven development notebooks.
