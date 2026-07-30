# /deep-review — Read-Only Code Review

**One git diff command. Then write the full review. No exploration.**

## Step 1 — Capture the diff

```bash
# Uncommitted changes (default)
git diff HEAD

# Staged only
git diff --cached

# Specific commit
git show <sha>

# Branch diff against base
git diff <base>...HEAD
```

Also get recent context:

```bash
git log --oneline -10
```

## Step 2 — Write the review immediately

No further tool calls. Focus: correctness → reliability → security → regression.
Real defects only. Evidence + trigger on every finding.
See `SKILL.md` for finding format and risk weights.

## Deep mode

Only when user asks for deep/thorough review, or change is large/high-risk.
May open `references/review-depth.md` and `references/tech-stacks.md`.
Max 3 additional tool batches.

## Forbidden

- `Read` / `Grep` / `Glob` / `Task` / second `Bash` (in instant mode)
- Modifying code, committing, pushing
- Long preambles
