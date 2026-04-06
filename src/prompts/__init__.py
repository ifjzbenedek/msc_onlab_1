"""Prompt templates for all agent roles."""

from src.prompts.writer import (
    writer_system,
    writer_prompt,
    writer_revision_prompt,
    writer_error_prompt,
)
from src.prompts.reviewer import REVIEWER_SYSTEM, reviewer_prompt
from src.prompts.reflection import REFLECTION_SYSTEM, reflection_prompt

__all__ = [
    # Writer
    "writer_system",
    "writer_prompt",
    "writer_revision_prompt",
    "writer_error_prompt",
    # Reviewer
    "REVIEWER_SYSTEM",
    "reviewer_prompt",
    # Reflection
    "REFLECTION_SYSTEM",
    "reflection_prompt",
]
