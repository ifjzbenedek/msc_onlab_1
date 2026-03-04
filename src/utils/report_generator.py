import json
from pathlib import Path


class ReportGenerator:

    def __init__(self, data: dict) -> None:
        self.data = data
        self.entries = data["entries"]
        self.pipeline_names: list[str] = data["pipelines"]

    def generate(self) -> str:
        lines = [
            "# Comparison Report",
            "",
            f"- **Writer model**: {self.data.get('writer_model', '?')}",
            f"- **Reviewer model**: {self.data.get('reviewer_model', '?')}",
            f"- **Seed**: {self.data.get('seed', '?')}",
            f"- **Max iterations**: {self.data.get('max_iterations', '?')}",
            f"- **Total time**: {self.data.get('total_time_seconds', 0) / 60:.1f} min",
            "",
        ]

        lines.append(self._summary_table())
        lines.append(self._details_table())

        return "\n".join(lines)

    def _summary_table(self) -> str:
        lines = ["## Summary", ""]

        header = "| Difficulty | " + " | ".join(self.pipeline_names) + " |"
        separator = "|---|" + "|".join(["---"] * len(self.pipeline_names)) + "|"
        lines.extend([header, separator])

        for diff in ["Easy", "Medium", "Hard"]:
            group = [e for e in self.entries if e["difficulty"] == diff]
            if not group:
                continue
            cells = [diff]
            for name in self.pipeline_names:
                submitted = [e for e in group if e.get(name, {}).get("accepted") is not None]
                accepted = sum(1 for e in submitted if e[name]["accepted"])
                cells.append(f"{accepted}/{len(submitted)}")
            lines.append("| " + " | ".join(cells) + " |")

        total_cells = ["**Total**"]
        for name in self.pipeline_names:
            submitted = [e for e in self.entries if e.get(name, {}).get("accepted") is not None]
            accepted = sum(1 for e in submitted if e[name]["accepted"])
            total_cells.append(f"**{accepted}/{len(submitted)}**")
        lines.append("| " + " | ".join(total_cells) + " |")

        lines.append("")
        return "\n".join(lines)

    def _details_table(self) -> str:
        lines = ["## Details", ""]

        header = "| # | Problem | Difficulty | " + " | ".join(self.pipeline_names) + " |"
        separator = "|---|---|---|" + "|".join(["---"] * len(self.pipeline_names)) + "|"
        lines.extend([header, separator])

        for i, entry in enumerate(self.entries):
            cells = [str(i + 1), entry["title"], entry["difficulty"]]
            for name in self.pipeline_names:
                result = entry.get(name, {})
                accepted = result.get("accepted")
                if accepted is None:
                    cells.append(result.get("status", "—"))
                elif accepted:
                    cells.append(f"Accepted ({result['time']:.0f}s)")
                else:
                    cells.append(f"{result.get('status', 'Failed')} ({result['time']:.0f}s)")
            lines.append("| " + " | ".join(cells) + " |")

        lines.append("")
        return "\n".join(lines)

    @classmethod
    def from_json(cls, path: Path) -> "ReportGenerator":
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))