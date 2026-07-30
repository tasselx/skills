---
name: deep-review
description: >
  Fast read-only review of git diffs. Use for code review, PR review,
  uncommitted/staged/commit/branch diff review. No script dependency —
  runs git commands directly. Use when the user wants to review changes,
  asks for a code review, or invokes deep-review.
---

# Deep Review

Read-only, production-safety code review. **Quality = real bugs only.** No style nits. No padded findings. No repo tourism.

This skill is agent-neutral. Use it from Codex, Claude Code, Cursor, OpenCode, Gemini CLI, or any other coding agent that can read this `SKILL.md` file and run local shell commands.

## Quick Workflow

1. Determine the review target (what to diff against):
   - Uncommitted changes: `git diff HEAD` (all changes vs last commit)
   - Staged only: `git diff --cached`
   - A specific commit: `git show <sha>`
   - Branch diff: `git diff <base>...HEAD` (three-dot, against merge-base)
   - Specific file: `git diff -- <path>`

2. Run **one** git command to capture the diff:

```bash
git diff HEAD                    # uncommitted (default)
# or
git diff --cached                # staged only
# or
git show <sha>                   # specific commit
# or
git diff main...HEAD             # branch diff against main
```

3. Get recent commit context:

```bash
git log --oneline -10
```

4. Write the review immediately from the diff. **No further tool calls.**

**Default is oneshot**: one `git diff` + one review message. Do not "verify callers", "scan related tests", or "open surrounding files" unless deep mode.

## Modes

- **Instant** (default): `git diff` → review. One tool call.
- **Deep**: for large/high-risk changes (auth/payments/migrations/concurrency). May read `$SKILL_DIR/references/review-depth.md` and `$SKILL_DIR/references/tech-stacks.md` for extra checklists. Max 3 additional tool batches. Still no full-repo explore.

## Focus Categories

In order, skip N/A: **correctness → reliability → security → regression**.
Only if clearly hit by the diff: performance, deployment.
**Skip by default:** architecture essays, observability theater, low nitpicks, "consider adding tests" without a concrete bug.

## Output Format

Emit in one message:

1. Optional header: `mode=instant|deep · files=N · lang=zh|en`
2. Each finding (if any):

```markdown
### 1. 🔴 [CRITICAL] 标题

**Confidence:** Confirmed · **Category:** Security · **Location:** `a.py:42`

问题简述（触发条件 + 后果）。

- **Evidence:** `a.py:42` 具体行为
- **Trigger:** 谁/什么条件；likelihood High|Medium|Low
- **Fix:** 可执行改法（≤8 行代码）
```

3. If ≥2 findings: short index table
4. Summary table always:

```markdown
---
## Review Summary
| Field | Value |
|-------|-------|
| **Decision** | ✅ APPROVE / ⚠️ APPROVE WITH COMMENTS / 🔧 REQUEST CHANGES / 🛑 BLOCK MERGE |
| **Risk** | Low/Medium/High/Very High (raw N; rule) |
| **Issues** | 🔴 x · 🟠 x · 🟡 x · 🟢 x |
| **Files** | `…` |

**Why:** 1–2 句。
```

5. Limitations / Questions for Author — **omit if empty**.

Markers: 🔴 Critical · 🟠 High · 🟡 Medium · 🟢 Low

Finding gate: needs `path:line` evidence + realistic trigger. Drop weak/speculative items. Dedupe root causes.

## Output Language

1. User chat override ("用中文" / "in English") wins.
2. Else default to **中文** (Chinese prose, English for paths/code/severity/confidence/category/Decision labels).
3. If user writes in English, default to English.

## Risk Weights

| | Confirmed | Likely | Potential |
|--|----------:|-------:|----------:|
| Critical | 100 | 80 | 45 |
| High | 55 | 40 | 22 |
| Medium | 20 | 14 | 8 |
| Low | 4 | 3 | 1 |

Very High: score≥80 or Critical+Confirmed/Likely → often 🛑
High: 45–79 or Critical+Potential or High+Confirmed/Likely → 🔧
Medium: 15–44 or Medium+Confirmed/Likely → ⚠️
else ✅ (if no Critical/High)

## Absolute Bans

- Do not modify code, commit, push, patch, or run formatters
- Do not open `references/review-depth.md` unless deep mode
- Do not start Task/explore/subagent
- Do not print long preambles ("I'll start by…") — diff then review

**Success metric:** small diffs finish in **one git command + one review message**.
