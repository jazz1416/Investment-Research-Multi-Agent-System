import json
import os
import datetime
from typing import Dict, List, Any, Optional


class ResearchMemoryStore:
    """
    Manages persistent, cross-run memory for stock research analyses.
    Stores historical evaluation scores, recurring critique notes, and key takeaways per ticker.
    """

    def __init__(self, filepath: str = "data/processed/memory_store.json"):
        self.filepath = filepath
        self._ensure_dir_exists()
        self.memory: Dict[str, List[Dict[str, Any]]] = self._load_memory()

    def _ensure_dir_exists(self) -> None:
        """Ensures the destination folder exists before reading or writing."""
        dir_name = os.path.dirname(self.filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

    def _load_memory(self) -> Dict[str, List[Dict[str, Any]]]:
        """Loads memory data from JSON file if present."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"[MemoryStore] Warning: Failed to load memory file ({e}). Starting fresh.")
                return {}
        return {}

    def _save_memory(self) -> None:
        """Persists memory data to JSON file."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[MemoryStore] Error saving memory to {self.filepath}: {e}")

    def get_ticker_memory(self, ticker: str, max_entries: int = 3) -> str:
        """
        Fetches formatted history for a given ticker to inject into prompts.
        
        Parameters:
            ticker (str): Stock symbol (e.g., 'AAPL', 'NVDA').
            max_entries (int): Number of most recent runs to include.
            
        Returns:
            str: Formatted memory text block for LLM context injection.
        """
        symbol = ticker.upper()
        ticker_history = self.memory.get(symbol, [])

        if not ticker_history:
            return f"No previous research memory recorded for {symbol}."

        # Take the N most recent entries
        recent_runs = ticker_history[-max_entries:]
        memory_lines = [f"=== HISTORICAL MEMORY FOR {symbol} ==="]

        for i, entry in enumerate(recent_runs, 1):
            timestamp = entry.get("timestamp", "Unknown Date")
            score = entry.get("score", "N/A")
            summary = entry.get("summary", "No summary provided.")
            lessons = entry.get("lessons_learned", "")

            line = f"Run #{i} [{timestamp}] - Final Quality Score: {score}/10\n  Summary: {summary}"
            if lessons:
                line += f"\n  Lessons Learned: {lessons}"
            memory_lines.append(line)

        return "\n".join(memory_lines)

    def save_run(
        self,
        ticker: str,
        timestamp: Optional[str],
        score: int,
        summary: str,
        lessons_learned: Optional[str] = None
    ) -> None:
        """
        Appends a completed research run record to the memory store.
        
        Parameters:
            ticker (str): Stock symbol.
            timestamp (str): Execution timestamp string.
            score (int): Final evaluation score (1-10).
            summary (str): Brief summary of run outcome and evaluator feedback.
            lessons_learned (str): Optional recurring critique or pitfall note to avoid next time.
        """
        symbol = ticker.upper()
        if symbol not in self.memory:
            self.memory[symbol] = []

        if not timestamp:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = {
            "timestamp": timestamp,
            "score": score,
            "summary": summary,
            "lessons_learned": lessons_learned or ""
        }

        self.memory[symbol].append(entry)
        self._save_memory()
        print(f"[MemoryStore] Saved run for {symbol} to {self.filepath}.")

    def clear_memory(self, ticker: Optional[str] = None) -> None:
        """Clears memory for a specific ticker or wipes the entire memory store."""
        if ticker:
            symbol = ticker.upper()
            if symbol in self.memory:
                del self.memory[symbol]
                self._save_memory()
                print(f"[MemoryStore] Cleared memory for {symbol}.")
        else:
            self.memory = {}
            self._save_memory()
            print("[MemoryStore] Cleared all memory records.")