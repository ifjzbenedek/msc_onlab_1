import logging
from typing import Optional

from src.clients.ollama_client import OllamaClient
from src.clients.leetcode_submitter import LeetCodeSubmitter
from src.models.config import SolveConfig
from src.models.problem import Problem
from src.models.result import ReviewerFeedback, SubmissionResult
from src.prompts import (
    WRITER_SYSTEM, writer_prompt,
    REVIEWER_SYSTEM, reviewer_prompt,
    writer_revision_prompt,
    writer_error_prompt,
)
from src.utils.parsers import extract_code, parse_review

log = logging.getLogger(__name__)


def solve_with_review(
    problem: Problem,
    ollama: OllamaClient,
    config: SolveConfig,
    submitter: Optional[LeetCodeSubmitter] = None,
) -> tuple[Optional[str], list[ReviewerFeedback], Optional[SubmissionResult]]:

    # First attempt
    raw = ollama.generate(
        model=config.writer_model,
        prompt=writer_prompt(problem),
        system=WRITER_SYSTEM,
    )
    code = extract_code(raw)

    if not code:
        log.warning("No code block in first response")
        return None, [], None

    reviews: list[ReviewerFeedback] = []
    last_sub: Optional[SubmissionResult] = None

    for i in range(config.max_iterations):
        # Review the current code
        review_raw = ollama.generate(
            model=config.reviewer_model,
            prompt=reviewer_prompt(problem, code),
            system=REVIEWER_SYSTEM,
        )
        accepted, feedback = parse_review(review_raw)

        reviews.append(ReviewerFeedback(
            accepted=accepted,
            feedback=feedback,
            model=config.reviewer_model,
            message_number=i + 1,
        ))

        log.info("Review #%d: %s", i + 1, "ACCEPT" if accepted else "REVISE")

        if accepted:
            if submitter:
                try:
                    last_sub = submitter.submit(problem.slug, problem.id, code)
                except Exception as e:
                    log.error("Submit failed: %s", e)
                    break

                # Compile or Runtime err
                if last_sub.status in ("Runtime Error", "Compile Error"):
                    error_type = last_sub.status
                    error_msg = last_sub.compile_error or last_sub.runtime_error or ""
                    log.info("Submit error: %s — retrying", error_type)

                    raw = ollama.generate(
                        model=config.writer_model,
                        prompt=writer_error_prompt(problem, code, error_type, error_msg),
                        system=WRITER_SYSTEM,
                    )
                    new_code = extract_code(raw)
                    if new_code:
                        code = new_code
                        continue
                    else:
                        log.warning("No code block after error fix attempt")

            break

        # Revise based on reviewer feedback
        raw = ollama.generate(
            model=config.writer_model,
            prompt=writer_revision_prompt(problem, code, feedback),
            system=WRITER_SYSTEM,
        )
        new_code = extract_code(raw)

        if not new_code:
            log.warning("No code block in revision #%d", i + 1)
            break

        code = new_code

    return code, reviews, last_sub