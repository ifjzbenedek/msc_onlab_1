import argparse
import random
import subprocess
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.clients import SshTunnel

SKIP_MODELS = {
    "moondream", "minicpm-v", "llava", "llama3.2-vision",
    "tinyllama", "orca-mini",
}


def fetch_models(ollama_host: str) -> list[dict]:
    resp = httpx.get(f"{ollama_host}/api/tags", timeout=60)
    resp.raise_for_status()
    models = []
    for m in resp.json()["models"]:
        name = m["name"]
        base_name = name.split(":")[0]
        if base_name in SKIP_MODELS:
            continue
        size_gb = round(m["size"] / (1024 ** 3), 1)
        models.append({"name": name, "size_gb": size_gb})
    return models


def build_combinations(
    models: list[dict], max_size_gb: float,
) -> list[tuple[str, str]]:
    
    combos = []
    for w in models:
        for r in models:
            if w["name"] == r["name"]:
                continue
            if w["size_gb"] + r["size_gb"] <= max_size_gb:
                combos.append((w["name"], r["name"]))
    return combos


def select_combinations(
    combos: list[tuple[str, str]], max_combos: int, seed: int,
) -> list[tuple[str, str]]:
    
    random.seed(seed)
    random.shuffle(combos)
    return combos[:max_combos]


def run_comparison(
    writer: str,
    reviewer: str,
    easy: int,
    medium: int,
    hard: int,
    seed: int,
    max_iterations: int,
    lang: str = "python3",
) -> bool:

    cmd = [
        sys.executable,
        "scripts/compare_methods.py",
        "--writer-model", writer,
        "--reviewer-model", reviewer,
        "--easy", str(easy),
        "--medium", str(medium),
        "--hard", str(hard),
        "--seed", str(seed),
        "--max-iterations", str(max_iterations),
        "--lang", lang,
    ]
    print(f"")
    print(f"Running: {writer} + {reviewer} ({lang})")
    print(f"")

    result = subprocess.run(cmd, cwd=str(Path(__file__).resolve().parent.parent))
    return result.returncode == 0


def print_summary(results: list[tuple[str, str, bool]], total_time: float) -> None:

    print(f"")
    print(f"Exploration done in {total_time / 60:.1f} min")
    print(f"")
    for w, r, ok in results:
        status = "OK" if ok else "FAILED"
        print(f"  [{status}] {w} + {r}")


def resolve_ollama_host(cli_host: str | None) -> str:
    """Return the Ollama host from CLI arg or config."""
    if cli_host:
        return cli_host
    import config
    return config.OLLAMA_HOST


def main() -> None:
    parser = argparse.ArgumentParser(description="Explore model combinations")
    parser.add_argument("--max-combos", type=int, default=10,
                        help="Max number of combinations to try")
    parser.add_argument("--max-size-gb", type=float, default=22.0,
                        help="Max combined model file size in GB")
    parser.add_argument("--easy", type=int, default=5)
    parser.add_argument("--medium", type=int, default=5)
    parser.add_argument("--hard", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--ollama-host", default=None,
                        help="Ollama host URL (default: from config)")
    parser.add_argument("--lang", default="python3",
                        help="LeetCode langSlug (e.g. python3, java, cpp)")
    parser.add_argument("--no-tunnel", action="store_true",
                        help="Skip SSH tunnel (use if tunnel is already open)")
    args = parser.parse_args()

    import config

    tunnel = None
    if not args.no_tunnel:
        tunnel = SshTunnel(
            ssh_host=config.SSH_HOST,
            ssh_port=config.SSH_PORT,
            ssh_user=config.SSH_USER,
            remote_port=config.SSH_TUNNEL_REMOTE_PORT,
            local_port=config.SSH_TUNNEL_LOCAL_PORT,
        )
        tunnel.start()

    try:
        _run_exploration(args, tunnel)
    finally:
        if tunnel is not None:
            tunnel.stop()


def _run_exploration(args: argparse.Namespace, tunnel: SshTunnel | None) -> None:
    """Core exploration logic, wrapped so the tunnel is always cleaned up."""
    ollama_host = resolve_ollama_host(args.ollama_host)

    print(f"Fetching models from {ollama_host}...")
    models = fetch_models(ollama_host)
    print(f"Found {len(models)} usable models:")
    for m in sorted(models, key=lambda x: x["size_gb"], reverse=True):
        print(f"  {m['name']:30s} {m['size_gb']:.1f} GB")

    combos = build_combinations(models, args.max_size_gb)
    if not combos:
        print(f"\nNo valid combinations under {args.max_size_gb} GB")
        sys.exit(1)

    selected = select_combinations(combos, args.max_combos, args.seed)
    print(f"\n{len(combos)} valid combinations, running {len(selected)}:")
    for i, (w, r) in enumerate(selected):
        print(f"  {i + 1}. {w} + {r}")

    t0 = time.time()
    results = []

    for i, (writer, reviewer) in enumerate(selected):
        print(f"\n>>> Combination {i + 1}/{len(selected)}")

        if tunnel is not None:
            tunnel.ensure_alive()

        success = run_comparison(
            writer, reviewer,
            easy=args.easy, medium=args.medium, hard=args.hard,
            seed=args.seed, max_iterations=args.max_iterations,
            lang=args.lang,
        )
        results.append((writer, reviewer, success))

    print_summary(results, time.time() - t0)


if __name__ == "__main__":
    main()
