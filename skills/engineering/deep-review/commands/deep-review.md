Use the `deep-review` skill from this repository or installed skills directory.

Task:
Perform a thorough, defect-first, read-only code review of the current code changes and return every actionable finding.

Rules:
- Locate the skill directory and set `SKILL_DIR` to it when running bundled resources.
- Determine the review target from user intent (uncommitted changes, staged changes, a specific commit, or a branch diff vs a base branch).
- Run the skill's read-only context helper first: `python3 "$SKILL_DIR/scripts/collect_review_context.py"`.
- For specific targets, pass arguments: `--commit <sha>` or `--base <branch>`.
- Inspect the full diff content, read surrounding context of each changed hunk, and review across all categories: Correctness, Security, Performance, API Design, Error Handling, Tests, Maintainability.
- Read `$SKILL_DIR/references/review-checklist.md` for the detailed checklist when deeper analysis is needed.
- Report each finding with severity (CRITICAL / WARNING / SUGGESTION / PRAISE), file path, line number, category, description, and a concrete suggestion.
- Order findings by severity: Critical first, then Warning, Suggestion, Praise.
- End with a summary count and an overall assessment of merge readiness.
- This skill is read-only: never modify, stage, commit, or push.
- Do not report false positives. If not confident a finding is real, downgrade severity or omit it.
