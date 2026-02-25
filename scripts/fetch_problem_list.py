import json
import sys
sys.path.insert(0, ".")

import config
from src.clients import LeetCodeClient


def main() -> None:
    client = LeetCodeClient(graphql_url=config.LEETCODE_GRAPHQL_URL)

    print("Fetching all LeetCode problems...")
    problems = client.fetch_problem_list()

    # Filter out paid-only problems (we can't access those)
    free = [p for p in problems if not p["paid_only"]]

    # Save to JSON
    out_path = "data/problem_list.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(free, f, indent=2, ensure_ascii=False)

    # Stats
    easy = sum(1 for p in free if p["difficulty"] == "Easy")
    medium = sum(1 for p in free if p["difficulty"] == "Medium")
    hard = sum(1 for p in free if p["difficulty"] == "Hard")

    print(f"\nTotal: {len(problems)} problems ({len(free)} free)")
    print(f"  Easy:   {easy}")
    print(f"  Medium: {medium}")
    print(f"  Hard:   {hard}")
    print(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
