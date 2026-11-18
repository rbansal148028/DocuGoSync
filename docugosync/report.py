"""Human-readable report rendering."""
from .analyzer import Finding


def render_markdown(findings: list[Finding]) -> str:
    lines = [
        "# DocuGoSync report",
        "",
        f"**Findings:** {len(findings)}",
        "",
    ]
    if not findings:
        lines += ["No likely documentation drift was detected.", ""]
        return "\n".join(lines)

    for index, item in enumerate(findings, 1):
        lines += [
            f"## {index}. {item.kind.replace('_', ' ').title()}",
            "",
            f"- **Severity:** {item.severity}",
            f"- **Confidence:** {item.confidence:.0%}",
            f"- **Documentation:** `{item.doc_path}`" + (f", line {item.doc_line}" if item.doc_line else ""),
            f"- **Source:** `{item.source_path}`",
            f"- **Code evidence:** `{item.code_evidence}`",
            f"- **Documented text:** {item.documented_text}",
            f"- **Suggested correction:** {item.suggestion}",
            "",
        ]
    lines.append("> Review suggestions before applying them. Confidence is a rule-based estimate, not a guarantee.")
    return "\n".join(lines) + "\n"


def render_terminal(findings: list[Finding]) -> str:
    if not findings:
        return "DocuGoSync: no likely documentation drift detected."
    out = [f"DocuGoSync: {len(findings)} finding(s)\n"]
    for i, item in enumerate(findings, 1):
        location = f"{item.doc_path}:{item.doc_line}" if item.doc_line else item.doc_path
        out.extend([
            f"[{i}] {item.kind} | {item.severity.upper()} | confidence {item.confidence:.0%}",
            f"    Docs:   {location}",
            f"    Source: {item.source_path}",
            f"    Text:   {item.documented_text}",
            f"    Change: {item.code_evidence}",
            f"    Fix:    {item.suggestion}",
            "",
        ])
    return "\n".join(out)
