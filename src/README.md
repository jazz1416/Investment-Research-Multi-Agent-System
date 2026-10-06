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

## `insider_agent.py`
Insider-transaction specialist agent.

Primary function:

```python
analyze_insider_activity(...)
```

Responsibilities:

- Extract information from Sec For 4 transaction data for ticker

Expected output:

```text
agent = insider_agent
ticker
transaction_count
unique_insiders
acquired_transactions
disposed_transactions
total_transaction_value
start_date
end_date
```

## `market_agent.py`
Market specialist agent.

Primary function:

```python
analyze_market(...)
```

Responsibilities:

- Extract market data for ticker
- Calcuate average daily return and volume

Expected output:

```text
agent = market_agent
ticker
row_count
start_date
end_date
latest_close
latest_volume
average_daily_return
average_volume
```

## `news_agent.py`
News specialist agent.

Primary function:

```python
analyze_news(...)
```

Responsibilities:

- Analyze processed news-research results for a ticker
- Count articles per category
- Store information regarding title, category, event, summary and url for news

Expected output:

```text
agent = news_agent
ticker
article_count
categories
research_notes
```

## `planner.py`
Planner agent.

Primary function:

```python
generate_research_plan(...)
```

Responsibilities:

- Create a structured research plan for a stock ticker
- Conduct news, market, insider, risk and catalyst analysis for a ticker

Expected output:

```text
ticker
objective
research_steps
```

## `router.py`
Router agent.

Primary function:

```python
route_step(...)
```

Responsibilities:

- Route a planner step to the appropriate specialist agent

Expected output:

```text
step_id
task
agent
reason
description
```

## `orchestrator.py`
Orchestrator for multi-agent investment research workflow.

Primary function:

```python
orchestrate_research(...)
```

Responsibilities:

- Run the full planner-router-specialist workflow

Expected output:

```text
ticker
plan
routing_decisions
executed_steps
specialist_results
final_synthesis
```


## `synthesis_agent.py`
Syntehsis specialist.

Primary function:

```python
synthesize_research(...)
```

Responsibilities:

- Combine specialist outputs into structured research conclusions
- Generate summary including news articles, market rows and insider transactions for a ticker

Expected output:

```text
agent
ticker
risks
catalysts
summary
```

## `memory.py`
Manage memory storage across runs.

Functions:

```python
_ensure_dir_exists(...)
_load_memory(...)
_save_memory(...)
get_ticker_memory(...)
save_run(...)
clear_memory(...)
```

Responsibilities:

- Load and save memory directory
- Grab ticker memory
- Save run history
- Clear existing memory
- Enables memory across runs

## `evaluator.py`
Evaluator agent.

Primary function:

```python
evaluate_draft(...)
```

Responsibilities:

- Evaluate incoming drafts through strict requirements hard coded before letting LLM judge draft
- Generate scores for factual grounding, completeness, logical coherence, and clarity and structure out of 10
- Ensure draft has specific headers and source citations
- Ensure draft doesn't contain ellipsis or bracketed placeholders
- LLM as a judge critiques draft based on `EVALUATOR_SYSTEM_PROMPT` returning feedback and scores
- Passes draft only if all hard gates are passed, factual grounding score >= 8 and overall score >= 8


Expected output:

```text
eval_result
```


## `optimizer.py`
Optimizer agent.

Primary function:

```python
optimize_draft(...)
```

Responsibilities:

- Optimize incoming draft based on evaluator feedback
- Use `gpt-40-mini` to improve drafts following strict guidelines from evaluator agent and `OPTIMIZER_SYSTEM_PROMPT`


Expected output:

```text
refined_draft
```

## `eval_opt_workflow.py`
Orchstrates the Evaluator-Optimizer refinement loop.

Primary function:

```python
run_evaluator_optimizer_workflow(...)
```

Responsibilities:

- Get memory context for runs related to a ticker
- Run Evaluator agent on generated draft and send feedback to Optimizer 
- Run up to `max_iterations` loops between Evaluator and Optimizer while logging each run, stopping early if draft passes Evaluator


Expected output:

```text
current_draft
final_eval_result
iteration_history
```


## `research_pipeline.py`
Connect the planner-router orchestration to the evaluator-optimizer workflow.

Primary function:

```python
run_full_research(...)
```

Responsibilities:

- Write initial research draft from data gathered from specialist agents


Expected output:

```text
ticker
orchestration
initial_draft
raw_evidence
final_report
final_evaluation
history
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
