"""Data model for a LeetCode problem."""

from pydantic import BaseModel


class Problem(BaseModel):
    id: str
    title: str
    slug: str
    difficulty: str
    description: str
    code_stub: str
