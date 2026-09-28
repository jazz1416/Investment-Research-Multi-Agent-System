
"""Market specialist agent."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def analyze_market(ticker: str, project_root: str | Path = ".") -> dict:
    """Analyze processed market evidence for a ticker."""

    ticker = ticker.upper().strip()
    project_root = Path(project_root)

    market_path = (
        project_root
        / "data"
        / "processed"
        / "market_data_clean.csv"
    )

    if not market_path.exists():
        raise FileNotFoundError(
            f"Market data file not found: {market_path}"
        )

    market = pd.read_csv(market_path)

    ticker_market = market[
        market["ticker"].astype(str).str.upper() == ticker
    ].copy()

    if ticker_market.empty:
        return {
            "agent": "market_agent",
            "ticker": ticker,
            "row_count": 0,
            "message": f"No market data found for {ticker}.",
        }

    ticker_market["date"] = pd.to_datetime(
        ticker_market["date"],
        errors="coerce",
        utc=True,
    )

    ticker_market = ticker_market.sort_values("date")

    latest = ticker_market.iloc[-1]

    average_return = ticker_market["daily_return"].mean()
    average_volume = ticker_market["volume"].mean()

    return {
        "agent": "market_agent",
        "ticker": ticker,
        "row_count": len(ticker_market),
        "start_date": ticker_market["date"].min(),
        "end_date": ticker_market["date"].max(),
        "latest_close": float(latest["close"]),
        "latest_volume": float(latest["volume"]),
        "average_daily_return": float(average_return),
        "average_volume": float(average_volume),
    }
