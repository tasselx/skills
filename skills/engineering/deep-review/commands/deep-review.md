Use the `deep-review` skill. `SKILL.md` is source of truth.

Task: production-level **read-only** review of current changes; actionable findings only.

## Steps (keep short)

1. `SKILL_DIR` = installed `deep-review` directory.
2. **One** snapshot (prefer compact):
   ```bash
   python3 "$SKILL_DIR/scripts/review_snapshot.py" --compact
   ```
   Modes: `--mode staged` | `commit --commit <sha>` | `branch-diff --base <ref>` | `file --file <path>`
3. If `has_changes` false → `empty_hint` + ask target.
4. Obey `output_language` / `output_language_rule` from snapshot (or user chat override). If `zh`, write the **whole** review in Chinese prose — do not default to English because `LANG=en_US`.
5. Read `review_profile` + `agent_hints.speed_contract` and **obey**:
   - **instant** → **zero** further tools; review from `diff_patch` + `file_contents` + `stack_excerpts`; **oneshot** full report in the next message.
   - **standard** → ≤1 parallel read batch only if `full_file_read_paths` non-empty; then oneshot.
   - **deep** → ≤3 tool batches; stream findings; then Summary.
6. Never repeat `git status`. Never load `review-depth.md` on instant/standard.

## Hard rules

- Read-only: no modify/stage/commit/push/fix/patch.
- No style nits; no padded findings; evidence + trigger required.
- Weights/decision: `SKILL.md` Risk Score.
- Language: follow snapshot `output_language` (`zh`→中文正文, `en`→English). User chat override wins. Never trust shell `LANG` alone.
