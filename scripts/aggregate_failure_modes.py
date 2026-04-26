"""Reads a compare_*.json and prints a (pipeline x failure-mode) count table from the LeetCode status fields."""

import argparse
import json
from collections import defaultdict
from pathlib import Path


CATEGORIES = [
    "Accepted",
    "Wrong Answer",
    "Runtime Error",
    "Time Limit Exceeded",
    "Memory Limit Exceeded",
    "Compile Error",
    "Output Limit Exceeded",
    "Internal Error",
]


def categorize(status: str) -> str:
    for cat in CATEGORIES:
        if cat in status:
            return cat
    if status.startswith("HTTP"):
        return "HTTP error"
    return "Other"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path", type=Path)
    args = parser.parse_args()

    with open(args.json_path) as f:
        payload = json.load(f)

    pipelines: list[str] = payload["pipelines"]
    entries = payload["entries"]

    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for entry in entries:
        for pipe in pipelines:
            run = entry.get(pipe)
            if run is None:
                continue
            counts[pipe][categorize(run.get("status", "Other"))] += 1

    used_categories = sorted(
        {cat for pipe in counts.values() for cat in pipe.keys()},
        key=lambda c: (CATEGORIES.index(c) if c in CATEGORIES else 999, c),
    )

    name_w = max(len(p) for p in pipelines) + 2
    cat_w = max(max(len(c) for c in used_categories), 6) + 2

    header = "pipeline".ljust(name_w) + "".join(c.rjust(cat_w) for c in used_categories)
    print(header)
    print("-" * len(header))
    for pipe in pipelines:
        row = pipe.ljust(name_w) + "".join(
            str(counts[pipe].get(c, 0)).rjust(cat_w) for c in used_categories
        )
        print(row)


if __name__ == "__main__":
    main()
