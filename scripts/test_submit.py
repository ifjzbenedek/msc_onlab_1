import sys
sys.path.insert(0, ".")

import config
from src.clients import LeetCodeClient, LeetCodeSubmitter

TWO_SUM_SOLUTION = """
class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}
        for i, n in enumerate(nums):
            diff = target - n
            if diff in seen:
                return [seen[diff], i]
            seen[n] = i
"""


def main() -> None:
    if not config.LEETCODE_SESSION:
        print("LEETCODE_SESSION not set in .env")
        sys.exit(1)

    leetcode = LeetCodeClient(graphql_url=config.LEETCODE_GRAPHQL_URL)
    submitter = LeetCodeSubmitter(
        session_cookie=config.LEETCODE_SESSION,
        graphql_url=config.LEETCODE_GRAPHQL_URL,
    )

    slug = "two-sum"
    problem = leetcode.fetch_problem(slug)
    print(f"Submitting known solution for: {problem.title}")

    result = submitter.submit(
        slug=slug,
        question_id=problem.id,
        code=TWO_SUM_SOLUTION,
    )

    print(f"\nStatus:     {result['status']}")
    print(f"Tests:      {result['total_correct']}/{result['total_testcases']}")
    print(f"Runtime:    top {result['runtime_percentile']:.0f}%")
    print(f"Memory:     top {result['memory_percentile']:.0f}%")


if __name__ == "__main__":
    main()