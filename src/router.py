
"""Router Agent for the investment research multi-agent system."""

from __future__ import annotations


def route_step(step: dict) -> dict:
    """Route a planner step to the appropriate specialist agent."""

    task = step.get("task", "").strip().lower()

    routing_map = {
        "news_analysis": "news_agent",
        "market_analysis": "market_agent",
        "insider_analysis": "insider_agent",
        "risk_analysis": "synthesis_agent",
        "catalyst_analysis": "synthesis_agent",
        "final_synthesis": "synthesis_agent",
    }

    selected_agent = routing_map.get(task, "synthesis_agent")

    reasons = {
        "news_agent": "This task depends primarily on processed financial-news evidence.",
        "market_agent": "This task depends primarily on market price, return, and volume evidence.",
        "insider_agent": "This task depends primarily on SEC Form 4 insider-transaction evidence.",
        "synthesis_agent": "This task requires combining evidence from multiple sources.",
    }

    return {
        "step_id": step.get("step_id"),
        "task": task,
        "agent": selected_agent,
        "reason": reasons[selected_agent],
        "description": step.get("description", ""),
    }
