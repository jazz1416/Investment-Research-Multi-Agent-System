
"""News specialist agent."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def analyze_news(ticker: str, project_root: str | Path = ".") -> dict:
    """Analyze processed news-research results for a ticker."""

    ticker = ticker.upper().strip()
    project_root = Path(project_root)

    news_path = (
        project_root
        / "data"
        / "processed"
        / "news_research_results.csv"
    )

    if not news_path.exists():
        raise FileNotFoundError(
            f"News research file not found: {news_path}"
        )

    news = pd.read_csv(news_path)

    ticker_news = news[
        news["ticker"].astype(str).str.upper() == ticker
    ].copy()

    if ticker_news.empty:
        return {
            "agent": "news_agent",
            "ticker": ticker,
            "article_count": 0,
            "categories": {},
            "research_notes": [],
            "message": f"No processed news found for {ticker}.",
        }

    category_counts = (
        ticker_news["category"]
        .value_counts()
        .to_dict()
    )

    research_notes = ticker_news[
        [
            "title",
            "category",
            "event",
            "summary",
            "url",
        ]
    ].to_dict(orient="records")

    return {
        "agent": "news_agent",
        "ticker": ticker,
        "article_count": len(ticker_news),
        "categories": category_counts,
        "research_notes": research_notes,
    }
