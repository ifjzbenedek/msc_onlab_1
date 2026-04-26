"""Reads a compare_*.json and prints a (tag x pipeline) -> accepted/submitted table."""

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path", type=Path)
    parser.add_argument("--min-count", type=int, default=2,
                        help="Skip tags that appear in fewer than this many problems.")
    args = parser.parse_args()

    with open(args.json_path) as f:
        payload = json.load(f)

    pipelines: list[str] = payload["pipelines"]
    entries = payload["entries"]

    accepted: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    submitted: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    tag_counts: dict[str, int] = defaultdict(int)

    for entry in entries:
        for tag in entry.get("tags") or []:
            tag_counts[tag] += 1
            for pipe in pipelines:
                run = entry.get(pipe)
                if run is None or run.get("accepted") is None:
                    continue
                submitted[tag][pipe] += 1
                if run["accepted"]:
                    accepted[tag][pipe] += 1

    sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])
    header = ["tag", "n"] + pipelines
    widths = [max(len(h), 12) for h in header]

    print(f"Tag x Pipeline accepted/submitted (min {args.min_count} problems / tag)\n")
    print("  ".join(h.ljust(w) for h, w in zip(header, widths)))
    print("-" * (sum(widths) + 2 * len(widths)))

    for tag, n in sorted_tags:
        if n < args.min_count:
            continue
        row = [tag, str(n)]
        for pipe in pipelines:
            sub = submitted[tag][pipe]
            acc = accepted[tag][pipe]
            row.append(f"{acc}/{sub}" if sub else "-")
        print("  ".join(c.ljust(w) for c, w in zip(row, widths)))


if __name__ == "__main__":
    main()
