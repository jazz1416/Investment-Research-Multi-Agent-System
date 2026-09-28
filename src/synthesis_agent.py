
"""Synthesis specialist for combining multi-source research evidence."""

from __future__ import annotations


def synthesize_research(
    ticker: str,
    news_result: dict,
    market_result: dict,
    insider_result: dict,
) -> dict:
    """Combine specialist outputs into structured research conclusions."""

    ticker = ticker.upper().strip()

    risks = []
    catalysts = []

    # News-derived signals
    categories = news_result.get("categories", {})

    if categories.get("macro_market", 0) > 0:
        risks.append(
            "Macro or broader market developments may affect the stock."
        )

    if categories.get("analyst_investor", 0) > 0:
        catalysts.append(
            "Recent analyst or investor commentary may influence market expectations."
        )

    # Market-derived signals
    avg_return = market_result.get("average_daily_return")

    if avg_return is not None:
        if avg_return < 0:
            risks.append(
                "Average daily market return over the available period is negative."
            )
        else:
            catalysts.append(
                "Average daily market return over the available period is positive."
            )

    # Insider-derived signals
    acquired = insider_result.get("acquired_transactions", 0)
    disposed = insider_result.get("disposed_transactions", 0)

    if disposed > acquired:
        risks.append(
            "Disposed insider transactions outnumber acquired transactions in the available Form 4 data."
        )

    if acquired > 0:
        catalysts.append(
            "The available Form 4 data includes insider acquisition transactions."
        )

    return {
        "agent": "synthesis_agent",
        "ticker": ticker,
        "risks": risks,
        "catalysts": catalysts,
        "summary": {
            "news_articles": news_result.get("article_count", 0),
            "market_rows": market_result.get("row_count", 0),
            "insider_transactions": insider_result.get(
                "transaction_count", 0
            ),
        },
    }
