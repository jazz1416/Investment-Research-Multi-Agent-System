"""Orchestrator for the multi-agent investment research workflow."""

from __future__ import annotations

from pathlib import Path

from src.insider_agent import analyze_insider_activity
from src.market_agent import analyze_market
from src.news_agent import analyze_news
from src.planner import generate_research_plan
from src.router import route_step
from src.synthesis_agent import synthesize_research

# the function each specialist agent runs
SPECIALIST_TOOLS = {
    "news_agent": analyze_news,
    "market_agent": analyze_market,
    "insider_agent": analyze_insider_activity,
}

SKIPPED_MESSAGES = {
    "news_agent": ("article_count", "No processed news found for {ticker} (skipped by planner)."),
    "market_agent": ("row_count", "No market data found for {ticker} (skipped by planner)."),
    "insider_agent": (
        "transaction_count",
        "No insider transactions found for {ticker} (skipped by planner).",
    ),
}


def orchestrate_research(
    ticker: str,
    project_root: str | Path = ".",
) -> dict:
    """Run the planner, router, specialists and synthesis for one ticker.

    Only the agents that the router picked get called.
    """

    ticker = ticker.upper().strip()
    project_root = Path(project_root)

    plan = generate_research_plan(ticker, project_root)

    routing_decisions = [route_step(step) for step in plan["research_steps"]]
    selected_agents = {decision["agent"] for decision in routing_decisions}

    # only call the agents that got a step, the rest are marked as skipped
    specialist_results = {}
    for agent_name, tool in SPECIALIST_TOOLS.items():
        if agent_name in selected_agents:
            specialist_results[agent_name] = tool(ticker, project_root)
        else:
            count_key, message = SKIPPED_MESSAGES[agent_name]
            specialist_results[agent_name] = {
                "agent": agent_name,
                "ticker": ticker,
                count_key: 0,
                "skipped": True,
                "message": message.format(ticker=ticker),
            }

    synthesis_result = synthesize_research(
        ticker,
        specialist_results["news_agent"],
        specialist_results["market_agent"],
        specialist_results["insider_agent"],
    )
    specialist_results["synthesis_agent"] = synthesis_result

    executed_steps = [
        {
            "step_id": decision["step_id"],
            "task": decision["task"],
            "agent": decision["agent"],
            "reason": decision["reason"],
            "result": specialist_results[decision["agent"]],
        }
        for decision in routing_decisions
    ]

    return {
        "ticker": ticker,
        "plan": plan,
        "routing_decisions": routing_decisions,
        "agents_called": sorted(selected_agents & SPECIALIST_TOOLS.keys()),
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

    print("Planner decisions:")
    for decision in result["plan"]["planning_decisions"]:
        status = "include" if decision["included"] else "skip"
        print(f"- {decision['task']}: {status} ({decision['reason']})")

    print("=" * 72)
    for step in result["executed_steps"]:
        print(f"Step {step['step_id']}: {step['task']} -> {step['agent']}")

    print(f"Agents called: {', '.join(result['agents_called']) or 'none'}")

    print("=" * 72)
    print("Final synthesis")
    print("Risks:")
    for risk in result["final_synthesis"]["risks"]:
        print(f"- {risk}")

    print("Catalysts:")
    for catalyst in result["final_synthesis"]["catalysts"]:
        print(f"- {catalyst}")
