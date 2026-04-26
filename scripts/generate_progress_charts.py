"""Generate PNG charts for PROGRESS.md from result data."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = Path("docs/charts")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Dark-themed style
plt.style.use("dark_background")
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#888"
plt.rcParams["axes.labelcolor"] = "#ddd"
plt.rcParams["xtick.color"] = "#ddd"
plt.rcParams["ytick.color"] = "#ddd"
plt.rcParams["axes.titlecolor"] = "#fff"
plt.rcParams["figure.facecolor"] = "#1e1e1e"
plt.rcParams["axes.facecolor"] = "#252526"


# ============================================================
# Chart 1: Language comparison (acceptance rate per pipeline)
# ============================================================
def chart_language_comparison() -> None:
    pipelines = ["baseline", "baseline+fix", "reviewer", "reviewer+fix"]
    py = [83, 67, 67, 83]
    cpp = [83, 83, 83, 83]
    java = [67, 83, 83, 67]

    x = np.arange(len(pipelines))
    width = 0.27

    fig, ax = plt.subplots(figsize=(10, 5.5))
    b1 = ax.bar(x - width, py, width, label="Python3", color="#3776ab")
    b2 = ax.bar(x, cpp, width, label="C++", color="#f34b7d")
    b3 = ax.bar(x + width, java, width, label="Java", color="#e48b1c")

    ax.set_ylabel("Acceptance Rate (%)", fontsize=11)
    ax.set_title("Acceptance rate by pipeline & language\n(qwen2.5-coder:32b + gemma3:27b, 6 problems)",
                 fontsize=13, pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(pipelines, fontsize=10)
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, fontsize=10)
    ax.grid(axis="y", alpha=0.2, linestyle="--")
    ax.set_axisbelow(True)

    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 1.5, f"{h}%",
                    ha="center", va="bottom", fontsize=9, color="#ddd")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "language_comparison.png", dpi=140, bbox_inches="tight")
    plt.close()
    print(f"  saved {OUT_DIR / 'language_comparison.png'}")


# ============================================================
# Chart 2: Language comparison — average runtime
# ============================================================
def chart_language_runtime_no_swap() -> None:
    """Comparison: measured time vs estimated 'no-swap' time per pipeline & language."""
    pipelines = ["reviewer", "reviewer+fix"]
    langs = ["Python3", "C++", "Java"]

    measured = {
        "Python3": [229.2, 337.1],
        "C++": [338.0, 491.0],
        "Java": [221.7, 343.1],
    }
    no_swap = {
        "Python3": [95, 143],
        "C++": [50, 75],
        "Java": [49, 73],
    }

    n = len(pipelines)
    width = 0.13
    x = np.arange(n)
    colors_meas = {"Python3": "#3776ab", "C++": "#f34b7d", "Java": "#e48b1c"}
    colors_clean = {"Python3": "#7fbcff", "C++": "#ff7fa3", "Java": "#ffb960"}

    fig, ax = plt.subplots(figsize=(11, 6))
    for li, lang in enumerate(langs):
        offset = (li - 1) * (2.5 * width)
        ax.bar(x + offset - width / 2, measured[lang], width,
               color=colors_meas[lang], label=f"{lang} measured")
        ax.bar(x + offset + width / 2, no_swap[lang], width,
               color=colors_clean[lang], hatch="..", edgecolor="white", linewidth=0,
               label=f"{lang} no-swap (calc.)")

    ax.set_ylabel("Avg runtime per problem (s)", fontsize=11)
    ax.set_title("Measured runtime vs no-swap calculation\n"
                 "(qwen2.5-coder:32b + gemma3:27b → 34 GB on 24 GB GPU)",
                 fontsize=13, pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(pipelines, fontsize=11)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper right")
    ax.grid(axis="y", alpha=0.2, linestyle="--")
    ax.set_axisbelow(True)

    # Annotate
    for li, lang in enumerate(langs):
        offset = (li - 1) * (2.5 * width)
        for i in range(n):
            ax.text(i + offset - width / 2, measured[lang][i] + 8,
                    f"{measured[lang][i]:.0f}", ha="center", fontsize=7.5, color="#ddd")
            ax.text(i + offset + width / 2, no_swap[lang][i] + 8,
                    f"{no_swap[lang][i]:.0f}", ha="center", fontsize=7.5, color="#bbb")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "language_runtime_no_swap.png", dpi=140, bbox_inches="tight")
    plt.close()
    print(f"  saved {OUT_DIR / 'language_runtime_no_swap.png'}")


def chart_language_runtime() -> None:
    """Stacked bar: pure compute vs model-swap overhead per pipeline & language.

    Per-call cost is derived from baseline+fix (no swap, ~1.5 calls on average):
      per_call ≈ baseline+fix / 1.5

    Compute per pipeline:
      baseline       = 1  call
      baseline+fix   = 1.5 calls
      reviewer       = 4  calls (2W + 2R)
      reviewer+fix   = 6  calls (3W + 2R + 1 fix)

    Swap overhead = measured - compute.
    """
    pipelines = ["baseline", "baseline+fix", "reviewer", "reviewer+fix"]
    langs = ["Python3", "C++", "Java"]

    # baseline+fix is pure-writer compute, ~1.5 calls
    bfix = {"Python3": 35.7, "C++": 18.7, "Java": 18.2}
    per_call = {l: bfix[l] / 1.5 for l in langs}

    n_calls = {
        "baseline": 1.0,
        "baseline+fix": 1.5,
        "reviewer": 4.0,
        "reviewer+fix": 6.0,
    }

    measured = {
        "Python3": [137.6, 35.7, 229.2, 337.1],
        "C++":     [40.7,  18.7, 338.0, 491.0],
        "Java":    [136.4, 18.2, 221.7, 343.1],
    }

    # Compute and swap per (lang, pipeline)
    compute = {l: [round(per_call[l] * n_calls[p], 1) for p in pipelines] for l in langs}
    swap = {l: [max(0, m - c) for m, c in zip(measured[l], compute[l])] for l in langs}

    width = 0.26
    x = np.arange(len(pipelines))
    offsets = {"Python3": -width, "C++": 0, "Java": width}
    base_colors = {"Python3": "#3776ab", "C++": "#f34b7d", "Java": "#e48b1c"}

    fig, ax = plt.subplots(figsize=(13, 6.5))

    for lang in langs:
        ax.bar(x + offsets[lang], compute[lang], width,
               color=base_colors[lang], edgecolor="#1e1e1e", linewidth=0.5,
               label=f"{lang} — compute")
        ax.bar(x + offsets[lang], swap[lang], width, bottom=compute[lang],
               color=base_colors[lang], alpha=0.4, hatch="//",
               edgecolor="white", linewidth=0,
               label=f"{lang} — model-swap overhead")

    # Total annotations
    for lang in langs:
        for i, m in enumerate(measured[lang]):
            ax.text(i + offsets[lang], m + 10, f"{m:.0f}s",
                    ha="center", fontsize=8, color="#ddd")
        # Compute-only label inside the solid block (only when there's swap on top)
        for i, (c, s) in enumerate(zip(compute[lang], swap[lang])):
            if s > 20 and c > 25:
                ax.text(i + offsets[lang], c / 2, f"{c:.0f}",
                        ha="center", va="center", fontsize=7.5, color="white", fontweight="bold")

    ax.set_ylabel("Avg runtime per problem (s)", fontsize=11)
    ax.set_title("Runtime breakdown per pipeline & language — pure compute vs model-swap overhead\n"
                 "(qwen2.5-coder:32b + gemma3:27b → 34 GB on a 24 GB RTX 3090)",
                 fontsize=13, pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(pipelines, fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=9, ncol=3, loc="upper left")
    ax.grid(axis="y", alpha=0.2, linestyle="--")
    ax.set_axisbelow(True)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(OUT_DIR / "language_runtime.png", dpi=140, bbox_inches="tight")
    plt.close()
    print(f"  saved {OUT_DIR / 'language_runtime.png'}")


# ============================================================
# Chart 3: Pipeline leaderboard (12 pipelines, total acceptance)
# ============================================================
def chart_pipeline_leaderboard() -> None:
    data_path = Path("results/compare_20260413_003938.json")
    if not data_path.exists():
        print(f"  skip — {data_path} not found")
        return

    d = json.loads(data_path.read_text())
    pipelines = d["pipelines"]
    totals = []
    for p in pipelines:
        accepted = sum(1 for e in d["entries"] if p in e and e[p].get("accepted"))
        totals.append((p, accepted, len(d["entries"])))

    totals.sort(key=lambda r: r[1], reverse=True)
    names = [t[0] for t in totals]
    counts = [t[1] for t in totals]
    pcts = [100 * c / totals[0][2] for c in counts]

    # Highlight winner
    colors = ["#4caf50" if i == 0 else "#5a7fc4" for i in range(len(names))]

    fig, ax = plt.subplots(figsize=(10, 6.5))
    bars = ax.barh(names, pcts, color=colors)
    ax.invert_yaxis()
    ax.set_xlabel("Acceptance Rate (%)", fontsize=11)
    ax.set_title("Pipeline leaderboard — Total acceptance across 15 problems\n"
                 "(qwen2.5-coder:14b + gemma2:9b, Python3, seed=123)",
                 fontsize=13, pad=15)
    ax.set_xlim(0, 100)
    ax.grid(axis="x", alpha=0.2, linestyle="--")
    ax.set_axisbelow(True)

    for bar, c, p in zip(bars, counts, pcts):
        ax.text(p + 1, bar.get_y() + bar.get_height() / 2,
                f"{c}/15  ({p:.0f}%)", va="center", fontsize=9, color="#ddd")

    # Annotate winner
    ax.text(pcts[0] + 1, -0.6, "★ winner", color="#4caf50",
            fontsize=11, fontweight="bold")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "pipeline_leaderboard.png", dpi=140, bbox_inches="tight")
    plt.close()
    print(f"  saved {OUT_DIR / 'pipeline_leaderboard.png'}")


# ============================================================
# Chart 4: Pipeline acceptance per difficulty
# ============================================================
def chart_pipeline_per_difficulty() -> None:
    data_path = Path("results/compare_20260413_003938.json")
    if not data_path.exists():
        return

    d = json.loads(data_path.read_text())
    pipelines = d["pipelines"]
    difficulties = ["Easy", "Medium", "Hard"]

    # Order by total acceptance (best first)
    totals = {p: sum(1 for e in d["entries"] if p in e and e[p].get("accepted")) for p in pipelines}
    pipelines_sorted = sorted(pipelines, key=lambda p: totals[p], reverse=True)

    by_diff = {p: {diff: [0, 0] for diff in difficulties} for p in pipelines}
    for e in d["entries"]:
        diff = e["difficulty"]
        for p in pipelines:
            if p in e:
                by_diff[p][diff][1] += 1
                if e[p].get("accepted"):
                    by_diff[p][diff][0] += 1

    n = len(pipelines_sorted)
    x = np.arange(n)
    width = 0.27

    easy = [by_diff[p]["Easy"][0] for p in pipelines_sorted]
    med = [by_diff[p]["Medium"][0] for p in pipelines_sorted]
    hard = [by_diff[p]["Hard"][0] for p in pipelines_sorted]

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.bar(x - width, easy, width, label="Easy", color="#4caf50")
    ax.bar(x, med, width, label="Medium", color="#ffb300")
    ax.bar(x + width, hard, width, label="Hard", color="#e53935")

    ax.set_ylabel("Accepted (out of 5)", fontsize=11)
    ax.set_title("Pipeline acceptance by difficulty\n(qwen2.5-coder:14b + gemma2:9b, Python3)",
                 fontsize=13, pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(pipelines_sorted, rotation=35, ha="right", fontsize=9)
    ax.set_ylim(0, 5.5)
    ax.set_yticks(range(0, 6))
    ax.legend(frameon=False, fontsize=10)
    ax.grid(axis="y", alpha=0.2, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(OUT_DIR / "pipeline_per_difficulty.png", dpi=140, bbox_inches="tight")
    plt.close()
    print(f"  saved {OUT_DIR / 'pipeline_per_difficulty.png'}")


# ============================================================
# Chart 5: Pipeline runtime vs accuracy scatter
# ============================================================
def chart_runtime_vs_accuracy() -> None:
    data_path = Path("results/compare_20260413_003938.json")
    if not data_path.exists():
        return

    d = json.loads(data_path.read_text())
    pipelines = d["pipelines"]

    points = []
    for p in pipelines:
        times = [e[p]["time"] for e in d["entries"] if p in e]
        accepted = sum(1 for e in d["entries"] if p in e and e[p].get("accepted"))
        points.append((p, sum(times) / len(times), 100 * accepted / len(times)))

    fig, ax = plt.subplots(figsize=(10, 6.5))
    for name, t, acc in points:
        color = "#4caf50" if acc >= 65 else ("#ffb300" if acc >= 50 else "#e53935")
        ax.scatter(t, acc, s=170, color=color, edgecolors="white", linewidths=1.2, zorder=3)
        ax.annotate(name, (t, acc), xytext=(8, 6), textcoords="offset points",
                    fontsize=9, color="#ddd")

    ax.set_xlabel("Average runtime per problem (s)", fontsize=11)
    ax.set_ylabel("Acceptance Rate (%)", fontsize=11)
    ax.set_title("Runtime vs Accuracy trade-off\n(green = best, yellow = average, red = worst)",
                 fontsize=13, pad=15)
    ax.grid(alpha=0.2, linestyle="--")
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(OUT_DIR / "runtime_vs_accuracy.png", dpi=140, bbox_inches="tight")
    plt.close()
    print(f"  saved {OUT_DIR / 'runtime_vs_accuracy.png'}")


if __name__ == "__main__":
    print("Generating charts...")
    chart_language_comparison()
    chart_language_runtime()
    chart_pipeline_leaderboard()
    chart_pipeline_per_difficulty()
    chart_runtime_vs_accuracy()
    print("Done.")
