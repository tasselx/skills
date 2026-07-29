Use the `deep-review` skill from this repository or installed skills directory.
All detailed rules live in `SKILL.md` — follow that file as the single source of truth.

Task:
Perform a production-level, read-only code review of the current code changes and return every actionable finding.

Required steps:
1. Set `SKILL_DIR` to the installed `deep-review` skill directory.
2. Run the snapshot helper first (do not invent file lists when the script succeeds):
   - uncommitted: `python3 "$SKILL_DIR/scripts/review_snapshot.py"`
   - staged: `python3 "$SKILL_DIR/scripts/review_snapshot.py" --mode staged`
   - commit: `python3 "$SKILL_DIR/scripts/review_snapshot.py" --mode commit --commit <sha>`
   - branch-diff: `python3 "$SKILL_DIR/scripts/review_snapshot.py" --mode branch-diff --base <ref>`
   - file: `python3 "$SKILL_DIR/scripts/review_snapshot.py" --mode file --file <path>`
3. If `has_changes` is false, report `empty_hint` and ask which target to review.
4. If `must_read_tech_stack_sections` is non-empty, read `$SKILL_DIR/references/tech-stacks.md` and apply those sections.
5. Inspect real diffs and complete changed files (`prioritized_paths` first; skip `excluded_paths` unless targeted).
6. Review per `SKILL.md`: intent → impact → categories → bug patterns → verify/dedupe → findings → quantified risk score → merge decision.
7. Output findings and final report exactly as specified in `SKILL.md`.

Hard rules:
- Read-only: never modify files, stage, commit, push, rewrite code, apply fixes, or generate patches.
- No style-only nits; no padding findings; evidence + trigger path required.
- Use severity × confidence weights from snapshot `risk_matrix` / `SKILL.md` (Medium+Confirmed ≠ Medium+Potential).
- Output language: follow `SKILL.md` Output Language rules — detect system locale (Chinese → Chinese, else English), or honor user-specified language.
