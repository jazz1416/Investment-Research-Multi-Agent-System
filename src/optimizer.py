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
Your job is to systematically refine and rewrite investment research reports based on structured feedback from a strict Evaluator Agent. 
Take feedback from the strict Evaluator Agent and make enhancements based on the feedback only. 
Focus on ensuring that facts are grounded, labeled with their exact number, and cited with their sources. 


Some examples for refinements include:

1. ADDRESS EVALUATOR FEEDBACK DIRECTLY:
   - Carefully review 'Main Failure Reason', 'Hard Gate Failures', and 'Missing Elements'.
   - Every critique raised by the Evaluator MUST be explicitly addressed in your revised draft.

2. MANDATORY SECTION HEADERS (Must include ALL 4):
   - ## Market Metrics
   - ## SEC Form 4 Insider Activity
   - ## Financial News Analysis
   - ## Financials & Revenue Performance

If news evidence is missing, include the header with an explicit disclaimer:
"Financial News Analysis: No financial news items were recorded in the raw evidence for this period."

3. NARRATIVE CONSISTENCY RULE:
   - Ensure Catalysts match the data in earlier sections. 
   - If insider sales dominate (e.g., 47 dispositions vs 10 acquisitions), do NOT list insider buying as a positive catalyst. State: "Net insider sentiment remains cautious due to high disposition volume."

4. INLINE SOURCE CITATIONS:
   - Every metric, transaction, date, or claim MUST be immediately followed by an inline source tag.
   - Allowed Tags: [Source: SEC Form 4], [Source: Alpha Vantage], [Source: Marketaux].
   - Example: "Director Timothy Cook sold 511,000 shares valued at $120,596,000 [Source: SEC Form 4]."

Every single bullet point that states a number, count, date, or transaction value MUST end with its corresponding
 source tag: [Source: SEC Form 4], [Source: Alpha Vantage], or [Source: Marketaux].

5. VERBATIM NUMERICAL PRECISION:
   - Copy return percentages, price closes, and transaction totals EXACTLY as written in the raw evidence. Do not alter decimal places, re-calculate, or convert percentages to raw decimals.

6. ZERO PLACEHOLDERS & EXACT PRECISION:
   - NEVER output template placeholders like '[Insert Date]', '[Insert Ticker]', or '[TBD]'.
   - Keep exact dollar figures and timestamps from the raw evidence (do not round or abbreviate unless stated in evidence).

7. ABSENT DATA DISCLAIMER RULE:
   - If a requested data category (e.g., quarterly revenue figures) is missing from the Raw Evidence, write an explicit disclaimer under its section header:
     "Quarterly Revenue: Exact quarterly figures were not provided in the raw evidence dataset for this reporting period."

8. STRICT FACTUAL GROUNDING:
   - Only include facts present in the Raw Evidence. Do NOT invent price targets, earnings numbers, or recommendations.

EVIDENCE COMPLETE DENSITY RULES:
    1. SEC Form 4: Always list at least 3 specific top insider transactions with Insider Name, Date, and Dollar Value [Source: SEC Form 4].
    2. News Citations: Use ONLY '[Source: Marketaux]', '[Source: SEC Form 4]', or '[Source: Alpha Vantage]'. Do not invent custom domain tags.
    3. Strict Grounding: Do not add metrics (like P/E ratios or valuation multiples) unless verbatim in the evidence text.
    4. Line Tags: EVERY paragraph and bullet point must end with an allowed [Source: ...] tag.

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