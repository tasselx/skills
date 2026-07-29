---
name: deep-review
description:
  Deep production-level review of code changes.
  Analyze intent, architecture, correctness, security, performance,
  reliability and maintainability. Find real defects and classify
  issues by severity and confidence.
  Use when reviewing code, reviewing a PR, reviewing a diff,
  reviewing uncommitted changes, reviewing staged changes,
  reviewing a commit, or reviewing a branch diff.
---

# Deep Review

Senior production review. Ship-safety only — no padding, no style nits.

**Prefer:** real defect > speculation, evidence > theory.  
**Read-only:** never modify files, commit, push, rewrite, apply fixes, or generate patches.  
**Tone:** neutral (“When X, Y may happen”).

# Output Language

**Authoritative source: snapshot field `output_language` (`zh` | `en`).**  
Also read `output_language_rule` and obey it. Do **not** re-guess from shell `LANG` alone — many systems keep `LANG=en_US` while the UI language is Chinese.

Resolution order used by the snapshot script:
1. User explicit request in the chat (e.g. "用中文审查", "review in English") — overrides snapshot for this run.
2. Env override: `DEEP_REVIEW_LANG=zh|en`
3. Chinese POSIX locale (`zh_*` in `LANG` / `LC_*` / `LANGUAGE`)
4. **macOS UI language** (`AppleLocale` / `AppleLanguages`) — use this when shell LANG is English
5. Default: `en`

When `output_language=zh` (or user asked for Chinese):
- Finding titles, body, Evidence/Trigger/Fix **prose**, Summary **Why**, Limitations, Questions → **Chinese**
- Keep in English: paths, code, git, severity tokens (`CRITICAL`…), confidence, category, merge decision, table keys (`Decision`, `Risk`, `Issues`, `Files`, `Stacks`, `Profile`)
- Do **not** emit an English-only report.

When `output_language=en`:
- All prose in English.

Kickoff/progress lines follow the same language. No mixed Chinese/English prose (except English tokens above).

# Speed Contract (mandatory)

Snapshot returns `review_profile` + `agent_hints.speed_contract`. **Obey them.**

| Profile | When (approx) | Tool batches **after** snapshot | Emit |
|---------|----------------|----------------------------------|------|
| **instant** | ≤5 reviewable files **and** ≤150 lines, no security/migration/large/multi-package | **0** | **oneshot** full report |
| **standard** | ≤20 files **and** ≤800 lines | **≤1** (only if `full_file_read_paths` non-empty) | **oneshot** |
| **deep** | large / security / migration / monorepo multi-package / else | **≤3** | stream findings |

Hard bans (all profiles unless deep + explicitly needed):
- No second `git status` / ad-hoc git parsing when snapshot OK
- No re-loading this SKILL.md
- No `references/review-depth.md` on **instant/standard**
- No full `tech-stacks.md` when `stack_excerpts_complete`
- No tests on instant/standard
- No grep/caller walks on **instant**
- No “let me explore the codebase” loops

**instant:** after snapshot stdout is in context, your **next message is the complete review**. Use only `diff_patch`, `file_contents.files`, `stack_excerpts`. Zero extra tools.

# Fast Workflow

## 1. Snapshot only (always first)

```bash
export SKILL_DIR="/path/to/deep-review"
python3 "$SKILL_DIR/scripts/review_snapshot.py" --compact
# --mode staged | commit --commit <sha> | branch-diff --base <ref> | file --file <path>
```

If `has_changes` is false → print `empty_hint`, ask target, stop.

Trust: `review_profile`, `agent_hints`, `output_language`, `output_language_rule`,
`diff_patch`, `file_contents`, `stack_excerpts`,
`prioritized_paths`, `excluded_paths`, `full_file_read_paths`, `change_types`.

## 2. Branch on profile

### instant (default for small diffs)

1. Read snapshot fields in-memory (no tools).
2. Review `diff_patch.patch` + any `file_contents.files`.
3. Apply `stack_excerpts.sections` lightly (skip if change is docs/test-only).
4. **Immediately write full report** (findings if any + Summary).  
   Keep focus: correctness / obvious reliability / security only. Skip architecture-for-its-own-sake, observability theater, low nits.

### standard

1. If `full_file_read_paths` empty → same as instant oneshot.  
2. Else **one** parallel Read batch for those paths only, then oneshot report.
3. Categories: correctness, reliability, security, regression; others only if clearly relevant.

### deep

1. Parallel load remaining `full_file_read_paths`; optional targeted caller grep for public API changes.
2. Stream each confirmed finding as you go; cap ≤3 tool batches after snapshot.
3. `review-depth.md` only if still blocked on calibration.

# Scope

**Skip:** `excluded_paths` (generated/lock/binary) unless targeted.  
**Prioritize:** production logic, public APIs, security, persistence/network, migrations.  
**Large:** partial OK; list unread paths in Limitations.  
**Mixed:** group findings, finish anyway.

# Finding Rules

Need: `` `path:line` `` evidence, realistic trigger, severity, confidence.  
Confidence: Confirmed | Likely | Potential  
Severity: Critical · High · Medium · Low (Low only if useful)  
Drop style/preference/no-path/weak items. Dedupe by root cause.  
Sort display order: severity → confidence → impact.

# Output Format

Normal markdown. Markers: 🔴 Critical · 🟠 High · 🟡 Medium · 🟢 Low  
Decisions: ✅ APPROVE · ⚠️ APPROVE WITH COMMENTS · 🔧 REQUEST CHANGES · 🛑 BLOCK MERGE

## oneshot (instant/standard)

Single message:

1. Optional one-line header: `profile=instant · N files · M lines`
2. Finding details `#1…` (if any) — discovery or severity order
3. Findings index table only if ≥2
4. Review Summary
5. Limitations / Questions — **only if non-empty**

## stream (deep only)

Emit each finding when confirmed; end with index (≥2) + Summary + optional Limitations/Questions.

## Finding detail (compact)

```markdown
### 1. 🔴 [CRITICAL] Short title

**Confidence:** Confirmed · **Category:** Security · **Location:** `a.py:42`

When attacker-controlled `query` is concatenated into SQL and executed.

- **Evidence:** `a.py:42` `f"…{query}…"` → `cursor.execute`
- **Trigger:** `GET /search?q=`; likelihood High
- **Fix:** parameterized query (`%s` placeholder)
```

Rules: title ≤12 words; Fix ≤8 lines; no blockquotes; no full-file dumps.

## Summary (always)

```markdown
---
## Review Summary

| Field | Value |
|-------|-------|
| **Decision** | 🔧 REQUEST CHANGES |
| **Risk** | High (raw 55; High+Confirmed) |
| **Issues** | 🔴 0 · 🟠 1 · 🟡 0 · 🟢 0 |
| **Files** | `a.py` |
| **Stacks** | Python |
| **Profile** | instant |

**Why:** one or two sentences.
```

Zero issues → Issues row or line `✅ No issues found.`

# Risk Score & Merge

| Severity | Confirmed | Likely | Potential |
|----------|-----------|--------|-----------|
| Critical | 100 | 80 | 45 |
| High | 55 | 40 | 22 |
| Medium | 20 | 14 | 8 |
| Low | 4 | 3 | 1 |

Raw = sum after dedupe. Cluster 3+: top full, extras 25%. All-Potential cap Medium. Medium+Potential sole & score<15 → Low.

| Risk | Condition |
|------|-----------|
| Very High | ≥80 or Critical+Confirmed/Likely |
| High | 45–79 or Critical+Potential or High+Confirmed/Likely |
| Medium | 15–44 or Medium+Confirmed/Likely or 5+ Low |
| Low | else |

| Decision | When |
|----------|------|
| BLOCK MERGE | Very High or Critical+Confirmed |
| REQUEST CHANGES | High or any Critical or High+Confirmed |
| APPROVE WITH COMMENTS | Medium or High+Potential only |
| APPROVE | Low, no Critical/High |

# Incomplete context

Gap → impact → lower confidence → Limitations. Never invent unread code.

# Depth reference

Only **deep** profile may open [`references/review-depth.md`](./references/review-depth.md).  
Stacks: `stack_excerpts` first; headings from [`references/tech-stacks.md`](./references/tech-stacks.md) only if incomplete.
