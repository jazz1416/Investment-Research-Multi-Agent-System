import os
from typing import List
from pydantic import BaseModel, Field
from openai import OpenAI
import re

# Initialize client using environment variables configured in .env
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


# Pydantic schemas for evaluation rubric and results
class EvaluationRubric(BaseModel):
    factual_grounding_score: int = Field(default=0, description="Score (0-10) for factual alignment.")
    completeness_score: int = Field(default=0, description="Score (0-10) for required sections.")
    logical_coherence_score: int = Field(default=0, description="Score (0-10) for narrative consistency.")
    clarity_and_structure: int = Field(default=0, description="Score (0-10) for formatting and structure.")

class EvaluationResult(BaseModel):
    overall_score: int
    passed: bool
    rubric: EvaluationRubric
    failure_reason: str = Field(default="")
    refinement_feedback: str = Field(default="")
    missing_elements: List[str] = Field(default_factory=list)

# Evaluator prompts 
EVALUATOR_SYSTEM_PROMPT = """
You are a Strict Financial Research Evaluation Agent auditing automated investment reports.

CRITICAL EVALUATION RUBRIC:
1. HARD PASS/FAIL GATES (Immediate Failure if False):
   - NO_PLACEHOLDERS: Draft must contain zero bracketed placeholders (e.g., '[Insert Date]', '[TBD]').
   - MANDATORY_SECTIONS: Must contain explicit headers for Market Metrics, SEC Insider Activity, and News.
   - NO_FINANCIAL_ADVICE: Must not output explicit 'BUY/SELL' recommendations or fabricated target prices.

2. FACTUAL GROUNDING & PRECISION (0-10):
   - Deduct 2 points for every unverified figure, rounded dollar amount (when exact figures exist in evidence), or misaligned trade date.
   - Every metric must cite its source origin (e.g., [SEC Form 4], [Alpha Vantage], [Marketaux]).
   - Do not penalize for domain-specific tags as long as [Marketaux] is also listed as a source

3. COMPLETENESS (0-10):
   - All available ticker data points in Raw Evidence must be represented.
   - If a data category is absent from Raw Evidence, an explicit missing-data disclaimer must be present under that section.
   - If a data metric (e.g., quarterly revenue) is NOT present in the raw evidence dataset, award FULL POINTS if the draft contains an explicit disclaimer statement under that section header explaining that the data was absent from the raw evidence.
    - Do NOT deduct points for missing raw data if an explicit disclaimer is present.

4. LOGICAL COHERENCE (0-10):
   - Flag any narrative contradictions (e.g., claiming bullish sentiment when price and insider trades are heavily negative).

Pass Condition:
Draft passes ONLY if ALL Hard Gates == True AND Factual Grounding >= 8 AND Overall Score >= 8.
"""

EVALUATOR_USER_PROMPT_TEMPLATE = """
--- CANDIDATE RESEARCH DRAFT ---
{current_draft}

--- RAW EVIDENCE SOURCE ---
{raw_evidence}

Please evaluate the draft against the raw evidence and return a structured EvaluationResult.
"""


def evaluate_draft(
    current_draft: str,
    raw_evidence: str,
    model: str = MODEL_NAME
) -> EvaluationResult:
    """
    Evaluates a candidate research draft using programmatic hard gates first,
    followed by structured LLM evaluation if hard gates pass.
    
    Parameters:
        current_draft (str): The research report draft to evaluate.
        raw_evidence (str): Ground truth evidence (daily_evidence.csv / news_research_results.csv).
        model (str): The LLM model to execute evaluation.
        
    Returns:
        EvaluationResult: Structured result object containing scores, pass/fail status with reason, and critique.
    """
    # Step 1: Manual hard gate checks before LLM as a judge
    failures = []

    # Cheks for exact mandatory headers
    mandatory_headers = [
        "## Market Metrics",
        "## SEC Form 4 Insider Activity",
        "## Financial News Analysis",
        "## Financials & Revenue Performance"
    ]
    missing_headers = [h for h in mandatory_headers if h not in current_draft]
    if missing_headers:
        failures.append(f"Missing exact mandatory section headers: {missing_headers}")

    # Check for line by line source citations
    bullet_lines = [
        line.strip() 
        for line in current_draft.split("\n") 
        if line.strip().startswith("-") or line.strip().startswith("*")
    ]
    uncited_bullets = [
        line for line in bullet_lines 
        if "[Source:" not in line and "not recorded" not in line.lower()
    ]
    if uncited_bullets:
        failures.append(
            f"EVERY individual bullet point containing factual metrics MUST include an inline source tag "
            f"(e.g., [Source: Alpha Vantage], [Source: SEC Form 4], [Source: Marketaux]). "
            f"Missing on: {uncited_bullets[:2]}"
        )

    # Ensures no ellipsis are in the draft
    if "..." in current_draft:
        failures.append(
            "Draft contains literal ellipsis '...'. Write full sentences and use explicit disclaimers for missing data."
        )

    # Ensures no bracketed placeholders are in the draft
    placeholder_pattern = r"\\[(Insert|TBD|Date|Ticker|Header|Name|Value)[^\\]]*\]"
    found_placeholders = re.findall(placeholder_pattern, current_draft, re.IGNORECASE)
    if found_placeholders:
        failures.append(f"Draft contains template placeholders matching pattern: {found_placeholders}")

    # Break out of evaluation if any hard gates fail
    # Do not proceed with LLM as a judge if hard gates fail
    if failures:
        failure_msg = " | ".join(failures)
        return EvaluationResult(
            overall_score=4,
            passed=False,
            rubric=EvaluationRubric(
                factual_grounding_score=4,
                completeness_score=4,
                logical_coherence_score=4,
                clarity_and_structure=4
            ),
            failure_reason=f"Hard gate failure: {failure_msg}",
            refinement_feedback=f"Please fix the following issues: {failure_msg}",
            missing_elements=failures
        )

    # Step 2: LLM as a judge (only runs if hard gates pass)
    user_message = EVALUATOR_USER_PROMPT_TEMPLATE.format(
        current_draft=current_draft,
        raw_evidence=raw_evidence
    )

    # Generate structured response from LLM based on system_prompt
    response = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        response_format=EvaluationResult,
        temperature=0.1
    )

    eval_result: EvaluationResult = response.choices[0].message.parsed
    return eval_result