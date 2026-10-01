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
You are an expert Financial Research Evaluation Agent.
Your job is to rigorously evaluate candidate stock research reports against raw evidence sources and output structured quality metrics.

Evaluation Criteria:
1. FACTUAL GROUNDING (0-10): Are all stock prices, SEC Form 4 trade values, dates, and claims strictly supported by the raw evidence? Deduct heavily for any invented figures.
2. COMPLETENESS (0-10): Does the report cover all available key data points in the raw evidence (market metrics, insider trades, news)? 
   - NOTE ON MISSING METRICS: If specific financial metrics (such as quarterly revenue) are NOT present in the raw evidence, do NOT penalize the draft for omitting them, provided the draft notes their absence or accurately summarizes all available evidence.
3. CLARITY & STRUCTURE (0-10): Is the report professional, well-formatted, and logical?

Pass Threshold:
- Overall Score must be >= 8/10.
- Factual Grounding must be >= 8/10.
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