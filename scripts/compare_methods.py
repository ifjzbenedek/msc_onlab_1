"""Compare baseline (single-shot) vs reviewer-loop on the same random problems."""

import argparse
import json
import random
import time
import sys
from pathlib import Path

sys.path.insert(0, ".")

import logging

import httpx
import config
from src.clients import OllamaClient, LeetCodeClient, LeetCodeSubmitter
from src.agents import Baseline, BaselineFix, Reviewer, ReviewerFix, AgentPipeline
from src.utils import ReportGenerator
from src.models.config import SolveConfig
from src.models.pipeline_run_result import PipelineRunResult

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

RESULTS_DIR = Path("results")

WRITER_MODEL = "qwen2.5-coder:14b"
REVIEWER_MODEL = "gemma2:9b"


def pick_problems(all_problems: list[dict], difficulty: str, n: int) -> list[dict]:
    pool = [p for p in all_problems if p["difficulty"] == difficulty and not p["paid_only"]]
    return random.sample(pool, min(n, len(pool)))


def run_pipeline(pipeline: AgentPipeline, problem) -> PipelineRunResult:
    t0 = time.time()
    try:
        result = pipeline.run(problem)
    except httpx.HTTPStatusError as e:
        short = f"HTTP {e.response.status_code}"
        print(f"  [{pipeline.name}] error: {short}")
        return PipelineRunResult(time=round(time.time() - t0, 1), status=short)
    except Exception as e:
        short = str(e).split("\n")[0][:80]
        print(f"  [{pipeline.name}] error: {short}")
        return PipelineRunResult(time=round(time.time() - t0, 1), status=short)
    elapsed = round(time.time() - t0, 1)

    reviews = len(result.reviews)
    review_info = f", {reviews} reviews" if reviews else ""

    if not result.code:
        print(f"  [{pipeline.name}] no code ({elapsed:.0f}s)")
        return PipelineRunResult(time=elapsed, status="no code")

    if not result.submission:
        print(f"  [{pipeline.name}] generated ({elapsed:.0f}s{review_info})")
        return PipelineRunResult(time=elapsed, status="not submitted", num_reviews=reviews)

    icon = "+" if result.submission.accepted else "x"
    print(f"  [{pipeline.name}] [{icon}] {result.submission.status} ({elapsed:.0f}s{review_info})")
    return PipelineRunResult(
        time=elapsed,
        accepted=result.submission.accepted,
        status=result.submission.status,
        num_reviews=reviews,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare baseline vs reviewer-loop")
    parser.add_argument("--easy", type=int, default=10)
    parser.add_argument("--medium", type=int, default=10)
    parser.add_argument("--hard", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-iterations", type=int, default=3)
    args = parser.parse_args()

    random.seed(args.seed)

    data_path = Path("data/problem_list.json")
    if not data_path.exists():
        print("data/problem_list.json not found — run scripts/fetch_problem_list.py first")
        sys.exit(1)

    with open(data_path) as f:
        all_problems = json.load(f)

    selected: list[dict] = []
    for diff, n in [("Easy", args.easy), ("Medium", args.medium), ("Hard", args.hard)]:
        picked = pick_problems(all_problems, diff, n)
        print(f"{diff}: {len(picked)} problems")
        selected.extend(picked)

    print(f"\nTotal: {len(selected)} problems")
    print(f"Writer:   {WRITER_MODEL}")
    print(f"Reviewer: {REVIEWER_MODEL}")
    print("=" * 60)

    leetcode = LeetCodeClient(graphql_url=config.LEETCODE_GRAPHQL_URL)
    ollama = OllamaClient(host=config.OLLAMA_HOST)
    submitter = LeetCodeSubmitter(
        session_cookie=config.LEETCODE_SESSION,
        graphql_url=config.LEETCODE_GRAPHQL_URL,
    )

    cfg = SolveConfig(
        writer_model=WRITER_MODEL,
        reviewer_model=REVIEWER_MODEL,
        max_iterations=args.max_iterations,
    )

    pipelines: list[AgentPipeline] = [
        Baseline(ollama, WRITER_MODEL, submitter),
        BaselineFix(ollama, WRITER_MODEL, submitter),
        Reviewer(ollama, cfg, submitter),
        ReviewerFix(ollama, cfg, submitter),
    ]

    pipeline_names = [p.name for p in pipelines]
    results = []
    t0 = time.time()

    for i, p in enumerate(selected):
        print(f"\n[{i+1}/{len(selected)}] {p['title']} ({p['difficulty']})")

        try:
            problem = leetcode.fetch_problem(p["slug"])
        except Exception as e:
            print(f"  skip (fetch failed: {e})")
            continue

        entry = {"slug": p["slug"], "title": p["title"], "difficulty": p["difficulty"]}

        for pipeline in pipelines:
            print(f"  [{pipeline.name}] running...")
            entry[pipeline.name] = run_pipeline(pipeline, problem).model_dump()

        results.append(entry)

    # Save results to JSON
    total_time = time.time() - t0
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"compare_{time.strftime('%Y%m%d_%H%M%S')}.json"

    payload = {
        "writer_model": WRITER_MODEL,
        "reviewer_model": REVIEWER_MODEL,
        "seed": args.seed,
        "max_iterations": args.max_iterations,
        "total_time_seconds": round(total_time, 1),
        "pipelines": pipeline_names,
        "entries": results,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # Console summary
    print(f"\n{'=' * 60}")
    print(f"Done in {total_time / 60:.1f} min — saved to {out_path}\n")

    for diff in ["Easy", "Medium", "Hard"]:
        group = [e for e in results if e["difficulty"] == diff]
        if not group:
            continue
        print(f"  {diff}:")
        for name in pipeline_names:
            submitted = [e for e in group if e.get(name, {}).get("accepted") is not None]
            accepted = sum(1 for e in submitted if e[name]["accepted"])
            avg_time = sum(e[name]["time"] for e in group if name in e) / len(group)
            print(f"    {name:15s}  {accepted}/{len(submitted)} accepted, avg {avg_time:.0f}s")
        print()


    # Generate Markdown report
    md_path = out_path.with_suffix(".md")
    report = ReportGenerator(payload)
    md_path.write_text(report.generate(), encoding="utf-8")
    print(f"Report: {md_path}")


if __name__ == "__main__":
    main()
