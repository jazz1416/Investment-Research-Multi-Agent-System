"""Connect the planner-router orchestration to the evaluator-optimizer workflow.

Flow:
    orchestrate_research()            plan, route, run specialists, synthesize
    -> build_research_draft()         turn the results into a written draft
    -> build_raw_evidence()           collect the evidence the evaluator checks against
    -> run_evaluator_optimizer_workflow()   evaluate, refine, and save memory
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.orchestrator import orchestrate_research

MAX_NEWS_NOTES = 5


def _format_date(value) -> str:
    """Return a date as YYYY-MM-DD, or 'n/a' if missing."""
    if value is None or pd.isna(value):
        return "n/a"
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def _clean_text(value) -> str:
    """Return text with missing values replaced by an empty string."""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def build_research_draft(result: dict) -> str:
    """Write an initial research draft from an orchestrate_research() result.

    Every figure in the draft comes directly from the specialist agents, so the
    evaluator can check it against the raw evidence.
    """

    ticker = result["ticker"]
    news = result["specialist_results"]["news_agent"]
    market = result["specialist_results"]["market_agent"]
    insider = result["specialist_results"]["insider_agent"]
    synthesis = result["final_synthesis"]

    lines = [f"# Investment Research Draft: {ticker}", ""]

    # Market performance
    lines.append("## Market Performance")
    if market.get("row_count", 0) > 0:
        lines.extend(
            [
                f"- Trading days analyzed: {market['row_count']} "
                f"({_format_date(market['start_date'])} to {_format_date(market['end_date'])})",
                f"- Latest close: ${market['latest_close']:,.2f} "
                f"on volume of {market['latest_volume']:,.0f} shares",
                f"- Average daily return: {market['average_daily_return']:.2%}",
                f"- Average daily volume: {market['average_volume']:,.0f} shares",
            ]
        )
    else:
        lines.append(f"- {market.get('message', 'No market data available.')}")
    lines.append("")

    # Financials (required section in the optimizer prompt)
    lines.extend(
        [
            "## Financials & Revenue Performance",
            "Quarterly Revenue: Exact quarterly revenue dollar figures were not recorded "
            "in the primary evidence dataset for this reporting period.",
            "",
        ]
    )

    # Insider activity
    lines.append("## Insider Activity (SEC Form 4)")
    if insider.get("transaction_count", 0) > 0:
        lines.extend(
            [
                f"- Transactions: {insider['transaction_count']} by "
                f"{insider['unique_insiders']} insiders "
                f"({_format_date(insider['start_date'])} to {_format_date(insider['end_date'])})",
                f"- Acquisitions: {insider['acquired_transactions']}, "
                f"dispositions: {insider['disposed_transactions']}",
                f"- Total transaction value: ${insider['total_transaction_value']:,.2f}",
            ]
        )
    else:
        lines.append(f"- {insider.get('message', 'No insider transactions available.')}")
    lines.append("")

    # News
    lines.append("## News Coverage")
    if news.get("article_count", 0) > 0:
        categories = ", ".join(
            f"{name} ({count})" for name, count in news["categories"].items()
        )
        lines.append(f"- Articles analyzed: {news['article_count']}")
        lines.append(f"- Categories: {categories}")
        for note in news["research_notes"][:MAX_NEWS_NOTES]:
            title = _clean_text(note.get("title"))
            summary = _clean_text(note.get("summary")) or _clean_text(note.get("event"))
            category = _clean_text(note.get("category"))
            line = f"- {title} [{category}]"
            lines.append(f"{line}: {summary}" if summary else line)
    else:
        lines.append(f"- {news.get('message', 'No news available.')}")
    lines.append("")

    # Synthesis
    lines.append("## Risks")
    if synthesis["risks"]:
        lines.extend(f"- {risk}" for risk in synthesis["risks"])
    else:
        lines.append("- No risks identified from the available evidence.")
    lines.append("")

    lines.append("## Catalysts")
    if synthesis["catalysts"]:
        lines.extend(f"- {catalyst}" for catalyst in synthesis["catalysts"])
    else:
        lines.append("- No catalysts identified from the available evidence.")

    return "\n".join(lines)


def build_raw_evidence(ticker: str, project_root: str | Path = ".") -> str:
    """Collect the market, insider, and news evidence the evaluator checks against.

    Uses the same format as notebook 05.
    """

    ticker = ticker.upper().strip()
    processed = Path(project_root) / "data" / "processed"

    daily = pd.read_csv(processed / "daily_evidence.csv")
    news = pd.read_csv(processed / "news_research_results.csv")

    t_daily = daily[daily["ticker"].astype(str).str.upper() == ticker]
    t_news = news[news["ticker"].astype(str).str.upper() == ticker]

    daily_text = (
        t_daily.to_string(index=False) if not t_daily.empty else "No market/SEC evidence recorded."
    )
    news_text = (
        t_news.to_string(index=False) if not t_news.empty else "No news research evidence recorded."
    )

    return (
        f"\n=== DAILY MARKET & SEC FORM 4 EVIDENCE ({ticker}) ===\n{daily_text}\n"
        f"\n=== PROCESSED NEWS RESEARCH EVIDENCE ({ticker}) ===\n{news_text}\n"
    )


def run_full_research(
    ticker: str,
    project_root: str | Path = ".",
    max_iterations: int = 3,
    memory_store_path: str | Path | None = None,
) -> dict:
    """Run the full system: orchestration, then evaluation and refinement with memory.

    Load the .env file before calling this function, because the evaluator and
    optimizer read the LLM settings when they are imported.
    """

    # Imported here so the orchestration part can run without LLM settings.
    from src.eval_opt_workflow import run_evaluator_optimizer_workflow

    project_root = Path(project_root)
    if memory_store_path is None:
        memory_store_path = project_root / "data" / "processed" / "memory_store.json"

    orchestration = orchestrate_research(ticker, project_root)
    initial_draft = build_research_draft(orchestration)
    raw_evidence = build_raw_evidence(ticker, project_root)

    final_report, final_evaluation, history = run_evaluator_optimizer_workflow(
        ticker=orchestration["ticker"],
        initial_draft=initial_draft,
        raw_evidence=raw_evidence,
        max_iterations=max_iterations,
        memory_store_path=str(memory_store_path),
    )

    return {
        "ticker": orchestration["ticker"],
        "orchestration": orchestration,
        "initial_draft": initial_draft,
        "raw_evidence": raw_evidence,
        "final_report": final_report,
        "final_evaluation": final_evaluation,
        "history": history,
    }
