"""Load Stage 2 ranking output and return normalized Stage 3 candidates."""

import json
from pathlib import Path
from typing import Any

from .stage2_adapter import normalize_stage2_output


def load_rankings(file_path: str | Path) -> list[dict[str, Any]]:
    """Read a ranking JSON file and normalize its candidates in source order."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Ranking file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Ranking path is not a file: {path}")

    try:
        with path.open("r", encoding="utf-8") as ranking_file:
            payload = json.load(ranking_file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in ranking file {path} "
            f"at line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error

    return normalize_stage2_output(payload)
