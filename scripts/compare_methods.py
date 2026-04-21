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
from src.agents import (
    AgentPipeline, Baseline, BaselineFix, Reviewer, ReviewerFix,
    BestOfN, SelfReflection, PeerReview, HierarchicalReview,
    Debate, CoopetitionMerge, PlannerCoder, Orchestrator,
    LLMRouter, RuleRouter, WeightedMajority,
)
from src.utils import ReportGenerator
from src.models.config import SolveConfig
from src.models.pipeline_run_result import PipelineRunResult

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

RESULTS_DIR = Path("results")

DEFAULT_WRITER_MODEL = "qwen2.5-coder:14b"
DEFAULT_REVIEWER_MODEL = "gemma2:9b"


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

    voting_stats = result.voting_stats

    if not result.code:
        print(f"  [{pipeline.name}] no code ({elapsed:.0f}s)")
        return PipelineRunResult(time=elapsed, status="no code", voting_stats=voting_stats)

    if not result.submission:
        print(f"  [{pipeline.name}] generated ({elapsed:.0f}s{review_info})")
        return PipelineRunResult(
            time=elapsed, status="not submitted", num_reviews=reviews,
            voting_stats=voting_stats,
        )

    icon = "+" if result.submission.accepted else "x"
    print(f"  [{pipeline.name}] [{icon}] {result.submission.status} ({elapsed:.0f}s{review_info})")
    return PipelineRunResult(
        time=elapsed,
        accepted=result.submission.accepted,
        status=result.submission.status,
        num_reviews=reviews,
        voting_stats=voting_stats,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare baseline vs reviewer-loop")
    parser.add_argument("--easy", type=int, default=10)
    parser.add_argument("--medium", type=int, default=10)
    parser.add_argument("--hard", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--writer-model", default=DEFAULT_WRITER_MODEL)
    parser.add_argument("--reviewer-model", default=DEFAULT_REVIEWER_MODEL)
    parser.add_argument("--lang", default="python3",
                        help="LeetCode langSlug (e.g. python3, java, cpp)")
    parser.add_argument("--quick-reviewer-model", default=None,
                        help="Small model for hierarchical quick review (defaults to reviewer)")
    parser.add_argument("--judge-model", default=None,
                        help="Model for debate judge / merge (defaults to reviewer)")
    parser.add_argument("--voting-runs", type=int, default=0,
                        help="If >0, add BestOfN wrapper for each pipeline with N runs")
    parser.add_argument("--only-pipelines", default=None,
                        help="Comma-separated pipeline names to run (default: all). "
                             "Does not affect the WeightedMajority pool — WM always uses all 12.")
    parser.add_argument("--weighted-majority-beta", type=float, default=None,
                        help="If set, add a WeightedMajority ensemble with this beta.")
    parser.add_argument("--weighted-majority-pool", default=None,
                        help="Comma-separated pipeline names for WM pool (default: all 12). "
                             "Independent from --only-pipelines.")
    args = parser.parse_args()

    writer_model = args.writer_model
    reviewer_model = args.reviewer_model
    quick_reviewer_model = args.quick_reviewer_model or reviewer_model
    judge_model = args.judge_model or reviewer_model
    lang = args.lang

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
    print(f"Writer:          {writer_model}")
    print(f"Reviewer:        {reviewer_model}")
    print(f"Quick reviewer:  {quick_reviewer_model}")
    print(f"Judge:           {judge_model}")
    print(f"Language:        {lang}")
    print("=" * 60)

    leetcode = LeetCodeClient(graphql_url=config.LEETCODE_GRAPHQL_URL)
    ollama = OllamaClient(host=config.OLLAMA_HOST)
    submitter = LeetCodeSubmitter(
        session_cookie=config.LEETCODE_SESSION,
        graphql_url=config.LEETCODE_GRAPHQL_URL,
    )

    cfg = SolveConfig(
        writer_model=writer_model,
        reviewer_model=reviewer_model,
        max_iterations=args.max_iterations,
    )

    orchestrator_inner = {
        "baseline": Baseline(ollama, writer_model, submitter),
        "baseline+fix": BaselineFix(ollama, writer_model, submitter),
        "reviewer": Reviewer(ollama, cfg, submitter),
        "reviewer+fix": ReviewerFix(ollama, cfg, submitter),
    }

    base_pipelines: list[AgentPipeline] = [
        Baseline(ollama, writer_model, submitter),
        BaselineFix(ollama, writer_model, submitter),
        Reviewer(ollama, cfg, submitter),
        ReviewerFix(ollama, cfg, submitter),
        SelfReflection(ollama, writer_model, submitter),
        PeerReview(ollama, cfg, [reviewer_model] * 3, submitter),
        HierarchicalReview(ollama, cfg, quick_reviewer_model, reviewer_model, submitter),
        Debate(ollama, writer_model, writer_model, judge_model, submitter),
        CoopetitionMerge(ollama, writer_model, writer_model, judge_model, submitter),
        PlannerCoder(ollama, writer_model, writer_model, submitter),
        Orchestrator(orchestrator_inner, LLMRouter(ollama, reviewer_model), name="orchestrator-llm"),
        Orchestrator(orchestrator_inner, RuleRouter({"Easy": "baseline", "Medium": "baseline+fix", "Hard": "reviewer+fix"}), name="orchestrator-rule"),
    ]

    if args.only_pipelines:
        wanted = {n.strip() for n in args.only_pipelines.split(",") if n.strip()}
        known = {p.name for p in base_pipelines}
        unknown = wanted - known
        if unknown:
            print(f"Unknown pipeline names in --only-pipelines: {sorted(unknown)}")
            print(f"Known: {sorted(known)}")
            sys.exit(1)
        pipelines: list[AgentPipeline] = [p for p in base_pipelines if p.name in wanted]
    else:
        pipelines = list(base_pipelines)

    if args.weighted_majority_beta is not None:
        if args.weighted_majority_pool:
            wm_wanted = {n.strip() for n in args.weighted_majority_pool.split(",") if n.strip()}
            known = {p.name for p in base_pipelines}
            unknown = wm_wanted - known
            if unknown:
                print(f"Unknown pipeline names in --weighted-majority-pool: {sorted(unknown)}")
                print(f"Known: {sorted(known)}")
                sys.exit(1)
            wm_pool = [p for p in base_pipelines if p.name in wm_wanted]
        else:
            wm_pool = list(base_pipelines)
        pipelines.append(WeightedMajority(
            pipelines=wm_pool,
            beta=args.weighted_majority_beta,
            seed=args.seed,
        ))

    if args.voting_runs > 0:
        for p in list(pipelines):
            pipelines.append(BestOfN(p, runs=args.voting_runs))

    pipeline_names = [p.name for p in pipelines]
    t0 = time.time()

    # Fetch all problems upfront
    problems: list[tuple[dict, object]] = []
    for i, p in enumerate(selected):
        try:
            problem = leetcode.fetch_problem(p["slug"], lang=lang)
            problems.append((p, problem))
        except Exception as e:
            print(f"  skip {p['title']} (fetch failed: {e})")

    # Run pipeline-by-pipeline to minimise model swaps
    pipeline_results: dict[str, dict[str, PipelineRunResult]] = {
        p["slug"]: {} for p, _ in problems
    }

    for pi, pipeline in enumerate(pipelines):
        print(f"\n{'=' * 40}")
        print(f"Pipeline: {pipeline.name} ({len(problems)} problems)")
        print(f"{'=' * 40}")

        for i, (p, problem) in enumerate(problems):
            print(f"  [{i+1}/{len(problems)}] {p['title']} ({p['difficulty']})")
            result = run_pipeline(pipeline, problem)
            pipeline_results[p["slug"]][pipeline.name] = result
            if i < len(problems) - 1:
                time.sleep(8)

        if pi < len(pipelines) - 1:
            time.sleep(15)

    # Assemble results in the original format
    results = []
    for p, _ in problems:
        entry = {"slug": p["slug"], "title": p["title"], "difficulty": p["difficulty"]}
        for name in pipeline_names:
            if name in pipeline_results[p["slug"]]:
                entry[name] = pipeline_results[p["slug"]][name].model_dump()
        results.append(entry)

    # Save results to JSON
    total_time = time.time() - t0
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"compare_{time.strftime('%Y%m%d_%H%M%S')}.json"

    payload = {
        "writer_model": writer_model,
        "reviewer_model": reviewer_model,
        "lang": lang,
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
