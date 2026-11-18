"""Small, dependency-free documentation and source extractors."""
from __future__ import annotations

import ast
import html
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocLine:
    path: str
    line: int
    text: str


def extract_doc_lines(root: Path) -> list[DocLine]:
    """Read supported docs while preserving source line numbers."""
    results: list[DocLine] = []
    ignored = {".git", ".venv", "venv", "node_modules", "__pycache__", ".tox"}
    extensions = {".md", ".markdown", ".rst", ".html", ".htm"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        if any(part in ignored for part in path.parts):
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if path.suffix.lower() in {".html", ".htm"}:
            raw = re.sub(r"(?is)<(script|style)\b.*?</\1\s*>", " ", raw)
            raw = re.sub(r"(?s)<[^>]+>", " ", raw)
            raw = html.unescape(raw)
        for number, line in enumerate(raw.splitlines(), 1):
            clean = re.sub(r"\s+", " ", line).strip()
            if clean:
                results.append(DocLine(path.as_posix(), number, clean))
    return results


def literal_value(node: ast.AST):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def extract_code_facts(source: str) -> dict:
    """Extract argparse flags and simple literal assignments from Python."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"flags": set(), "settings": {}}

    flags: set[str] = set()
    settings: dict[str, object] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "add_argument":
                for arg in node.args:
                    value = literal_value(arg)
                    if isinstance(value, str) and value.startswith("--"):
                        flags.add(value)

        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value_node = node.value
            if value_node is None:
                continue
            value = literal_value(value_node)
            if value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    settings[target.id] = value

    return {"flags": flags, "settings": settings}
