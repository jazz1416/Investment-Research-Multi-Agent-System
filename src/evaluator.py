import os
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI

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
    factual_grounding: int = Field(
        description="Score 1-10: Are stock prices, market returns, and SEC Form 4 transactions accurate and directly supported by evidence?"
    )
    completeness: int = Field(
        description="Score 1-10: Does the report cover both daily market metrics and processed news context?"
    )
    clarity_and_structure: int = Field(
        description="Score 1-10: Is the analysis well-organized, concise, and logically structured?"
    )

class EvaluationResult(BaseModel):
    overall_score: int = Field(
        description="Overall quality score from 1 to 10."
    )
    passed: bool = Field(
        description="True if overall_score >= 8 and factual_grounding >= 8, otherwise False."
    )
    failure_reason: Optional[str] = Field(
        default=None,
        description="Concise explanation of why the draft failed the quality pass gate (required if passed is False; set to None if passed is True)."
    )
    rubric: EvaluationRubric
    missing_elements: List[str] = Field(
        description="List of specific missing data points, SEC transaction details, or unaddressed news facts."
    )
    refinement_feedback: str = Field(
        description="Detailed critique and specific instructions for the Optimizer to improve the draft."
    )


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


# Evaluation function
def evaluate_draft(
    current_draft: str,
    raw_evidence: str,
    model: str = MODEL_NAME
) -> EvaluationResult:
    """
    Evaluates a candidate research draft against raw evidence using structured LLM output.
    
    Parameters:
        current_draft (str): The research report draft to evaluate.
        raw_evidence (str): Ground truth evidence (daily_evidence.csv / news_research_results.csv).
        model (str): The LLM model to execute evaluation.
        
    Returns:
        EvaluationResult: Structured result object containing scores, pass/fail status with reason, and critique.
    """
    user_message = EVALUATOR_USER_PROMPT_TEMPLATE.format(
        current_draft=current_draft,
        raw_evidence=raw_evidence
    )

    # Generate response from LLM
    response = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        response_format=EvaluationResult,
        # Set temperature to a low number for deterministic grading
        temperature=0.1
    )

    eval_result: EvaluationResult = response.choices[0].message.parsed
    return eval_result