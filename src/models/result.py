from pydantic import BaseModel


class SolveResult(BaseModel):
    slug: str
    title: str
    difficulty: str
    model: str
    raw_response: str
    extracted_code: str | None
    generation_seconds: float
    error: str | None = None


class SubmissionResult(BaseModel):
    slug: str
    submission_id: int
    accepted: bool
    status: str
    total_correct: int | None = None
    total_testcases: int | None = None
    runtime_percentile: float | None = None
    memory_percentile: float | None = None
    # error feedback (useful for reviewer agent)
    compile_error: str | None = None
    runtime_error: str | None = None
    last_testcase: str | None = None
    code_output: str | None = None
    expected_output: str | None = None


class BenchmarkEntry(BaseModel):
    solve: SolveResult
    submission: SubmissionResult | None = None