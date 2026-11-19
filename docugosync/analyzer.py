"""Core documentation drift checks for DocuGoSync."""
from __future__ import annotations

import re
import difflib
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from .extractors import DocLine, extract_code_facts, extract_doc_lines


@dataclass
class Finding:
    kind: str
    severity: str
    confidence: float
    doc_path: str
    doc_line: int | None
    documented_text: str
    source_path: str
    code_evidence: str
    suggestion: str


def _run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True
    )
    return result.stdout


def _relative_docs(root: Path) -> list[DocLine]:
    return extract_doc_lines(root)


def analyze_snapshots(
    old_sources: dict[str, str],
    new_sources: dict[str, str],
    docs: list[DocLine],
) -> list[Finding]:
    """Compare source snapshots and relate changed facts to documentation."""
    findings: list[Finding] = []

    old_facts = {p: extract_code_facts(s) for p, s in old_sources.items()}
    new_facts = {p: extract_code_facts(s) for p, s in new_sources.items()}

    removed_flags: list[tuple[str, str]] = []
    added_flags: list[tuple[str, str]] = []
    changed_settings: list[tuple[str, str, object, object]] = []
    added_settings: list[tuple[str, str, object]] = []

    for path in sorted(set(old_facts) | set(new_facts)):
        old = old_facts.get(path, {"flags": set(), "settings": {}})
        new = new_facts.get(path, {"flags": set(), "settings": {}})
        removed_flags.extend((flag, path) for flag in old["flags"] - new["flags"])
        added_flags.extend((flag, path) for flag in new["flags"] - old["flags"])

        for name in old["settings"].keys() & new["settings"].keys():
            before, after = old["settings"][name], new["settings"][name]
            if before != after:
                changed_settings.append((name, path, before, after))
        for name in new["settings"].keys() - old["settings"].keys():
            if name.isupper():
                added_settings.append((name, path, new["settings"][name]))

    # Removed flags still mentioned by documentation.
    for old_flag, source_path in removed_flags:
        replacements = [new for new, p in added_flags if p == source_path]
        for doc in docs:
            if old_flag in doc.text:
                replacement = replacements[0] if len(replacements) == 1 else None
                suggestion = (
                    doc.text.replace(old_flag, replacement)
                    if replacement else f"Verify the replacement for {old_flag} and update this sentence."
                )
                findings.append(Finding(
                    kind="removed_or_renamed_flag",
                    severity="high",
                    confidence=0.99 if replacement else 0.94,
                    doc_path=doc.path,
                    doc_line=doc.line,
                    documented_text=doc.text,
                    source_path=source_path,
                    code_evidence=f"Removed flag: {old_flag}" + (f"; added flag: {replacement}" if replacement else ""),
                    suggestion=suggestion,
                ))

    # Changed literal defaults: require both the setting name and old value in the doc line.
    
    
    # Changed literal defaults: compare documented values with new code values.
    for name, source_path, before, after in changed_settings:
        pattern = (
            rf"\b{re.escape(name)}\b"
            rf"(?:\s+default)?\s*"
            rf"(?:is|=|:|defaults?\s+to)\s*"
            r"(`?)([-+]?\d+(?:\.\d+)?|True|False|None)(`?)"
        )

        for doc in docs:
            match = re.search(pattern, doc.text, re.IGNORECASE)

            if not match:
                continue

            documented_value = match.group(2)

            if documented_value.lower() == str(after).lower():
                continue

            suggestion = (
                doc.text[:match.start(2)]
                + str(after)
                + doc.text[match.end(2):]
            )

            findings.append(Finding(
                kind="changed_default",
                severity="high",
                confidence=0.96,
                doc_path=doc.path,
                doc_line=doc.line,
                documented_text=doc.text,
                source_path=source_path,
                code_evidence=f"{name}: {before!r} -> {after!r}",
                suggestion=suggestion,
            ))

    # New uppercase settings absent from all documentation.
    all_doc_text = "\n".join(d.text for d in docs).lower()
    for name, source_path, value in added_settings:
        if name.lower() in all_doc_text:
            continue
        candidate = next((d for d in docs if "config" in d.text.lower() or "option" in d.text.lower()), None)
        findings.append(Finding(
            kind="undocumented_configuration",
            severity="medium",
            confidence=0.82,
            doc_path=candidate.path if candidate else "(documentation not found)",
            doc_line=candidate.line if candidate else None,
            documented_text=candidate.text if candidate else "No matching documentation sentence found.",
            source_path=source_path,
            code_evidence=f"New configuration setting: {name} = {value!r}",
            suggestion=f"Add {name} to the configuration documentation and explain its purpose and default ({value!r}).",
        ))

    # Stable de-duplication.
    unique = {}
    for finding in findings:
        key = (finding.kind, finding.doc_path, finding.doc_line, finding.source_path, finding.code_evidence)
        unique[key] = finding
    return sorted(unique.values(), key=lambda f: (-f.confidence, f.doc_path, f.doc_line or 0))


def analyze_repository(repo: Path, base: str = "HEAD~1") -> list[Finding]:
    """Analyze changed Python files against docs in the current working tree."""
    repo = repo.resolve()
    changed = _run_git(repo, "diff","--no-renames","--name-only", f"{base}...HEAD").splitlines()
    py_files = [p for p in changed if p.endswith(".py")]

    old_sources: dict[str, str] = {}
    new_sources: dict[str, str] = {}
    for relative in py_files:
        try:
            old_sources[relative] = _run_git(repo, "show", f"{base}:{relative}")
        except subprocess.CalledProcessError:
            old_sources[relative] = ""
        path = repo / relative
        if path.exists():
            new_sources[relative] = path.read_text(encoding="utf-8", errors="replace")
        else:
            new_sources[relative] = ""

    docs = _relative_docs(repo)
    return analyze_snapshots(old_sources, new_sources, docs)


def finding_dict(finding: Finding) -> dict:
    return asdict(finding)
