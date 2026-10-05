"""Planner agent: checks what data we have for a ticker, then builds the research steps."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

EVIDENCE_FILES = {
    "news": "news_research_results.csv",
    "market": "market_data_clean.csv",
    "insider": "sec_form4_clean.csv",
}


def check_available_evidence(ticker: str, project_root: str | Path = ".") -> dict:
    """Count how many rows each processed dataset has for this ticker."""

    ticker = ticker.upper().strip()
    processed = Path(project_root) / "data" / "processed"

    counts = {}
    news_categories = {}

    for source, filename in EVIDENCE_FILES.items():
        path = processed / filename

        if not path.exists():
            counts[source] = 0
            continue

        data = pd.read_csv(path)
        rows = data[data["ticker"].astype(str).str.upper() == ticker]
        counts[source] = len(rows)

        if source == "news" and not rows.empty and "category" in rows.columns:
            news_categories = rows["category"].value_counts().to_dict()

    return {
        "ticker": ticker,
        "counts": counts,
        "news_categories": news_categories,
    }


def _default_evidence(ticker: str) -> dict:
    """Used when we don't check the data: treat every source as available."""

    return {
        "ticker": ticker,
        "counts": {"news": None, "market": None, "insider": None},
        "news_categories": {},
    }


def generate_research_plan(ticker: str, project_root: str | Path | None = None) -> dict:
    """Build the research plan for a ticker.

    If project_root is given, a step is only added when that source has data.
    If not, it returns the full 6-step plan.
    """

    ticker = ticker.upper().strip()

    if project_root is None:
        evidence = _default_evidence(ticker)
    else:
        evidence = check_available_evidence(ticker, project_root)

    counts = evidence["counts"]
    categories = evidence["news_categories"]

    candidate_steps = []
    decisions = []

    # News step
    if counts["news"] == 0:
        decisions.append(
            {"task": "news_analysis", "included": False,
             "reason": f"No processed news articles found for {ticker}."}
        )
    else:
        description = f"Review recent financial news and macro developments relevant to {ticker}."
        reason = "News data available."
        if counts["news"]:
            top_category = max(categories, key=categories.get) if categories else None
            reason = f"Found {counts['news']} processed news articles."
            if top_category:
                top_count = categories[top_category]
                description += f" Most coverage is {top_category} ({top_count} articles)."
        candidate_steps.append(("news_analysis", description))
        decisions.append({"task": "news_analysis", "included": True, "reason": reason})

    # Market step
    if counts["market"] == 0:
        decisions.append(
            {"task": "market_analysis", "included": False,
             "reason": f"No market data found for {ticker}."}
        )
    else:
        reason = (
            f"Found {counts['market']} trading days of market data."
            if counts["market"] else "Market data available."
        )
        candidate_steps.append(
            ("market_analysis",
             f"Analyze recent price, return, and trading-volume behavior for {ticker}.")
        )
        decisions.append({"task": "market_analysis", "included": True, "reason": reason})

    # Insider step
    if counts["insider"] == 0:
        decisions.append(
            {"task": "insider_analysis", "included": False,
             "reason": f"No SEC Form 4 insider transactions found for {ticker}."}
        )
    else:
        reason = (
            f"Found {counts['insider']} SEC Form 4 insider transactions."
            if counts["insider"] else "Insider data available."
        )
        candidate_steps.append(
            ("insider_analysis", f"Review recent SEC Form 4 insider transactions for {ticker}.")
        )
        decisions.append({"task": "insider_analysis", "included": True, "reason": reason})

    # risk, catalyst and summary steps only make sense if we have some data
    if candidate_steps:
        candidate_steps.extend(
            [
                ("risk_analysis",
                 f"Identify important risks using the available evidence for {ticker}."),
                ("catalyst_analysis",
                 f"Identify possible catalysts or notable events affecting {ticker}."),
                ("final_synthesis",
                 f"Synthesize the research evidence into a concise investment-research "
                 f"summary for {ticker}."),
            ]
        )
    else:
        decisions.append(
            {"task": "final_synthesis", "included": False,
             "reason": f"No evidence available for {ticker}, so there is nothing to synthesize."}
        )

    research_steps = [
        {"step_id": step_id, "task": task, "description": description}
        for step_id, (task, description) in enumerate(candidate_steps, start=1)
    ]

    return {
        "ticker": ticker,
        "objective": f"Conduct structured multi-agent investment research for {ticker}.",
        "evidence_checked": project_root is not None,
        "evidence_counts": counts,
        "research_steps": research_steps,
        "planning_decisions": decisions,
    }
