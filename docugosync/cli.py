"""Command-line interface for DocuGoSync."""
from __future__ import annotations

import argparse
from pathlib import Path

from .analyzer import analyze_repository, analyze_snapshots
from .extractors import extract_doc_lines
from .report import render_markdown, render_terminal


def run_demo() -> int:
    root = Path(__file__).resolve().parent.parent / "examples"
    before = (root / "demo_before.py").read_text(encoding="utf-8")
    after = (root / "demo_after.py").read_text(encoding="utf-8")
    docs = extract_doc_lines(root)
    findings = analyze_snapshots(
        {"src/app.py": before},
        {"src/app.py": after},
        [d for d in docs if d.path.endswith("README.md")],
    )
    print(render_terminal(findings))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="docugosync",
        description="Detect documentation drift caused by code changes."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Analyze changed Python code against repository docs")
    scan.add_argument("--repo", type=Path, default=Path("."))
    scan.add_argument("--base", default="HEAD~1", help="Git base commit/ref")
    scan.add_argument("--output", type=Path, help="Write a Markdown report")

    sub.add_parser("demo", help="Run the built-in renamed-flag demonstration")
    args = parser.parse_args(argv)

    if args.command == "demo":
        return run_demo()

    try:
        findings = analyze_repository(args.repo, args.base)
    except Exception as exc:
        print(f"DocuGoSync could not analyze the repository: {exc}")
        return 2

    print(render_terminal(findings))
    if args.output:
        args.output.write_text(render_markdown(findings), encoding="utf-8")
        print(f"\nMarkdown report written to: {args.output}")
    return 1 if findings else 0
