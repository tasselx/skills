---
description: Fast read-only production code review of git diffs with risk score and merge advice
---

Load and follow the `deep-review` skill (Skill tool / SKILL.md). Then run it for this request.

User arguments: $ARGUMENTS

Default task if no arguments:
Review the current uncommitted changes (`git diff HEAD`) as a read-only production-safety code review.

Rules:
- One git diff command first, then write the full review. Prefer instant mode: real defects only.
- Targets: uncommitted (`git diff HEAD`), staged (`git diff --cached`), commit (`git show <sha>`), branch (`git diff <base>...HEAD`), or paths.
- Focus: correctness → reliability → security → regression. Evidence + trigger on every finding.
- Severity × confidence weights, risk score, merge recommendation. No style nits. No padded findings.
- Deep mode only when user asks for deep/thorough review, or change is large/high-risk; then may use `references/review-depth.md` and `references/tech-stacks.md`.
- Never modify code, stage, commit, or push.
