# DocuGoSync

**Catch documentation drift when code changes.**

DocuGoSync is a beginner-friendly MVP that compares a Git change with Markdown documentation and reports likely stale statements. It focuses on concrete, explainable checks before adding heavier AI components.

## What it detects in this MVP

- **Renamed/removed CLI flags**: finds old flags still mentioned in docs and suggests the new flag when a clear replacement exists.
- **Changed Python defaults**: finds documentation sentences that still mention an old literal default for a changed setting.
- **New configuration options**: warns when a newly introduced uppercase configuration setting is not mentioned in the docs.

Every finding includes the documentation file and line, related source file, evidence, confidence, and a proposed correction where possible.

## Quick start

Requires Python 3.10+ and Git for repository mode. There are no third-party Python dependencies.

```bash
# 1. Unzip and enter the project
cd DocuGoSync

# 2. Run the built-in demonstration
python -m docugosync demo

# 3. Analyze a real repository against its base commit
python -m docugosync scan --repo /path/to/repository --base origin/main

# Optional: write a Markdown report
python -m docugosync scan --repo /path/to/repository --base origin/main --output report.md
```

If `origin/main` is not available locally, use a locally available base such as `HEAD~1`.

## GitHub Actions

Copy `.github/workflows/docugosync.yml` into the repository being checked. Set the workflow's `base` argument to the branch you want to compare against. The workflow below uses the pull request base SHA.

```yaml
name: DocuGoSync
on:
  pull_request:
    types: [opened, synchronize, reopened]
permissions:
  contents: read
  pull-requests: write
jobs:
  documentation-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Check documentation drift
        run: |
          python -m docugosync scan --repo . --base "${{ github.event.pull_request.base.sha }}" --output docugosync-report.md
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: docugosync-report
          path: docugosync-report.md
```

This starter workflow uploads the report as an artifact. Posting inline PR review comments is a later integration step.

## How it works

1. Read the Git diff and identify changed Python files.
2. Parse old and new Python source with the standard-library `ast` module.
3. Extract CLI flags and literal configuration defaults.
4. Crawl Markdown, reStructuredText and HTML documentation files.
5. Match code facts to documentation lines using exact identifiers and values.
6. Produce findings with evidence and conservative confidence scores.

The MVP deliberately uses deterministic checks. It does **not** claim that semantic understanding or generated corrections are always correct.

## Project structure

```text
DocuGoSync/
├── docugosync/
│   ├── __init__.py
│   ├── __main__.py
│   ├── analyzer.py
│   ├── cli.py
│   ├── extractors.py
│   └── report.py
├── examples/
│   ├── demo_before.py
│   ├── demo_after.py
│   └── README.md
├── tests/
│   └── test_analyzer.py
├── .github/workflows/docugosync.yml
├── pyproject.toml
└── README.md
```

## Important limitations

- The first version analyzes Python source code; Tree-sitter support for other languages is a future extension.
- It uses exact identifiers and literal values rather than embeddings.
- A newly added setting may be reported as undocumented even if it is intentionally internal. Review findings before changing docs.
- HTML extraction is intentionally lightweight and does not execute JavaScript.
- Cross-repository and live website crawling are planned extensions.
- Confidence is a rule-based estimate, not a calibrated probability.

## Roadmap aligned with the hackathon brief

- **Phase 1 — MVP:** Markdown sentences, Python AST, flags/defaults, basic matching, terminal report.
- **Phase 2 — Smarter matching:** Sentence Transformers embeddings, hybrid BM25/vector retrieval, relationship graph, calibrated confidence.
- **Phase 3 — Pull request bot:** GitHub Actions annotations, incremental indexing, optional PR comments.
- **Phase 4 — Extra marks:** Historical PR replay across at least two repositories, external docs sources, evaluation report.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Project name

Use **DocuGoSync** consistently in the CLI, reports, configuration, and repository.
