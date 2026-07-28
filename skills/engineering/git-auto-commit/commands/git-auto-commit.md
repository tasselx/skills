Use the `git-auto-commit` skill from this repository or installed skills directory.

Task:
Analyze the current Git repository's real working-tree changes, learn recent commit style, generate a concise bilingual Chinese-English commit message, and create a safe local commit.

Rules:
- Locate the skill directory and set `SKILL_DIR` to it when running bundled resources.
- Run the skill's read-only snapshot helper first when available: `python3 "$SKILL_DIR/scripts/git_commit_snapshot.py"`.
- Inspect `git status --short`, `git diff --stat`, `git diff`, staged diff when present, and recent commits.
- Stage only intended files.
- Stop and ask before committing when secret-like files, huge diffs, unclear intent, destructive changes, public API breaks, migrations, or unrelated mixed changes are present.
- Never push unless the user explicitly asks for push.
- For dry-run requests, do not stage or commit; only return the proposed message and reasoning.

Default commit format:
`type(scope): 中文描述 English Keyword`
