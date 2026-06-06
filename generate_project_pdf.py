from pathlib import Path
import textwrap

SRC = Path("PROJECT_DIAGNOSIS_AND_WORKFLOW.md")
OUT = Path("PROJECT_DIAGNOSIS_AND_WORKFLOW.pdf")


def generate_with_reportlab(src: Path, out: Path) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    text = src.read_text(encoding="utf-8")

    c = canvas.Canvas(str(out), pagesize=A4)
    width, height = A4

    left_margin = 18 * mm
    right_margin = 18 * mm
    top_margin = 18 * mm
    bottom_margin = 18 * mm

    line_height = 5.2 * mm
    usable_width = width - left_margin - right_margin

    # Approximate chars per line for Courier 10
    font_name = "Courier"
    font_size = 10
    approx_char_width = 0.55 * font_size
    max_chars = max(40, int(usable_width / approx_char_width))

    c.setFont(font_name, font_size)
    y = height - top_margin

    for raw_line in text.splitlines():
        line = raw_line.replace("\t", "    ")
        if not line.strip():
            wrapped = [""]
        else:
            wrapped = textwrap.wrap(
                line,
                width=max_chars,
                break_long_words=False,
                break_on_hyphens=False,
            ) or [""]

        for wline in wrapped:
            if y <= bottom_margin:
                c.showPage()
                c.setFont(font_name, font_size)
                y = height - top_margin
            c.drawString(left_margin, y, wline)
            y -= line_height

    c.save()


if __name__ == "__main__":
    try:
        generate_with_reportlab(SRC, OUT)
        print(f"PDF generated: {OUT.resolve()}")
    except Exception as exc:
        raise SystemExit(f"Failed to generate PDF: {exc}")
