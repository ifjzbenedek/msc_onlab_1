import sys
sys.path.insert(0, ".")

import config
from src.clients import LeetCodeClient


def main() -> None:
    client = LeetCodeClient(graphql_url=config.LEETCODE_GRAPHQL_URL)

    slug = "two-sum"
    print(f"Fetching problem: {slug}\n")

    problem = client.fetch_problem(slug)

    print(f"ID:         {problem.id}")
    print(f"Title:      {problem.title}")
    print(f"Difficulty: {problem.difficulty}")
    print(f"\nPython3 code stub:\n{problem.code_stub}")

    print("\nAPI works!")


if __name__ == "__main__":
    main()
