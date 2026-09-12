"""Stage 3 ranking presentation utilities."""

from .comparison import compare_candidates, generate_comparison_explanation
from .data_loader import load_rankings
from .explanation_generator import generate_explanation
from .stage2_adapter import normalize_stage2_output

__all__ = [
    "compare_candidates",
    "generate_comparison_explanation",
    "generate_explanation",
    "load_rankings",
    "normalize_stage2_output",
]
