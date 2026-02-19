#!/usr/bin/env python3
"""
Convert Markdown (.md) files to PDF.

Uses the 'markdown' library for MD -> HTML and 'weasyprint' for HTML -> PDF.
Install dependencies with:

    pip install -r scripts/requirements-md2pdf.txt

Or: pip install markdown weasyprint

Usage:

    python scripts/md2pdf.py README.md
    python scripts/md2pdf.py README.md -o README.pdf
    python scripts/md2pdf.py PROJECT_OVERVIEW.md CHECKLIST.md -d ./output

Note: LaTeX-style math (e.g. \\( \\frac{...} \\)) in the Markdown will appear as raw
text in the PDF. For full math rendering, use Pandoc with a LaTeX engine instead.
"""

import argparse
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    print("Error: 'markdown' package not found. Install with: pip install markdown", file=sys.stderr)
    sys.exit(1)

try:
    from weasyprint import HTML, CSS
except ImportError:
    print("Error: 'weasyprint' package not found. Install with: pip install weasyprint", file=sys.stderr)
    sys.exit(1)


DEFAULT_CSS = """
@page {
    size: A4;
    margin: 2cm;
}
body {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #222;
    max-width: 100%;
}
h1 { font-size: 1.8em; margin-top: 0; border-bottom: 1px solid #ccc; padding-bottom: 0.2em; }
h2 { font-size: 1.4em; margin-top: 1.2em; }
h3 { font-size: 1.2em; margin-top: 1em; }
h4, h5, h6 { font-size: 1.1em; margin-top: 0.8em; }
p { margin: 0.5em 0; }
ul, ol { margin: 0.5em 0; padding-left: 1.5em; }
code { font-family: "Consolas", "Monaco", monospace; font-size: 0.9em; background: #f5f5f5; padding: 0.1em 0.3em; border-radius: 3px; }
pre { background: #f5f5f5; padding: 0.8em; overflow-x: auto; border-radius: 4px; margin: 0.8em 0; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; }
th, td { border: 1px solid #ccc; padding: 0.4em 0.6em; text-align: left; }
th { background: #eee; font-weight: 600; }
hr { border: none; border-top: 1px solid #ccc; margin: 1em 0; }
blockquote { margin: 0.8em 0; padding-left: 1em; border-left: 4px solid #ccc; color: #555; }
a { color: #06c; text-decoration: none; }
"""


def md_to_html(md_path: Path, extensions: list[str] | None = None) -> str:
    """Read a Markdown file and return HTML string."""
    text = md_path.read_text(encoding="utf-8", errors="replace")
    ext = extensions or ["extra", "sane_lists", "toc"]
    return markdown.markdown(text, extensions=ext, output_format="html5")


def html_to_pdf(html_content: str, pdf_path: Path, css_string: str = DEFAULT_CSS) -> None:
    """Render HTML string to PDF with optional CSS."""
    html_doc = HTML(string=html_content, base_url=str(pdf_path.parent))
    css = CSS(string=css_string)
    html_doc.write_pdf(pdf_path, stylesheets=[css])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert Markdown (.md) files to PDF.",
        epilog="Dependencies: pip install markdown weasyprint",
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Input .md file(s)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output PDF path (only valid when a single input file is given)",
    )
    parser.add_argument(
        "-d", "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Output directory for generated PDFs (default: current directory)",
    )
    parser.add_argument(
        "--no-toc",
        action="store_true",
        help="Disable table-of-contents extension",
    )
    args = parser.parse_args()

    if args.output and len(args.inputs) > 1:
        print("Error: -o/--output can only be used with a single input file.", file=sys.stderr)
        return 1

    extensions = ["extra", "sane_lists"]
    if not args.no_toc:
        extensions.append("toc")

    for md_path in args.inputs:
        if not md_path.exists():
            print(f"Error: file not found: {md_path}", file=sys.stderr)
            return 1
        if md_path.suffix.lower() != ".md":
            print(f"Warning: expected .md file, got {md_path.suffix}", file=sys.stderr)

        if args.output and len(args.inputs) == 1:
            out_path = args.output
        else:
            out_path = args.output_dir / (md_path.stem + ".pdf")

        out_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            html = md_to_html(md_path, extensions=extensions)
            # Wrap in a minimal document so WeasyPrint gets a proper base
            full_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'/></head><body>{html}</body></html>"
            html_to_pdf(full_html, out_path)
            print(f"Generated: {out_path}")
        except Exception as e:
            print(f"Error converting {md_path}: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
