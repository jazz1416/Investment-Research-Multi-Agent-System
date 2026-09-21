import os
import random
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parents[1]

PATHS = {
    "root": PROJECT_ROOT,
    "raw": PROJECT_ROOT / "data" / "raw",
    "processed": PROJECT_ROOT / "data" / "processed",
    "cache": PROJECT_ROOT / "data" / "cache",
    "docs": PROJECT_ROOT / "docs",
}


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)


def ensure_directories() -> None:
    for path in PATHS.values():
        path.mkdir(parents=True, exist_ok=True)


def load_project_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env")


def get_target_tickers() -> list[str]:
    load_project_env()
    raw = os.getenv("TARGET_TICKERS", "AAPL")
    return [ticker.strip().upper() for ticker in raw.split(",") if ticker.strip()]
