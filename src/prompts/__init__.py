"""Prompt templates for all agent roles."""

from src.prompts.writer import (
    writer_system,
    writer_prompt,
    writer_revision_prompt,
    writer_error_prompt,
)
from src.prompts.reviewer import REVIEWER_SYSTEM, QUICK_REVIEWER_SYSTEM, reviewer_prompt
from src.prompts.reflection import REFLECTION_SYSTEM, reflection_prompt
from src.prompts.debate import DEBATE_JUDGE_SYSTEM, debate_critique_prompt, debate_judge_prompt
from src.prompts.merge import MERGER_SYSTEM, merger_prompt
from src.prompts.planner import PLANNER_SYSTEM, planner_prompt, writer_from_plan_prompt

__all__ = [
    # Writer
    "writer_system",
    "writer_prompt",
    "writer_revision_prompt",
    "writer_error_prompt",
    # Reviewer
    "REVIEWER_SYSTEM",
    "QUICK_REVIEWER_SYSTEM",
    "reviewer_prompt",
    # Reflection
    "REFLECTION_SYSTEM",
    "reflection_prompt",
    # Debate
    "DEBATE_JUDGE_SYSTEM",
    "debate_critique_prompt",
    "debate_judge_prompt",
    # Merge
    "MERGER_SYSTEM",
    "merger_prompt",
    # Planner
    "PLANNER_SYSTEM",
    "planner_prompt",
    "writer_from_plan_prompt",
]
