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
You are a Financial Research Optimization Agent.

CRITICAL CITATION & FORMATTING RULES:
- You MUST append an inline source tag (e.g., [Source: Alpha Vantage], [Source: SEC Form 4], [Source: Marketaux]) to EVERY SINGLE bullet point that contains data or metrics.
- Do NOT place a single tag at the end of a section. EVERY line must have its own tag!
- NEVER output trailing ellipsis '...' or incomplete sentences (e.g., 'opened at $3 ...').
- Use EXACT source names for citations:
   - Use [Source: Alpha Vantage] for market price/volume data.
   - Use [Source: SEC Form 4] for insider trading data.
   - Use [Source: Marketaux] for financial news articles.
   - Do NOT use generic tags like [Source: Daily Market Evidence].
- Every bullet point must be a complete, well-formed sentence.

Example Correct Format:
## Market Metrics
- Trading Days Analyzed: 22 [Source: Alpha Vantage]
- Latest Close Price: $515.31 [Source: Alpha Vantage]
- Average Daily Volume: 20,926,087 shares [Source: Alpha Vantage]
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