# Setup

Environment and run instructions for the **Investment Research Multi-Agent System**.

## Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- git
- VS Code with Python + Jupyter extensions recommended

Use uv exclusively; do not create a second conda/venv environment.

## First-time setup

```bash
git clone <repo-url>
cd Investment-Research-Multi-Agent-System
uv sync
```

In VS Code, choose `.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on macOS/Linux as the notebook kernel.

## Configure API access

Copy the template:

Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

macOS/Linux:
```bash
cp .env.example .env
```

Edit `.env` and set:

```text
TARGET_TICKERS=AAPL,MSFT
ALPHA_VANTAGE_API_KEY=<your key>
SEC_USER_AGENT=Investment-Research-Multi-Agent-System your-email@example.com
```

Never commit `.env`.

## Running the project

Run notebooks **in order**:

```text
00_data_ingestion
    ↓
01_data_preprocessing
    ↓
02_evidence_assembly
    ↓
agent workflows
```

### 00 — ingestion
Fetches SEC Form 4 filings, Alpha Vantage daily market data, and Alpha Vantage financial news. Writes:

```text
data/raw/sec_form4.csv
data/raw/market_data.csv
data/raw/news.csv
```

### 01 — preprocessing
Normalizes schemas, dates, tickers, text, numeric fields, and duplicates. Writes cleaned source tables and a run manifest.

### 02 — evidence assembly
Aligns the three sources by ticker/date and writes:

```text
data/processed/daily_evidence.csv
```

## Dependencies

Dependencies are managed through `pyproject.toml` + `uv.lock`. After a teammate changes dependencies:

```bash
git pull
uv sync
```

## Code quality

```bash
uv run ruff check . --fix
uv run ruff format .
uv run ruff check .
```

Notebook `E402` is ignored project-wide because notebooks intentionally add `src/` to `sys.path` before importing shared modules.

## Notebook hygiene

- Imports near the top
- Shared paths/seeds from `src/shared.py`
- Relative paths only
- Restart + Run All before review
- Keep useful outputs; remove noisy debugging
- Never hard-code API keys
- Downstream notebooks use processed artifacts rather than repeating ingestion/cleaning
