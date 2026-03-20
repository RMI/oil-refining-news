# Agents Guide

## Goal

Keep this project as a local-only Google News RSS tagging pipeline.

## Product Rules

- Do not add Azure dependencies.
- Do not add MySQL or other database dependencies.
- Prefer file-based inputs and outputs.
- Keep Google News RSS as the external content source.

## Main Workflow

1. Read asset data from Excel or CSV.
2. Optionally read a local tag profile file.
3. Build keywords and tag references from the input files.
4. Pull article summaries from Google News RSS.
5. Apply local tagging logic.
6. Write tagged results to Excel or CSV.

## Key Files

- `main.py`: CLI entry point for the local pipeline
- `newsCompiler.py`: compatibility script with editable defaults
- `functions.py`: Google RSS fetch helpers and compatibility wrapper for tagging
- `input_loader.py`: file loading and output writing helpers
- `tagging.py`: local asset/tag preparation and tag matching logic

## Setup

1. `python -m venv .venv`
2. `.venv\Scripts\Activate.ps1`
3. `pip install -r requirements.txt`

## Done Criteria

- The pipeline runs locally with no VPN, Azure resource, or database access.
- Users can provide `.xlsx`, `.xls`, or `.csv` inputs.
- The output file contains tagged Google News results.
- README and this file stay current with the actual code.



## AI use disclosure

In all GitHub commits and PRs, include the following:

- AI-Assisted: yes/no
- AI-Tool: none | copilot-coding-agent | chatgpt | claude-code | cursor | other
- AI-Model: none | unknown | <model-name>
- AI-Role: none | author | editor | reviewer
- Disclosure-Confidence: high | medium | low