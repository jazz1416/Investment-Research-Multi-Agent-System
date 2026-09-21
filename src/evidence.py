from __future__ import annotations

import pandas as pd


def assemble_daily_evidence(
    market: pd.DataFrame,
    news: pd.DataFrame,
    sec: pd.DataFrame,
) -> pd.DataFrame:
    """Create one ticker/date evidence table without making investment judgments."""
    market = market.copy()
    news = news.copy()
    sec = sec.copy()

    market["date"] = pd.to_datetime(market["date"], utc=True).dt.normalize()
    news["date"] = pd.to_datetime(news["published_at"], utc=True).dt.normalize()
    sec["date"] = pd.to_datetime(sec["transaction_date"], utc=True).dt.normalize()

    news_daily = (
        news.groupby(["ticker", "date"], dropna=False)
        .agg(
            news_count=("title", "size"),
            news_titles=("title", lambda values: " || ".join(values.dropna().astype(str).head(10))),
            news_urls=("url", lambda values: " || ".join(values.dropna().astype(str).head(10))),
        )
        .reset_index()
    )

    sec_daily = (
        sec.groupby(["ticker", "date"], dropna=False)
        .agg(
            insider_transaction_count=("owner_name", "size"),
            insider_total_value=("transaction_value", "sum"),
            insider_names=(
                "owner_name",
                lambda values: " || ".join(
                    values.dropna().astype(str).unique()[:10]
                ),
            ),
        )
        .reset_index()
    )

    evidence = market.merge(news_daily, on=["ticker", "date"], how="outer")
    evidence = evidence.merge(sec_daily, on=["ticker", "date"], how="outer")
    evidence["news_count"] = evidence["news_count"].fillna(0).astype("int64")

    if "adj_close" in evidence and evidence["adj_close"].isna().all():
        evidence = evidence.drop(columns="adj_close")

    evidence = evidence.sort_values(["ticker", "date"]).reset_index(drop=True)
    return evidence
