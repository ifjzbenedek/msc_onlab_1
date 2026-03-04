from typing import Optional
from pydantic import BaseModel


class PipelineRunResult(BaseModel):
    time: float
    accepted: Optional[bool] = None
    status: str
    num_reviews: int = 0