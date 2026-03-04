import argparse
import sys
from pathlib import Path

sys.path.insert(0, ".")

from src.utils import ReportGenerator


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate markdown report from JSON")
    parser.add_argument("json_file", type=Path, help="Path to comparison JSON file")
    args = parser.parse_args()

    if not args.json_file.exists():
        print(f"File not found: {args.json_file}")
        sys.exit(1)

    report = ReportGenerator.from_json(args.json_file)
    md = report.generate()

    out_path = args.json_file.with_suffix(".md")
    out_path.write_text(md, encoding="utf-8")
    print(f"Report saved to {out_path}")


if __name__ == "__main__":
    main()