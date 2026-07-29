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

# Output Language

Adapt the review output language to the environment:

1. **User override** — If the user explicitly specifies a language (e.g. "用中文审查", "review in English"), honor that choice.
2. **System locale is Chinese** — If the system locale is a Chinese variant (`zh_CN`, `zh_TW`, `zh_HK`, `zh_MO`, `zh_SG`, or any `zh_*`), output in **Chinese**.
3. **Otherwise** — output entirely in **English**.

Detect locale from the environment (e.g. `LANG`, `LC_ALL`, `LC_MESSAGES`). Prefer the first available value; match case-insensitively on a `zh` prefix (including `zh_CN.UTF-8`).

When outputting in **Chinese**:
- Finding titles, descriptions, Evidence/Trigger/Fix prose, Review Summary **Why**, Limitations, and Questions for Author → Chinese.
- Code identifiers, file paths, git commands, and technical tokens stay in English as-is.
- Machine-parseable labels stay in English: severity (`CRITICAL` / `HIGH` / …), confidence (`Confirmed` / `Likely` / `Potential`), category (`Security` / …), merge decision (`APPROVE` / `REQUEST CHANGES` / …), and table field keys (`Decision`, `Risk`, `Issues`, `Files`, `Stacks`).

When outputting in **English**:
- Everything in English, including findings, summary Why, limitations, and questions.

Kickoff / progress lines follow the same language choice. Do not mix Chinese and English prose in the same review (except the English tokens listed above).

# Fast Workflow (do not invent extra steps)

Minimize tool rounds. Default path is **≤3 tool batches**.

**Progressive output (required):** stream findings as you confirm them. Do **not** buffer every issue until the end.

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

After this batch: print a one-line kickoff only, e.g.  
`Reviewing N files (mode=…, stacks=…). Streaming findings…`

Do **not** print the final Summary yet.

## 3. Analyze and emit (stream)

Work intent → impact → defects. Prefer high-risk paths first (security, migrations, production).

**Emit rule:** once a finding passes the gate (location + trigger + evidence + not a dupe), **immediately print its full detail block** in the user-visible reply. Then continue scanning.

1. **Intent** — goal, approach, expected vs actual; use `change_types` (+ commit subject).
2. **Impact** — callers/contracts/data flow as needed; monorepo → `package_roots`; mixed → note group in the finding body.
3. **Defect scan** (only fitting categories): correctness, reliability, security, performance, architecture (if real risk), testing, regression, observability, deployment; plus stack excerpts and bug patterns (state/async/errors/data/resources/trust).
4. **Gate → print** — each confirmed finding gets the next monotonic `#` and is written out **before** more tool calls when possible. Drop weak/speculative items silently (do not announce drops).
5. **Close out** — after the scan (or when large-diff batch ends), print index table (if ≥2), then Review Summary, then Limitations/Questions if any.

Between findings: optional one short status line is OK (`…still checking auth callers`). No long preambles, no “full report coming next”.

If a later finding supersedes an earlier one (same root cause): print a one-line correction  
`~~#N~~ superseded by #M (same root cause)`  
and only count `#M` in the Summary score.

## 4. Tool interleaving

You **may** emit text findings and then call more tools (read callers, etc.). Never hold back a full Finding Detail until the entire review is done. Summary tables are the only block that must wait until the end.

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

# Output Format

Render as normal markdown (not one giant code fence). Optimize for **narrow CLI** and scanability.

Markers: Critical 🔴 · High 🟠 · Medium 🟡 · Low 🟢  
Decision badges: ✅ APPROVE · ⚠️ APPROVE WITH COMMENTS · 🔧 REQUEST CHANGES · 🛑 BLOCK MERGE

## Order (streaming)

**While reviewing (live):**
1. One-line kickoff after snapshot/evidence load.
2. Each finding **detail block as soon as it is confirmed** (numbered `#1`, `#2`, …). Prefer emitting Critical/High before Low when several are ready.
3. Optional short progress lines between batches.

**At the end only:**
4. **Finding index table** if total findings ≥ 2 (rebuild from emitted items; severity sort for the table is OK even if emit order differed).
5. **Review Summary** (Decision / Risk / Issues / Files / Stacks / Why).
6. **Limitations** / **Questions for Author** if non-empty.

No findings → no detail blocks; end with Summary `✅ No issues found.`

Do **not** wait to print details until the Summary is ready. The index table and Summary are the closing section, not the first place findings appear.

## Finding index (end, when ≥2 findings)

Print **after** all detail blocks, immediately before Review Summary:

```markdown
## Findings index

| # | Sev | Conf | Loc | Title |
|---|-----|------|-----|-------|
| 1 | 🔴 C | Confirmed | `a.py:42` | SQL injection in search |
| 2 | 🟠 H | Likely | `b.go:28` | Off-by-one skips page 0 |
```

Sev abbrev in table only: `C` Critical · `H` High · `M` Medium · `L` Low.  
Sort rows by severity → confidence (user scan), even if live emit order was discovery order.  
One finding → skip the index table.

## Finding detail

```markdown
### 1. 🔴 [CRITICAL] Short title

| | |
|---|---|
| **Confidence** | Confirmed |
| **Category** | Security |
| **Location** | `path/to/file.ext:line` |

When `query` is attacker-controlled, the handler builds SQL via string concat and executes it.

- **Evidence:** `search.py:42` uses `f"...{query}..."` in `cursor.execute(...)`.
- **Trigger:** any unauthenticated `GET /search?q=`; likelihood High.
- **Fix:** parameterized query, e.g. `cursor.execute("... LIKE %s", (f"%{query}%",))`.
```

Rules:
- Keep title ≤12 words; put mechanism in body.
- Evidence must cite `` `path:line` ``.
- Fix is actionable; snippet ≤8 lines when helpful.
- Do **not** wrap findings in `>` blockquotes (breaks nest/scan in CLI).
- Do **not** dump full files or long patches in Fix.
- Related root cause → one finding, mention sibling locations in Evidence.

## Review Summary (always)

```markdown
---

## Review Summary

| Field | Value |
|-------|-------|
| **Decision** | 🔧 REQUEST CHANGES |
| **Risk** | High (raw 55; band: High+Confirmed) |
| **Issues** | 🔴 0 · 🟠 1 · 🟡 2 · 🟢 0 |
| **Files** | `a.py`, `b.go` (+N more if long) |
| **Stacks** | Python, Backend — or `none` |

**Why:** one or two sentences citing the highest finding(s) and score rule.
```

Optional second line under Issues when zero: `✅ No issues found.`

Skip Severity Chart ASCII bars and Risk Meter ASCII gauges — the summary table replaces both.

## Limitations / Questions

```markdown
## Review Limitations
- …

## Questions for Author
- …
```

Omit a section entirely when empty. No placeholder verbiage.

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

# Incomplete Context

State the gap → impact → lower confidence if needed → list in Limitations → never invent unread behavior.

# Tests (optional evidence)

Run targeted tests only for auth/payments/migrations/concurrency, confidence flip, or user request. No full suite by default. Failures may raise confidence; they alone do not force Critical.

# Depth Reference

Optional: [`references/review-depth.md`](./references/review-depth.md) for extended category prompts, examples, and edge-case handling.  
Stack checklists: embedded `stack_excerpts` or [`references/tech-stacks.md`](./references/tech-stacks.md) by heading only.
