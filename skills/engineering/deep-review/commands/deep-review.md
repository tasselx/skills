# /deep-review — HARD ENTRY

**Tool budget = 1.** Then write the full review. No exploration.

## Exactly one command

```bash
python3 "${HOME}/.agents/skills/deep-review/scripts/review_snapshot.py" --compact
# or repo path:
# python3 skills/engineering/deep-review/scripts/review_snapshot.py --compact
```

Other modes (still **one** call):  
`--mode staged` | `--mode commit --commit HEAD` | `--mode branch-diff --base main` | `--mode file --file p`  
`--profile deep` only when user wants slow/thorough.

## Then stop tools

From the JSON, write the review:

- Language = `output_language` / `output_language_rule` (zh → 中文正文). Never use shell `LANG` alone.
- Evidence = `diff_patch` + `file_contents.files` + `stack_excerpts`
- If `agent_hints.max_tool_batches_after_snapshot == 0` → **zero** further tools (default)

## Output

Findings (if any) → index if ≥2 → Review Summary table → Limitations/Questions only if needed.  
See skill `SKILL.md` for finding format and risk weights.

## Forbidden after snapshot

`Read` / `Grep` / `Glob` / `Task` / second `Bash` / reloading skill files / opening `review-depth.md`.

## Hard rules

- Read-only  
- Real defects only  
- Evidence + trigger on every finding  
