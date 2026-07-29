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

Senior production review. Goal: decide if the change is safe to ship — not to pad findings.

**Prefer:** real defect > speculation, evidence > style, production impact > theory.

**Read-only:** never modify files, commit, push, rewrite code, apply fixes, or generate patches.

**Tone:** neutral and factual (“When X, Y may happen”). No condescension, no filler.

**Language:** honor user request; else Chinese if locale is `zh_*`, otherwise English. Keep severity/confidence/category tokens and code/paths/commands in English.

# Fast Workflow (do not invent extra steps)

Minimize tool rounds. Default path is **≤3 tool batches**.

## 1. Snapshot (required first)

```bash
export SKILL_DIR="/path/to/deep-review"
python3 "$SKILL_DIR/scripts/review_snapshot.py"
# modes:
# --mode staged
# --mode commit --commit HEAD
# --mode branch-diff --base main
# --mode file --file path/a.py
# optional: --compact  --no-diff  --risk-matrix
```

Trust snapshot. **Do not** re-run `git status` after a successful snapshot.

Key fields: `has_changes`, `empty_hint`, `large_diff`, `change_types`, `detected_stacks`,
`must_read_tech_stack_sections`, `stack_excerpts`, `stack_excerpts_complete`,
`diff_patch`, `package_roots`, `mixed_changes_suspected`, `prioritized_paths`,
`excluded_paths`, `full_file_read_paths`, `patch_likely_enough_paths`, `files`, `agent_hints`.

If `has_changes` is false → print `empty_hint` and ask for target. Stop.

## 2. Load evidence (parallel, one batch)

| Source | Rule |
|--------|------|
| `diff_patch.patch` | Use when `diff_patch.included` and not needing a wider range. If `truncated`, run **one** mode-specific `git diff` / `git show` only for missing paths. |
| `stack_excerpts.sections` | Apply when present. If `stack_excerpts_complete` is true, **do not** open full `tech-stacks.md`. If incomplete/missing, read only the missing headings from `references/tech-stacks.md` (not the whole file). |
| Files | Read `full_file_read_paths` first (parallel). Use patch alone for `patch_likely_enough_paths` unless callers/contracts are unclear. Skip `excluded_paths` unless they are the target. Cap full-file reads on large diffs: security + migrations + top risk production files first. |
| Context | Grep/open callers **only** for changed public APIs, shared types, or suspected breakages — not blanket repo walks. |

Never reload this `SKILL.md`. Load `references/review-depth.md` only for large/high-risk changes or calibration disputes.

## 3. Single-pass analysis

Work from intent → impact → defects in **one mental pass** (not nine serial tool loops).

1. **Intent** — goal, approach, expected vs actual behavior; classify via `change_types` (+ commit subject if any).
2. **Impact** — callers, contracts, data/state flow; monorepo → `package_roots`; mixed → group findings.
3. **Defect scan** (use only categories that fit; drop N/A silently):
   - Correctness, Reliability, Security, Performance
   - Architecture (only if risk/debt is real), Testing, Regression
   - Observability, Deployment safety
   - Stack excerpts + bug patterns: state, async, errors, data, resources, trust boundaries
4. **Gate each finding** — exact location, realistic trigger path, production relevance. Deduplicate by root cause. Drop weak/speculative items.
5. **Score + report** — weights below → risk band → merge decision → final summary.

# Scope Cheatsheet

**Exclude by default:** generated, lockfiles, binaries (`excluded_paths`).

**Prioritize:** business logic, production code, public interfaces, security-sensitive, persistence/network, migrations.

**Large diff** (`large_diff`): say so; review `prioritized_paths` / security first; partial report OK; list unscanned paths under Limitations.

**Mixed changes:** flag, group findings, still finish review.

**Special:** generated output without generator-config change → skip; docs-only → accuracy/completeness; test-only → test correctness/isolation; binaries → size/type/metadata only.

# Finding Rules

Every finding needs: evidence (file + line + behavior), trigger path (who/what, conditions, likelihood), severity, confidence.

**Confidence:** Confirmed | Likely | Potential  
**Severity:** Critical (outage/data loss/exploitable) · High (common-path wrongness/reliability) · Medium (real but limited) · Low (only if useful)

False positives to avoid: style/preference, no execution path, uncommon edges without impact.

Sort: severity → confidence → impact → probability → recovery difficulty.

# Finding Format

```text
> ### <MARKER> [SEVERITY] Short title
>
> **Confidence:** Confirmed | Likely | Potential
> **Location:** `path/to/file.ext:line`
> **Category:** Correctness | Reliability | Security | Performance | Architecture | Testing | Regression | Observability | Deployment | Maintainability

Description (what goes wrong, when).

**Evidence:** concrete code behavior.
**Recommendation:** actionable fix (snippet if helpful).
```

Markers: Critical 🔴 · High 🟠 · Medium 🟡 · Low 🟢

# Risk Score & Merge

| Severity | Confirmed | Likely | Potential |
|----------|-----------|--------|-----------|
| Critical | 100 | 80 | 45 |
| High | 55 | 40 | 22 |
| Medium | 20 | 14 | 8 |
| Low | 4 | 3 | 1 |

Raw score = sum after dedupe.  
Root-cause cluster (3+): highest full weight, extras 25%.  
All-Potential → cap risk at Medium.  
Medium+Potential alone with score < 15 → Low.

| Risk | Condition |
|------|-----------|
| Very High | score ≥ 80 **or** Critical+Confirmed/Likely |
| High | 45–79 **or** Critical+Potential **or** High+Confirmed/Likely |
| Medium | 15–44 **or** Medium+Confirmed/Likely **or** 5+ Low |
| Low | otherwise |

| Decision | When |
|----------|------|
| **BLOCK MERGE** | Very High, or Critical+Confirmed |
| **REQUEST CHANGES** | High, or any Critical, or High+Confirmed |
| **APPROVE WITH COMMENTS** | Medium, or only High+Potential / non-blocking Medium |
| **APPROVE** | Low, no Critical/High |

# Final Report

---

## Review Summary

**Files reviewed:** …  
**Stacks applied:** … (from excerpts or "none")

### Severity Chart

Bars proportional to counts (max 40 `█`). Skip zeros. All zero → `✅ No issues found.`

### Risk Meter

```
Low          Medium        High       Very High
[....]  ← (Raw score: N, band: X)
```

> **Merge Decision:** ✅ APPROVE | ⚠️ APPROVE WITH COMMENTS | 🔧 REQUEST CHANGES | 🛑 BLOCK MERGE

**Final Decision:** one short paragraph (top findings + band rule).

## Review Limitations

Gaps, missing runtime/services/data, unread paths, truncated diff.

## Questions for Author

Only when needed (approach constraints, compatibility, deploy).

---

# Incomplete Context

State the gap → impact → lower confidence if needed → list in Limitations → never invent unread behavior.

# Tests (optional evidence)

Run targeted tests only for auth/payments/migrations/concurrency, confidence flip, or user request. No full suite by default. Failures may raise confidence; they alone do not force Critical.

# Depth Reference

Optional: [`references/review-depth.md`](./references/review-depth.md) for extended category prompts, examples, and edge-case handling.  
Stack checklists: embedded `stack_excerpts` or [`references/tech-stacks.md`](./references/tech-stacks.md) by heading only.
