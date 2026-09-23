
"""Insider-transaction specialist agent."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def analyze_insider_activity(
    ticker: str,
    project_root: str | Path = ".",
) -> dict:
    """Analyze SEC Form 4 insider transactions for a ticker."""

    ticker = ticker.upper().strip()
    project_root = Path(project_root)

    insider_path = (
        project_root
        / "data"
        / "processed"
        / "sec_form4_clean.csv"
    )

    if not insider_path.exists():
        raise FileNotFoundError(
            f"SEC Form 4 file not found: {insider_path}"
        )

    insider = pd.read_csv(insider_path)

    ticker_insider = insider[
        insider["ticker"].astype(str).str.upper() == ticker
    ].copy()

    if ticker_insider.empty:
        return {
            "agent": "insider_agent",
            "ticker": ticker,
            "transaction_count": 0,
            "message": f"No insider transactions found for {ticker}.",
        }

    ticker_insider["transaction_date"] = pd.to_datetime(
        ticker_insider["transaction_date"],
        errors="coerce",
        utc=True,
    )

    ticker_insider["transaction_value"] = pd.to_numeric(
        ticker_insider["transaction_value"],
        errors="coerce",
    )

    ticker_insider["shares"] = pd.to_numeric(
        ticker_insider["shares"],
        errors="coerce",
    )

    acquired = ticker_insider[
        ticker_insider["acquired_disposed"] == "A"
    ]

    disposed = ticker_insider[
        ticker_insider["acquired_disposed"] == "D"
    ]

    return {
        "agent": "insider_agent",
        "ticker": ticker,
        "transaction_count": len(ticker_insider),
        "unique_insiders": ticker_insider["owner_name"].nunique(),
        "acquired_transactions": len(acquired),
        "disposed_transactions": len(disposed),
        "total_transaction_value": float(
            ticker_insider["transaction_value"].fillna(0).sum()
        ),
        "start_date": ticker_insider["transaction_date"].min(),
        "end_date": ticker_insider["transaction_date"].max(),
    }
