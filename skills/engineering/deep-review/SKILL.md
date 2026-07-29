---
name: deep-review
description: >
  Fast read-only review of git diffs/PRs via one local snapshot script, then
  immediate findings. Use for code review, PR review, uncommitted/staged/commit
  diff review. Do not use multi-step explore agents for this.
---

# Deep Review — HARD PROTOCOL

You are doing a **fast, read-only** ship-safety review.
**Quality = real bugs only.** No style nits. No padded findings. No repo tourism.

---

## STOP — TOOL BUDGET (non-negotiable)

| Allowed tools for this skill | Count |
|------------------------------|------:|
| `Bash` running `review_snapshot.py` (below) | **1** |
| Any other tool (`Read`, `Grep`, `Glob`, `Task`, `Skill`, second `Bash`, …) | **0** |

**After snapshot JSON is returned, your next assistant message MUST be the finished review.**  
If you catch yourself planning another tool call → **cancel it** and write the review from the snapshot.

Exceptions (only):
- Snapshot failed / not a git repo → one fix attempt, then stop.
- User asked `--mode deep` / “深度审查” / `DEEP_REVIEW_PROFILE=deep` → max **3** tool batches after snapshot; still no full-repo explore.

Default is **always oneshot**. Do **not** “verify callers”, “scan related tests”, or “open surrounding files”. Everything needed is already inside the snapshot (`diff_patch`, `file_contents`, `stack_excerpts`).

---

## Step 1 — Single snapshot (only tool call)

```bash
SKILL_DIR="${SKILL_DIR:-$HOME/.agents/skills/deep-review}"
# fallback: repo checkout
[ -x "$SKILL_DIR/scripts/review_snapshot.py" ] || SKILL_DIR="$(dirname "$0")/.." 
python3 "$SKILL_DIR/scripts/review_snapshot.py" --compact
```

Optional flags (same single call):  
`--mode staged|commit|branch-diff|file` · `--commit <sha>` · `--base <ref>` · `--file <path>` · `--profile deep`

If `has_changes` is false → print `empty_hint`, ask target, **stop** (no more tools).

---

## Tongueless after snapshot

Use **only** these fields from JSON:

| Field | Use |
|-------|-----|
| `output_language` + `output_language_rule` | **Prose language** (`zh`→中文正文, `en`→English). Do not trust shell `LANG` alone. |
| `diff_patch.patch` | Primary evidence |
| `file_contents.files` | Full text of small/changed files (already embedded) |
| `stack_excerpts.sections` | Optional stack checklist scrapes |
| `change_types`, `prioritized_paths`, `excluded_paths` | Scope |
| `review_profile`, `agent_hints.speed_contract` | Confirm oneshot |

Ignore: inventing extra file reads when `file_contents` / patch already cover the change.

---

## Step 2 — Write the review immediately (no tools)

Focus categories (in order, skip N/A): **correctness → reliability → security → regression**.  
Only if clearly hit by the diff: performance, deployment.  
**Skip by default:** architecture essays, observability theater, Low nitpicks, “consider adding tests” without a concrete bug.

**Emit oneshot** in one message:

1. Optional header: `profile=… · files=N · lang=zh|en`
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
| **Stacks** | … or none |
| **Profile** | instant |

**Why:** 1–2 句。
```

5. Limitations / Questions for Author — **omit if empty**.

Markers: 🔴 Critical · 🟠 High · 🟡 Medium · 🟢 Low  

Finding gate: needs ``path:line`` evidence + realistic trigger. Drop weak/speculative items. Dedupe root causes.

---

## Output Language

1. User chat override (“用中文” / “in English”) wins.  
2. Else **must** follow snapshot `output_language`.  
3. `zh`: 全部叙述中文；路径/代码/severity·confidence·category·Decision 标签保持英文。  
4. `en`: all prose English.  
5. If `must_write_chinese: true` and you wrote English body → you failed the skill.

---

## Risk weights (for Summary)

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

---

## Absolute bans

- Do not modify code, commit, push, patch, or run formatters  
- Do not open `references/review-depth.md` unless user/profile **deep**  
- Do not full-read `tech-stacks.md` when `stack_excerpts_complete`  
- Do not start Task/explore/subagent  
- Do not print long preambles (“I'll start by…”) — snapshot then review  

**Success metric:** small diffs finish in **one tool call + one review message**, not multi-minute exploration.
