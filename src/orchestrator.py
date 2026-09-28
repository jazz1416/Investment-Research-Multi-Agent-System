
"""Orchestrator for the multi-agent investment research workflow."""

from __future__ import annotations

from pathlib import Path

from src.insider_agent import analyze_insider_activity
from src.market_agent import analyze_market
from src.news_agent import analyze_news
from src.planner import generate_research_plan
from src.router import route_step
from src.synthesis_agent import synthesize_research


def orchestrate_research(
    ticker: str,
    project_root: str | Path = ".",
) -> dict:
    """Run the full planner-router-specialist workflow."""

    ticker = ticker.upper().strip()
    project_root = Path(project_root)

    plan = generate_research_plan(ticker)

    routing_decisions = [
        route_step(step)
        for step in plan["research_steps"]
    ]

    news_result = analyze_news(
        ticker,
        project_root,
    )

    market_result = analyze_market(
        ticker,
        project_root,
    )

    insider_result = analyze_insider_activity(
        ticker,
        project_root,
    )

    synthesis_result = synthesize_research(
        ticker,
        news_result,
        market_result,
        insider_result,
    )

    specialist_results = {
        "news_agent": news_result,
        "market_agent": market_result,
        "insider_agent": insider_result,
        "synthesis_agent": synthesis_result,
    }

    executed_steps = []

    for decision in routing_decisions:
        agent_name = decision["agent"]

        executed_steps.append(
            {
                "step_id": decision["step_id"],
                "task": decision["task"],
                "agent": agent_name,
                "reason": decision["reason"],
                "result": specialist_results[agent_name],
            }
        )

    return {
        "ticker": ticker,
        "plan": plan,
        "routing_decisions": routing_decisions,
        "executed_steps": executed_steps,
        "specialist_results": specialist_results,
        "final_synthesis": synthesis_result,
    }


def display_orchestration(result: dict) -> None:
    """Print a readable summary of the workflow."""

    print("=" * 72)
    print(f"Ticker: {result['ticker']}")
    print(f"Objective: {result['plan']['objective']}")
    print("=" * 72)

    for step in result["executed_steps"]:
        print(
            f"Step {step['step_id']}: "
            f"{step['task']} -> {step['agent']}"
        )

    print("=" * 72)
    print("Final synthesis")
    print("Risks:")
    for risk in result["final_synthesis"]["risks"]:
        print(f"- {risk}")

    print("Catalysts:")
    for catalyst in result["final_synthesis"]["catalysts"]:
        print(f"- {catalyst}")
