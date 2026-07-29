Use the `git-auto-commit` skill from this repository or installed skills directory.

Task:
Analyze the current Git repository's real working-tree changes, learn recent commit style, generate a concise bilingual Chinese-English commit message, and create a safe local commit.

Rules:
- Locate the skill directory and set `SKILL_DIR` to it when running bundled resources.
- Run the skill's read-only snapshot helper first: `python3 "$SKILL_DIR/scripts/git_commit_snapshot.py"`.
- Inspect `git status --short`, `git diff --stat`, `git diff`, staged diff when present, and recent commits.
- The snapshot JSON includes `has_conflicts`, `conflicted_paths`, `merge_in_progress`, `rebase_in_progress`, and separate `staged_*` / `unstaged_*` line counts.
- If `has_conflicts` is `true`, report conflicted files and ask the user to resolve them; do not stage, commit, or push until resolved.
- Stage only intended files.
- Stop and ask before committing when secret-like files, unresolved conflicts, huge diffs, unclear intent, destructive changes, public API breaks, migrations, or unrelated mixed changes are present.
- Never push unless the user explicitly asks for push.
- For dry-run requests, do not stage or commit; only return the proposed message and reasoning.
- Do not add `Co-Authored-By`, `Generated-By`, or other AI attribution trailers unless the user explicitly asks for them.

Default commit format:
`type(scope): 中英文混排描述`

Use mixed Chinese-English naturally: Chinese for description, English for technical terms. No need for a separate English translation.
