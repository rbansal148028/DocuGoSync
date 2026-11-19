# DocuGoSync

**Catch documentation drift when code changes.**

DocuGoSync is a Python-based documentation drift detection tool that checks whether project documentation stays consistent with changes in source code.

When developers modify configuration defaults, rename command-line flags, or introduce new settings, documentation can become outdated. DocuGoSync identifies these possible mismatches and generates an explainable report with evidence and suggested corrections.

The project focuses on deterministic, rule-based checks to make documentation maintenance easier and more reliable.

---

## Features

The current MVP supports three main checks:

- **Renamed or removed CLI flags:** Detects outdated command-line flags that are still mentioned in documentation.
- **Changed Python defaults:** Detects when documentation mentions an old literal default value after the corresponding Python setting has changed.
- **New configuration options:** Identifies newly introduced uppercase configuration settings that are not mentioned in documentation.

Each finding can include:

- Documentation file and line number
- Related source-code file
- Issue type and severity
- Confidence estimate
- Code evidence
- Suggested documentation correction

DocuGoSync generates suggestions for developers to review. It does not automatically modify documentation.

---

## How It Works

1. A developer changes Python source code.
2. DocuGoSync reads the Git diff between the current branch and the selected base.
3. It identifies changed Python files.
4. Python's standard-library AST module is used to analyze source code.
5. The tool extracts relevant CLI flags and configuration defaults.
6. It scans supported documentation files.
7. It compares the extracted code information with documentation text.
8. It generates a Markdown report describing possible documentation drift.

The checks use deterministic matching based on identifiers and literal values rather than semantic AI understanding.

---

## Requirements

- Python 3.10 or above
- Git
- GitHub repository (for GitHub Actions integration)

There are no third-party Python dependencies required by the core tool.

---

## Quick Start: Run DocuGoSync

### 1. Clone the repository

```bash
git clone https://github.com/rbansal148028/DocuGoSync.git
```

### 2. Open the project directory

```bash
cd DocuGoSync
```

### 3. Run the built-in demonstration

```bash
python -m docugosync demo
```

This demonstrates how DocuGoSync identifies documentation mismatches using the included example files.

### 4. Run the unit tests

```bash
python -m unittest discover -s tests -v
```

### 5. Scan a Git repository

```bash
python -m docugosync scan --repo /path/to/repository --base origin/main
```

Replace `/path/to/repository` with the path to the repository you want to analyze.

The base branch must be available locally. If `origin/main` is unavailable, use another locally available base reference.

### 6. Save the report

```bash
python -m docugosync scan --repo /path/to/repository --base origin/main --output report.md
```

This generates a Markdown report containing the detected documentation issues.

---

## Using DocuGoSync in Your Own Python Project

You can integrate DocuGoSync into your own Python repository using the following manual setup.

### Step 1: Open Your Python Project

For example, suppose your project has this structure:

```text
MyProject/
├── src/
│   ├── app.py
│   └── config.py
├── README.md
└── requirements.txt
```

Keep your existing source-code and documentation files.

### Step 2: Get the DocuGoSync Source Code

Clone the DocuGoSync repository:

```bash
git clone https://github.com/rbansal148028/DocuGoSync.git
```

Open the cloned folder and copy the complete `docugosync/` directory into the root of your own project.

Your project should now contain:

```text
MyProject/
├── docugosync/
│   ├── __init__.py
│   ├── __main__.py
│   ├── analyzer.py
│   ├── cli.py
│   ├── extractors.py
│   └── report.py
├── src/
│   ├── app.py
│   └── config.py
├── README.md
└── requirements.txt
```

You do not need to copy the `examples/` or `tests/` folders to scan your own project.

### Step 3: Add the GitHub Actions Workflow

Copy the following file from the DocuGoSync repository:

`.github/workflows/docugosync.yml`

Place it at the same location in your own project:

```text
MyProject/
├── .github/
│   └── workflows/
│       └── docugosync.yml
├── docugosync/
├── src/
└── README.md
```

The workflow configuration is shown below:

```yaml
name: DocuGoSync

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  issues: write

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

      - name: Run DocuGoSync
        run: |
          python -m docugosync scan --repo . --base "${{ github.event.pull_request.base.sha }}" --output docugosync-report.md

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: docugosync-report
          path: docugosync-report.md

      - name: Comment on Pull Request
        if: always() && github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');

            if (!fs.existsSync('docugosync-report.md')) {
              core.notice('No DocuGoSync report found.');
              return;
            }

            const report = fs.readFileSync(
              'docugosync-report.md',
              'utf8'
            );

            const marker = '<!-- docugosync-report -->';
            const body = `${marker}\n${report}`;

            const { owner, repo } = context.repo;
            const issue_number = context.issue.number;

            const comments = await github.paginate(
              github.rest.issues.listComments,
              { owner, repo, issue_number }
            );

            const existing = comments.find(comment =>
              comment.user?.type === 'Bot' &&
              comment.body?.includes(marker)
            );

            if (existing) {
              await github.rest.issues.updateComment({
                owner,
                repo,
                comment_id: existing.id,
                body
              });
            } else {
              await github.rest.issues.createComment({
                owner,
                repo,
                issue_number,
                body
              });
            }
```

This workflow runs when a Pull Request is opened, updated, or reopened.

Make sure GitHub Actions is enabled and the repository's workflow permissions allow the workflow to create and update Pull Request comments.

### Step 4: Push Your Project to GitHub

Commit and push the integration files:

```bash
git add .
git commit -m "Add DocuGoSync integration"
git push
```

### Step 5: Make a Code Change

Suppose your Python project contains:

```python
TIMEOUT_SECONDS = 60
```

And your README documents:

```markdown
The TIMEOUT_SECONDS default is 60 seconds.
```

Now imagine a developer changes the Python default:

```python
TIMEOUT_SECONDS = 90
```

But the README is not updated.

DocuGoSync can detect that the documentation still describes the old default.

### Step 6: Open a Pull Request

Push your code changes to a branch and open a Pull Request against your base branch.

GitHub Actions automatically runs DocuGoSync.

### Step 7: Review the Documentation Report

After the workflow runs, the developer can:

1. Open the Pull Request.
2. View the DocuGoSync bot comment.
3. Review the detected documentation issue.
4. Check the source-code evidence and suggested correction.
5. Download the generated report from the Actions artifacts if needed.
6. Update the documentation if the finding is valid.

When the Pull Request is updated, the workflow runs again and updates its report comment.

---

## Example Detection

Suppose the source code changes from:

```python
TIMEOUT_SECONDS = 60
```

to:

```python
TIMEOUT_SECONDS = 90
```

But the documentation still says:

```markdown
The TIMEOUT_SECONDS default is 30 seconds.
```

DocuGoSync can produce a finding similar to:

```text
Type: Changed Default
Severity: High
Confidence: 96%

Documentation: examples/README.md
Line: 9

Source: examples/demo_after.py

Code Evidence:
TIMEOUT_SECONDS: 60 -> 90

Documented Text:
The TIMEOUT_SECONDS default is 30 seconds.

Suggested Correction:
The TIMEOUT_SECONDS default is 90 seconds.
```

The confidence value is a rule-based estimate, not a guaranteed probability.

---

## Project Structure

```text
DocuGoSync/
├── docugosync/
│   ├── __init__.py
│   ├── __main__.py
│   ├── analyzer.py
│   ├── cli.py
│   ├── extractors.py
│   └── report.py
│
├── examples/
│   ├── demo_before.py
│   ├── demo_after.py
│   └── README.md
│
├── tests/
│   └── test_analyzer.py
│
├── .github/
│   └── workflows/
│       └── docugosync.yml
│
├── pyproject.toml
└── README.md
```

### Main Components

| File | Purpose |
|---|---|
| `analyzer.py` | Analyzes code changes and detects documentation drift |
| `cli.py` | Handles command-line commands |
| `extractors.py` | Extracts information from supported documentation formats |
| `report.py` | Generates Markdown reports |
| `__main__.py` | Allows execution using `python -m docugosync` |
| `test_analyzer.py` | Contains unit tests for analyzer rules |

---

## Supported Documentation Formats

The current MVP supports:

- Markdown (`.md`)
- reStructuredText (`.rst`)
- HTML (`.html` and `.htm`)

HTML extraction is lightweight and does not execute JavaScript.

---

## Important Limitations

- The current MVP primarily analyzes Python source code.
- It uses Python AST and deterministic matching.
- It does not provide semantic understanding using embeddings or large language models.
- It does not crawl external websites or documentation hosted on other platforms.
- A newly added setting may be intentionally internal; findings should be reviewed by a developer.
- Suggested corrections are not automatically applied.
- Confidence scores are rule-based estimates, not calibrated probabilities.
- Integration into another repository currently requires manually copying the source folder and GitHub Actions workflow.
- Findings are informational in the current version and do not automatically block Pull Request merging.

---

## Testing

Run all unit tests using:

```bash
python -m unittest discover -s tests -v
```

Run the built-in demonstration:

```bash
python -m docugosync demo
```

---

## Future Scope

- Support for additional programming languages.
- Smarter documentation matching using semantic embeddings.
- Hybrid keyword and vector-based retrieval.
- Better code-to-documentation relationship tracking.
- Historical Pull Request analysis.
- External documentation source support.
- More advanced evaluation and confidence calibration.

---

## Project Goal

DocuGoSync aims to reduce documentation drift in software projects by identifying outdated documentation whenever code changes.

**Keep code and documentation in sync.**
