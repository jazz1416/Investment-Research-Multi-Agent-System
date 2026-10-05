import datetime
from typing import Dict, Any, Tuple, List, Optional

from src.evaluator import evaluate_draft, EvaluationResult
from src.optimizer import optimize_draft
from src.memory import ResearchMemoryStore

# Run Evaluator-Optimizer workflow
def run_evaluator_optimizer_workflow(
    ticker: str,
    initial_draft: str,
    raw_evidence: str,
    max_iterations: int = 3,
    memory_store_path: str = "data/processed/memory_store.json"
) -> Tuple[str, EvaluationResult, List[Dict[str, Any]]]:
    """
    Orchestrates the Evaluator-Optimizer refinement loop and handles cross-run memory.
    
    Parameters:
        ticker (str): The target stock symbol (e.g., 'AAPL', 'NVDA').
        initial_draft (str): The raw draft produced by specialist research agents.
        raw_evidence (str): The combined daily evidence and news processing facts.
        max_iterations (int): Maximum number of evaluation-optimization passes (default: 3).
        memory_store_path (str): Path to persistent JSON memory file.
        
    Returns:
        Tuple containing:
            - final_draft (str): The final polished analysis report.
            - final_eval (EvaluationResult): The final evaluation rubric & score object.
            - history (List[Dict]): Detailed iteration history for auditing.
    """
    ticker = ticker.upper()
    memory_store = ResearchMemoryStore(filepath=memory_store_path)
    
    # Fetch historical run memory for ticker
    memory_context = memory_store.get_ticker_memory(ticker)
    print(f"[{ticker}] Loaded Memory Context:\n{memory_context}\n" + "-"*50)

    current_draft = initial_draft
    iteration_history: List[Dict[str, Any]] = []
    final_eval_result: Optional[EvaluationResult] = None

    # Evaluator-Optimizer Execution Loop
    for iteration in range(1, max_iterations + 1):
        print(f"[{ticker}] --- Starting Iteration {iteration}/{max_iterations} ---")
        
        # Evaluate current draft
        eval_result: EvaluationResult = evaluate_draft(
            current_draft=current_draft,
            raw_evidence=raw_evidence
        )
        final_eval_result = eval_result

        # Log iteration
        iteration_log = {
            "iteration": iteration,
            "draft": current_draft,
            "overall_score": eval_result.overall_score,
            "passed": eval_result.passed,
            "rubric": eval_result.rubric.model_dump(),
            "feedback": eval_result.refinement_feedback,
            "missing_elements": eval_result.missing_elements,
            "timestamp": datetime.datetime.now().isoformat()
        }
        iteration_history.append(iteration_log)

        print(f"[{ticker}] Iteration {iteration} Score: {eval_result.overall_score}/10 | Passed: {eval_result.passed} | Failure Reason: {eval_result.failure_reason}")

        # Check termination criteria
        if eval_result.passed or iteration == max_iterations:
            if eval_result.passed:
                print(f"[{ticker}] Quality threshold met on iteration {iteration}!")
            else:
                print(f"[{ticker}] Reached max iterations ({max_iterations}). Finalizing current draft.")
            break

        # Helps communication between evaluator and optimizer
        feedback_prompt = f"""
        EVALUATOR CRITIQUE:
        - Overall Score: {eval_result.overall_score}/10
        - Main Failure Reason: {eval_result.failure_reason}
        - Refinement Feedback: {eval_result.refinement_feedback}
        """
        
        # Refine draft using optimizer
        print(f"[{ticker}] Refining draft based on evaluator feedback...")
        current_draft = optimize_draft(
            current_draft=current_draft,
            feedback=feedback_prompt,
            raw_evidence=raw_evidence,
            missing_elements=eval_result.missing_elements
        )

    # Update memory storage with final results
    run_summary = (
        f"Final Score: {final_eval_result.overall_score}/10 after {len(iteration_history)} iterations. "
        f"Evaluator Notes: {final_eval_result.refinement_feedback[:150]}..."
    )
    memory_store.save_run(
        ticker=ticker,
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        score=final_eval_result.overall_score,
        summary=run_summary
    )
    print(f"[{ticker}] Persistent memory updated in {memory_store_path}.")

    return current_draft, final_eval_result, iteration_history