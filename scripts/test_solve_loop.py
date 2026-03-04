"""Full pipeline test — fetches a problem, runs ReviewerFix pipeline, submits to LeetCode."""

import logging
import sys
import time

sys.path.insert(0, ".")

import config
from src.clients import OllamaClient, LeetCodeClient, LeetCodeSubmitter
from src.agents import ReviewerFix
from src.models.config import SolveConfig

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

SLUG = "two-sum"
WRITER_MODEL = "qwen2.5-coder:32b"
REVIEWER_MODEL = "qwen2.5-coder:32b"


def main() -> None:
    print(f"=== Full pipeline test ===")
    print(f"Problem: {SLUG}")
    print(f"Writer:  {WRITER_MODEL}")
    print(f"Reviewer: {REVIEWER_MODEL}")
    print()

    leetcode = LeetCodeClient(graphql_url=config.LEETCODE_GRAPHQL_URL)
    ollama = OllamaClient(host=config.OLLAMA_HOST)
    submitter = LeetCodeSubmitter(
        session_cookie=config.LEETCODE_SESSION,
        graphql_url=config.LEETCODE_GRAPHQL_URL,
    )

    print("[1] Fetching problem...")
    problem = leetcode.fetch_problem(SLUG)
    print(f"    {problem.title} ({problem.difficulty}), id={problem.id}")

    cfg = SolveConfig(writer_model=WRITER_MODEL, reviewer_model=REVIEWER_MODEL, max_iterations=3)
    pipeline = ReviewerFix(ollama=ollama, config=cfg, submitter=submitter)

    print(f"[2] Running {pipeline.name}...")
    t0 = time.time()
    result = pipeline.run(problem)
    elapsed = time.time() - t0

    print(f"\n=== Results ({elapsed:.1f}s) ===")
    print(f"Reviews: {len(result.reviews)}")
    for r in result.reviews:
        status = "ACCEPT" if r.accepted else "REVISE"
        print(f"  #{r.message_number} [{r.model}]: {status}")

    if result.code:
        print(f"\nFinal code:\n{result.code}")
    else:
        print("\nNo code produced.")


if __name__ == "__main__":
    main()
