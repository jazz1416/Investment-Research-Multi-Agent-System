"""Marketaux financial-news ingestion helpers."""

from __future__ import annotations

import math
import time
from typing import Any

import pandas as pd
import requests

BASE_URL = "https://api.marketaux.com/v1/news/all"


def _request(params: dict[str, Any], api_token: str) -> dict[str, Any]:
    response = requests.get(
        BASE_URL,
        params={**params, "api_token": api_token},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()

    meta = payload.get("meta", {})
    if meta.get("code"):
        raise RuntimeError(
            meta.get("message")
            or f"Marketaux error: {meta.get('code')}"
        )

    return payload


def fetch_financial_news(
    tickers: list[str],
    api_token: str,
    limit_per_ticker: int = 9,
    page_size: int = 3,
    pause_seconds: float = 0.5,
) -> pd.DataFrame:
    """Fetch recent financial news with pagination."""
    rows: list[dict[str, Any]] = []

    for ticker in tickers:
        symbol = ticker.strip().upper()
        ticker_rows: list[dict[str, Any]] = []
        pages_needed = math.ceil(limit_per_ticker / page_size)

        for page in range(1, pages_needed + 1):
            remaining = limit_per_ticker - len(ticker_rows)
            if remaining <= 0:
                break

            payload = _request(
                {
                    "symbols": symbol,
                    "filter_entities": "true",
                    "language": "en",
                    "limit": min(page_size, remaining),
                    "page": page,
                },
                api_token,
            )

            articles = payload.get("data", [])
            if not articles:
                break

            for article in articles:
                ticker_rows.append(
                    {
                        "ticker": symbol,
                        "published_at": article.get("published_at"),
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "content": (
                            article.get("snippet")
                            or article.get("description")
                        ),
                        "source": article.get("source"),
                        "url": article.get("url"),
                    }
                )

                if len(ticker_rows) >= limit_per_ticker:
                    break

            if page < pages_needed:
                time.sleep(pause_seconds)

        rows.extend(ticker_rows[:limit_per_ticker])

    return pd.DataFrame(rows)
