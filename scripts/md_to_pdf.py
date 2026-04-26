"""Convert PIPELINES.md to a clean PDF.

Renders the markdown using fpdf2 with proper unicode (DejaVu) fonts so
Hungarian accents work. Only handles the markdown features actually used
in PIPELINES.md (## headings + paragraphs + simple bold).
"""

import re
import sys
from pathlib import Path

from fpdf import FPDF


SRC = Path("docs/PIPELINES.md")
OUT = Path("docs/PIPELINES.pdf")


class PipelinesPDF(FPDF):
    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("DejaVu", "I", 8)
        self.set_text_color(120)
        self.cell(0, 6, "Pipeline-ok rövid magyarázata", align="R")
        self.ln(8)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("DejaVu", "I", 8)
        self.set_text_color(140)
        self.cell(0, 8, f"{self.page_no()}", align="C")


def render(md_text: str) -> None:
    pdf = PipelinesPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(left=22, top=20, right=22)

    # DejaVu ships with Windows in the Python install or matplotlib; try a few paths
    font_dir = None
    candidates = [
        Path("C:/Windows/Fonts/DejaVuSans.ttf"),
        Path(sys.prefix) / "Lib/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf",
    ]
    for p in candidates:
        if p.exists():
            font_dir = p.parent
            break
    if font_dir is None:
        raise SystemExit("DejaVuSans.ttf not found — install matplotlib or copy the font.")

    pdf.add_font("DejaVu", "", str(font_dir / "DejaVuSans.ttf"))
    pdf.add_font("DejaVu", "B", str(font_dir / "DejaVuSans-Bold.ttf"))
    pdf.add_font("DejaVu", "I", str(font_dir / "DejaVuSans-Oblique.ttf"))

    pdf.add_page()

    lines = md_text.splitlines()
    i = 0
    first_h1 = True
    while i < len(lines):
        line = lines[i].rstrip()

        if not line:
            pdf.ln(3)
            i += 1
            continue

        if line.startswith("# "):
            if not first_h1:
                pdf.ln(4)
            first_h1 = False
            pdf.set_font("DejaVu", "B", 20)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(0, 10, line[2:].strip())
            pdf.ln(2)

        elif line.startswith("## "):
            pdf.ln(3)
            pdf.set_font("DejaVu", "B", 13)
            pdf.set_text_color(40, 80, 160)
            pdf.multi_cell(0, 7, line[3:].strip())
            pdf.ln(1)

        elif line.startswith("### "):
            pdf.set_font("DejaVu", "B", 11)
            pdf.set_text_color(60)
            pdf.multi_cell(0, 6, line[4:].strip())

        elif (img_match := re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line)):
            alt_text, img_path = img_match.group(1), img_match.group(2)
            # Resolve relative to the markdown file location
            full_path = (SRC.parent / img_path).resolve()
            if not full_path.exists():
                # Try treating it as relative to project root
                full_path = Path(img_path).resolve()
            if full_path.exists():
                # Compute width fitting page (page width minus margins)
                page_w = pdf.w - pdf.l_margin - pdf.r_margin
                # Cap width at 160mm so charts don't fill the whole page
                img_w = min(page_w, 160)
                pdf.ln(2)
                # Center the image
                x = (pdf.w - img_w) / 2
                pdf.image(str(full_path), x=x, w=img_w)
                pdf.ln(2)
                if alt_text and alt_text != "alt text":
                    pdf.set_font("DejaVu", "I", 9)
                    pdf.set_text_color(120)
                    pdf.multi_cell(0, 5, alt_text, align="C")
                pdf.ln(3)
            else:
                pdf.set_font("DejaVu", "I", 9)
                pdf.set_text_color(180, 60, 60)
                pdf.multi_cell(0, 5, f"[image not found: {img_path}]")

        else:
            # Body paragraph — collect all lines until blank or new heading
            paragraph_lines = [line]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not lines[j].lstrip().startswith("#") \
                    and not re.match(r"!\[", lines[j].lstrip()):
                paragraph_lines.append(lines[j].rstrip())
                j += 1
            paragraph = " ".join(paragraph_lines).strip()
            i = j - 1  # outer loop will += 1

            pdf.set_font("DejaVu", "", 11)
            pdf.set_text_color(35)
            # Inline bold: split on **...**
            parts = re.split(r"\*\*(.+?)\*\*", paragraph)
            # fpdf2 doesn't combine multi-styles in multi_cell easily; for simplicity
            # we just write it as plain text with bold inline using write()
            line_height = 6
            for idx, part in enumerate(parts):
                if not part:
                    continue
                pdf.set_font("DejaVu", "B" if idx % 2 == 1 else "", 11)
                pdf.write(line_height, part)
            pdf.ln(line_height)
            pdf.ln(1)

        i += 1

    pdf.output(str(OUT))
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    if not SRC.exists():
        raise SystemExit(f"{SRC} not found")
    render(SRC.read_text(encoding="utf-8"))
