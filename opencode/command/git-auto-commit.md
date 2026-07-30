---
description: Analyze Git changes and create a safe bilingual Chinese-English local commit
---

Load and follow the `git-auto-commit` skill (Skill tool / SKILL.md). Then run it for this request.

User arguments: $ARGUMENTS

Default task if no arguments:
Analyze the current Git repository's real working-tree changes, learn recent commit style, generate a concise bilingual Chinese-English commit message, and create a safe local commit.

Rules:
- Locate the skill directory and set `SKILL_DIR` when running bundled resources.
- Run first: `python3 "$SKILL_DIR/scripts/git_commit_snapshot.py"`.
- Inspect `git status --short`, `git diff --stat`, `git diff`, staged diff when present, and recent commits.
- If snapshot `has_conflicts` is true, report conflicted files and stop; do not stage, commit, or push.
- Stage only intended files.
- Stop and ask before committing on secret-like files, unresolved conflicts, huge diffs, unclear intent, destructive changes, public API breaks, migrations, or unrelated mixed changes.
- Never push unless the user explicitly asks for push.
- For dry-run requests, do not stage or commit; only return the proposed message and reasoning.
- Do not add `Co-Authored-By`, `Generated-By`, or other AI attribution trailers unless the user explicitly asks.

Default commit format: `type(scope): 中英文混排描述`
Chinese for description, English for technical terms.
