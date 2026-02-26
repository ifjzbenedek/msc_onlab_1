import argparse
import json
import random
import time
import sys
from pathlib import Path

sys.path.insert(0, ".")

import httpx

import config
from src.clients import OllamaClient, LeetCodeClient, LeetCodeSubmitter
from src.models import BenchmarkEntry, SolveResult, SubmissionResult
from src.prompts import WRITER_SYSTEM, writer_prompt
from src.utils import extract_code

RESULTS_DIR = Path("results")


def pick_problems(all_problems: list[dict], difficulty: str, n: int) -> list[dict]:
    pool = [p for p in all_problems if p["difficulty"] == difficulty and not p["paid_only"]]
    return random.sample(pool, min(n, len(pool)))


def generate_solution(slug: str, model: str, leetcode: LeetCodeClient, ollama: OllamaClient) -> tuple[SolveResult, str | None]:
    """returns (result, question_id) — question_id needed for submission"""
    problem = leetcode.fetch_problem(slug)

    start = time.time()
    try:
        raw = ollama.generate(model=model, prompt=writer_prompt(problem), system=WRITER_SYSTEM)
        elapsed = time.time() - start
        code = extract_code(raw)
    except Exception as e:
        elapsed = time.time() - start
        result = SolveResult(
            slug=slug, title=problem.title, difficulty=problem.difficulty,
            model=model, raw_response="", extracted_code=None,
            generation_seconds=round(elapsed, 1), error=str(e),
        )
        return result, problem.id

    result = SolveResult(
        slug=slug, title=problem.title, difficulty=problem.difficulty,
        model=model, raw_response=raw, extracted_code=code,
        generation_seconds=round(elapsed, 1),
    )
    return result, problem.id


def submit_solution(slug: str, question_id: str, code: str, submitter: LeetCodeSubmitter) -> SubmissionResult:
    raw = submitter.submit(slug=slug, question_id=question_id, code=code)
    return SubmissionResult(
        slug=slug,
        submission_id=raw["submission_id"],
        accepted=raw["status_code"] == 10,
        status=raw["status"],
        total_correct=raw["total_correct"],
        total_testcases=raw["total_testcases"],
        runtime_percentile=raw["runtime_percentile"],
        memory_percentile=raw["memory_percentile"],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5-coder:32b")
    parser.add_argument("--easy", type=int, default=10)
    parser.add_argument("--medium", type=int, default=10)
    parser.add_argument("--hard", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-submit", action="store_true", help="skip leetcode submission")
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

    print(f"\ntotal: {len(selected)} problems, model: {args.model}")
    if not args.no_submit:
        print("submissions: ON (results will be verified on leetcode)")
    print("=" * 60)

    leetcode = LeetCodeClient(graphql_url=config.LEETCODE_GRAPHQL_URL)
    ollama = OllamaClient(host=config.OLLAMA_HOST)
    submitter = None if args.no_submit else LeetCodeSubmitter(
        session_cookie=config.LEETCODE_SESSION,
        graphql_url=config.LEETCODE_GRAPHQL_URL,
    )

    entries: list[BenchmarkEntry] = []
    t0 = time.time()

    for i, p in enumerate(selected):
        print(f"\n[{i+1}/{len(selected)}] {p['title']} ({p['difficulty']})")

        # Generate solution and extract code block
        try:
            solve, question_id = generate_solution(p["slug"], args.model, leetcode, ollama)
        except Exception as e:
            print(f"  skip (fetch failed: {e})")
            continue

        if solve.error:
            print(f"  generation error: {solve.error}")
            entries.append(BenchmarkEntry(solve=solve))
            continue

        if solve.extracted_code:
            print(f"  generated in {solve.generation_seconds:.0f}s")
        else:
            print(f"  no code block found in response")
            entries.append(BenchmarkEntry(solve=solve))
            continue

        # Submit to LeetCod
        submission = None
        if submitter and solve.extracted_code:
            try:
                submission = submit_solution(p["slug"], question_id, solve.extracted_code, submitter)
                icon = "+" if submission.accepted else "x"
                print(f"  [{icon}] {submission.status} ({submission.total_correct}/{submission.total_testcases})")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    print(f"  skip (premium-only problem)")
                else:
                    print(f"  submit error: {e}")
            except Exception as e:
                print(f"  submit error: {e}")

        entries.append(BenchmarkEntry(solve=solve, submission=submission))

    total_time = time.time() - t0

    # Save into json (later I can turn it into an md table or something)
    RESULTS_DIR.mkdir(exist_ok=True)
    safe_model = args.model.replace(":", "_").replace("/", "_")
    out_path = RESULTS_DIR / f"benchmark_{safe_model}_{time.strftime('%Y%m%d_%H%M%S')}.json"

    payload = {
        "model": args.model,
        "seed": args.seed,
        "total_time_seconds": round(total_time, 1),
        "entries": [e.model_dump() for e in entries],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # Printsum
    print(f"\n{'=' * 60}")
    print(f"done in {total_time / 60:.1f} min — saved to {out_path}")

    for diff in ["Easy", "Medium", "Hard"]:
        group = [e for e in entries if e.solve.difficulty == diff]
        if not group:
            continue
        submitted = [e for e in group if e.submission]
        accepted = sum(1 for e in submitted if e.submission.accepted)
        avg_time = sum(e.solve.generation_seconds for e in group) / len(group)
        if submitted:
            print(f"  {diff}: {accepted}/{len(submitted)} accepted, avg generation {avg_time:.0f}s")
        else:
            print(f"  {diff}: {len(group)} generated, avg {avg_time:.0f}s (no submissions)")


if __name__ == "__main__":
    main()