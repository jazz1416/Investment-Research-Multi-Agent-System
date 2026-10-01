import os
from typing import List, Optional
from openai import OpenAI
from datetime import datetime

# Read env variables
api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")

# If base_url is empty string or None, set to None so OpenAI uses its default URL
if not base_url:
    base_url = None

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

MODEL_NAME = os.getenv("LLM_MODEL", "gpt-4o-mini")

OPTIMIZER_SYSTEM_PROMPT = """
You are an expert Financial Research Optimization Agent.
Your job is to refine an investment analysis report based on structured feedback from an Evaluator Agent.

CRITICAL RULES:
1. MANDATORY SECTIONING: You MUST include a dedicated section titled "## Financials & Revenue Performance". In this section, explicitly state all revenue, sales, and financial growth metrics found in the Raw Evidence Source.
2. ADDRESS EVALUATOR CRITIQUE: Carefully review 'Missing Elements to Add' and 'Main Failure Reason'. Locate these exact figures in the Raw Evidence and write them into the revised draft.
3. STRICT FACTUAL GROUNDING: Every figure, percentage, stock price, and SEC trade must be strictly grounded in the Raw Evidence. Do NOT fabricate numbers.
4. ABSENT DATA FALLBACK: If specific quarterly revenue dollar figures are not present in the Raw Evidence, explicitly write under the section header:
   "Quarterly Revenue: Exact quarterly revenue dollar figures were not recorded in the primary evidence dataset for this reporting period."

Formatting Guidelines:
1. NEVER output bracketed template placeholders like '[Insert Current Date]' or '[Insert Ticker]'.
2. Replace date placeholders with actual dates or omit them cleanly.
"""


OPTIMIZER_USER_PROMPT_TEMPLATE = """
You are refining a stock research report to pass a strict quality gate.

Current Draft:
{current_draft}

Evaluator Critique & Failure Reason:
- Main Failure Reason: {failure_reason}
- Missing Elements to Add: {missing_elements}
- Specific Refinement Feedback: {feedback}

Raw Evidence Source:
{raw_evidence}

Instructions:
1. Revise the current draft to directly integrate the missing elements listed above.
2. Ensure every added metric (prices, Form 4 trade values, news headlines) is strictly grounded in the Raw Evidence.
3. If a requested metric is not in the Raw Evidence, state its absence explicitly as instructed.
"""


def optimize_draft(
    current_draft: str,
    feedback: str,
    missing_elements: List[str],
    raw_evidence: str,
    overall_score: int = 0,
    memory_context: Optional[str] = None,
    failure_reason: str = None,
    model: str = MODEL_NAME
) -> str:
    """
    Refines a candidate research draft using feedback and missing facts from the Evaluator.
    
    Parameters:
        current_draft (str): The candidate research draft to improve.
        feedback (str): Constructive critique instructions from EvaluationResult.
        missing_elements (List[str]): List of missing items identified by the Evaluator.
        raw_evidence (str): Ground truth data (from daily_evidence.csv / news_research_results.csv).
        overall_score (int): Previous quality score.
        memory_context (str): Historical run memory/notes for this ticker.
        model (str): LLM model identifier.
        
    Returns:
        str: The updated, higher-quality research report draft.
    """
    formatted_missing = "\n".join([f"- {item}" for item in missing_elements]) if missing_elements else "None noted."
    formatted_memory = memory_context if memory_context else "No historical notes for this ticker."
    formatted_failure_reason = failure_reason if failure_reason else "N/A"

    user_message = OPTIMIZER_USER_PROMPT_TEMPLATE.format(
        current_draft=current_draft,
        failure_reason=formatted_failure_reason,
        overall_score=overall_score,
        feedback=feedback,
        missing_elements=formatted_missing,
        raw_evidence=raw_evidence,
        memory_context=formatted_memory
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": OPTIMIZER_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        # Low temperature for accurate, grounded revisions
        temperature=0.3
    )

    refined_draft = response.choices[0].message.content.strip()
    return refined_draft