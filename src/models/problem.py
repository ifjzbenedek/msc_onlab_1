"""Data model for a LeetCode problem."""

from pydantic import BaseModel, Field


class Problem(BaseModel):
    id: str
    title: str
    slug: str
    difficulty: str
    description: str
    code_stub: str
    lang: str = "python3"
    tags: list[str] = Field(default_factory=list)
