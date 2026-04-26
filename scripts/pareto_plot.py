"""Reads a compare_*.json and renders a (avg_time, accept_rate) scatter plot with the Pareto frontier highlighted."""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def _stack_close_labels(
    points: list[tuple[str, float, float]],
    x_thresh: float,
    y_thresh: float,
) -> dict[str, tuple[int, int]]:
    """Assign vertical offsets to labels of points that cluster within (x_thresh, y_thresh)."""
    offsets: dict[str, tuple[int, int]] = {}
    placed: list[tuple[float, float]] = []
    for name, t, acc in sorted(points, key=lambda p: (p[1], -p[2])):
        y_pct = acc * 100
        stack_idx = sum(
            1 for px, py in placed
            if abs(px - t) < x_thresh and abs(py - y_pct) < y_thresh
        )
        offsets[name] = (5, 5 + stack_idx * 11)
        placed.append((t, y_pct))
    return offsets


def pareto_frontier(points: list[tuple[str, float, float]]) -> set[str]:
    """Return the names of points on the (low time, high accuracy) Pareto frontier."""
    frontier: set[str] = set()
    for name, t, acc in points:
        dominated = any(
            t2 <= t and acc2 >= acc and (t2 < t or acc2 > acc)
            for n2, t2, acc2 in points if n2 != name
        )
        if not dominated:
            frontier.add(name)
    return frontier


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path", type=Path)
    parser.add_argument("--out", type=Path, default=None,
                        help="Output image path (default: alongside the JSON, .png).")
    args = parser.parse_args()

    with open(args.json_path) as f:
        payload = json.load(f)

    pipelines: list[str] = payload["pipelines"]
    entries = payload["entries"]

    points: list[tuple[str, float, float]] = []
    for pipe in pipelines:
        runs = [e[pipe] for e in entries if pipe in e and e[pipe].get("accepted") is not None]
        if not runs:
            continue
        avg_time = sum(r["time"] for r in runs) / len(runs)
        acc_rate = sum(1 for r in runs if r["accepted"]) / len(runs)
        points.append((pipe, avg_time, acc_rate))

    frontier = pareto_frontier(points)

    label_offsets = _stack_close_labels(points, x_thresh=2.0, y_thresh=1.5)

    fig, ax = plt.subplots(figsize=(10, 6))
    for name, t, acc in points:
        is_top = name in frontier
        ax.scatter(t, acc * 100, s=120 if is_top else 60,
                   c="#2F5496" if is_top else "#999999",
                   edgecolors="black" if is_top else "none",
                   zorder=3 if is_top else 2)
        ax.annotate(name, (t, acc * 100),
                    xytext=label_offsets[name], textcoords="offset points",
                    fontsize=8, color="black" if is_top else "gray")

    sorted_front = sorted([p for p in points if p[0] in frontier], key=lambda x: x[1])
    if len(sorted_front) >= 2:
        ax.plot([p[1] for p in sorted_front], [p[2] * 100 for p in sorted_front],
                "--", color="#2F5496", alpha=0.4, zorder=1)

    ax.set_xlabel("Avg time per problem (s)")
    ax.set_ylabel("Accept rate (%)")
    ax.set_title(f"Pareto frontier — {args.json_path.name}")
    ax.grid(True, alpha=0.3)

    out = args.out or args.json_path.with_suffix(".pareto.png")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"Saved: {out}")
    print(f"Pareto-optimal pipelines: {sorted(frontier)}")


if __name__ == "__main__":
    main()
