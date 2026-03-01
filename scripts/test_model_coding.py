import argparse
import time
import sys
sys.path.insert(0, ".")

import config
from src.clients import OllamaClient, LeetCodeClient
from src.prompts import WRITER_SYSTEM, writer_prompt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5-coder:14b", help="Model to test")
    parser.add_argument("--slug", default="two-sum", help="LeetCode problem slug")
    args = parser.parse_args()

    # Fetch the problem from LeetCode
    leetcode = LeetCodeClient(graphql_url=config.LEETCODE_GRAPHQL_URL)
    problem = leetcode.fetch_problem(args.slug)

    print(f"Problem: {problem.title} ({problem.difficulty})")
    print(f"Model:   {args.model}")
    print("─" * 50)

    ollama = OllamaClient(host=config.OLLAMA_HOST)

    print("\nWaiting for model response...")
    start = time.time()
    response = ollama.generate(
        model=args.model,
        prompt=writer_prompt(problem),
        system=WRITER_SYSTEM,
        temperature=0.2,
    )
    elapsed = time.time() - start

    print(f"Time: {elapsed:.1f}s")
    print(f"\n{'─' * 50}")
    print("Model output:")
    print(f"{'─' * 50}")
    print(response)


if __name__ == "__main__":
    main()