
"""Planner Agent for the investment research multi-agent system."""

from __future__ import annotations


def generate_research_plan(ticker: str) -> dict:
    """Create a structured research plan for a stock ticker."""

    ticker = ticker.upper().strip()

    research_steps = [
        {
            "step_id": 1,
            "task": "news_analysis",
            "description": f"Review recent financial news and macro developments relevant to {ticker}.",
        },
        {
            "step_id": 2,
            "task": "market_analysis",
            "description": f"Analyze recent price, return, and trading-volume behavior for {ticker}.",
        },
        {
            "step_id": 3,
            "task": "insider_analysis",
            "description": f"Review recent SEC Form 4 insider transactions for {ticker}.",
        },
        {
            "step_id": 4,
            "task": "risk_analysis",
            "description": f"Identify important risks using the available news, market, and insider evidence for {ticker}.",
        },
        {
            "step_id": 5,
            "task": "catalyst_analysis",
            "description": f"Identify possible catalysts or notable events affecting {ticker}.",
        },
        {
            "step_id": 6,
            "task": "final_synthesis",
            "description": f"Synthesize the research evidence into a concise investment-research summary for {ticker}.",
        },
    ]

    return {
        "ticker": ticker,
        "objective": f"Conduct structured multi-agent investment research for {ticker}.",
        "research_steps": research_steps,
    }
