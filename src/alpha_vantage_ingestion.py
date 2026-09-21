from __future__ import annotations

from typing import Any

import pandas as pd
import requests

BASE_URL = "https://www.alphavantage.co/query"


def _request(params: dict[str, Any], api_key: str) -> dict[str, Any]:
    response = requests.get(
        BASE_URL,
        params={**params, "apikey": api_key},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()

    for key in ("Error Message", "Information", "Note"):
        if key in payload:
            raise RuntimeError(payload[key])

    return payload


def fetch_daily_market_data(
    tickers: list[str],
    api_key: str,
) -> pd.DataFrame:
    """Fetch compact daily OHLCV data."""
    rows: list[dict[str, Any]] = []

    for ticker in tickers:
        symbol = ticker.strip().upper()

        payload = _request(
            {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": "compact",
            },
            api_key,
        )

        for date, values in payload.get("Time Series (Daily)", {}).items():
            rows.append(
                {
                    "ticker": symbol,
                    "date": date,
                    "open": values.get("1. open"),
                    "high": values.get("2. high"),
                    "low": values.get("3. low"),
                    "close": values.get("4. close"),
                    "volume": values.get("5. volume"),
                }
            )

    return pd.DataFrame(rows)
