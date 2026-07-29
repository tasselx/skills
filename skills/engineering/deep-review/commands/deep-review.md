Use the `deep-review` skill from this repository or installed skills directory.
`SKILL.md` is the source of truth; keep the path short (snapshot → evidence → report).

Task:
Production-level, read-only code review of the current changes; return actionable findings only.

Required steps:
1. Set `SKILL_DIR` to the installed `deep-review` skill directory.
2. Snapshot first (do not invent file lists when the script succeeds):
   ```bash
   python3 "$SKILL_DIR/scripts/review_snapshot.py"
   # --mode staged | commit --commit <sha> | branch-diff --base <ref> | file --file <path>
   # defaults embed diff + stack excerpts; add --compact to shrink JSON
   ```
3. If `has_changes` is false, report `empty_hint` and ask which target to review.
4. **Do not** re-run `git status`. Prefer `diff_patch` and `stack_excerpts` from the snapshot.
5. If `stack_excerpts_complete` is false and stacks were detected, read only missing headings from `references/tech-stacks.md`.
6. Parallel-read `full_file_read_paths`; patch may suffice for `patch_likely_enough_paths`.
7. Single-pass review per `SKILL.md` → findings → risk score → merge decision → final report.

Hard rules:
- Read-only: never modify, stage, commit, push, rewrite, patch, or auto-fix.
- No style-only nits; no padded findings; evidence + trigger path required.
- Severity × confidence weights from `SKILL.md` (Medium+Confirmed ≠ Medium+Potential).
- Language: `SKILL.md` Output Language rules.
