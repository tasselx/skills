---
name: deep-review
description: Perform a read-only, defect-first code review of a specified code change and return every actionable finding. Use when the user asks to review code, review a PR, review a diff, review uncommitted changes, review a commit, or explicitly invokes deep-review.
---

# Deep Review

Perform a thorough, defect-first review of a code change and return every actionable finding. This skill is read-only: it never modifies code, stages files, commits, or pushes.

This skill is agent-neutral. Use it from Codex, Claude Code, Cursor, OpenCode, Gemini CLI, or any other coding agent that can read this `SKILL.md` file and run local shell commands.

## Quick Workflow

1. Verify the current directory is a Git repository.
2. Locate the skill directory. If this file is loaded from disk, use its parent directory as `SKILL_DIR`; otherwise ask the user for the installed `deep-review` skill path.
3. Determine the review target (see [Review Targets](#review-targets) below).
4. Run the read-only context helper to gather the diff snapshot:

```bash
export SKILL_DIR="/path/to/deep-review"
python3 "$SKILL_DIR/scripts/collect_review_context.py"
```

For a specific commit range or base branch, pass arguments:

```bash
# Review a specific commit
python3 "$SKILL_DIR/scripts/collect_review_context.py" --commit <sha>

# Review all commits on the current branch vs base branch
python3 "$SKILL_DIR/scripts/collect_review_context.py" --base main
```

5. Read the full diff content and inspect the changed files.
6. Run the review across all categories defined in [Review Categories](#review-categories).
7. Read `$SKILL_DIR/references/review-checklist.md` for the detailed checklist when a category needs deeper analysis.
8. Compile and present findings using the [Finding Format](#finding-format).
9. Provide a summary with counts by severity.

## Review Targets

Determine what to review based on user intent:

| User says | Target |
|-----------|--------|
| "review this", "review changes" | All uncommitted changes (staged + unstaged) |
| "review staged" | Staged changes only (`--cached`) |
| "review commit \<sha\>" | A specific commit (`--commit <sha>`) |
| "review this branch", "review vs main" | All commits on current branch vs base (`--base main`) |
| "review PR #N", "review MR" | Diff between merge-base of base and HEAD |
| "review file X" | Full content of a specific file |

If the target is ambiguous, ask the user to clarify before proceeding.

## Review Categories

Review every changed file across these categories. Not every category applies to every file, but you must consciously consider each.

### 1. Correctness & Logic
- Logic errors, off-by-one, incorrect conditions, wrong operator usage.
- Unhandled null/None/undefined/nil cases.
- Race conditions, deadlocks, ordering issues.
- Incorrect error propagation or swallowing.
- State mutation side effects.

### 2. Security
- Injection vulnerabilities (SQL, command, path traversal, XSS).
- Hardcoded secrets, credentials, API keys.
- Improper input validation or sanitization.
- Insecure deserialization, SSRF, open redirects.
- Overly permissive access control.

### 3. Performance
- Unnecessary allocations, redundant computations.
- N+1 query patterns, missing indexes.
- O(n²) or worse loops on potentially large data.
- Missing pagination for large result sets.
- Blocking I/O in async contexts.

### 4. API Design & Compatibility
- Breaking changes to public APIs, signatures, or contracts.
- Inconsistent naming, parameter ordering, or return types.
- Missing or incorrect type annotations.
- Improper HTTP status codes or error response shapes.

### 5. Error Handling & Resilience
- Missing error handling for network, I/O, or parse operations.
- Catching too broadly (swallowing all exceptions).
- Missing retry, timeout, or circuit breaker for external calls.
- Resource leaks (unclosed files, connections, streams).

### 6. Test Coverage
- Changed logic without corresponding test updates.
- Missing tests for new public methods or endpoints.
- Tests that do not actually assert the behavior they claim to.
- Flaky test patterns (time-dependent, order-dependent, external state).

### 7. Maintainability & Code Quality
- Dead code, unreachable branches, unused imports/variables.
- Overly complex functions (high cyclomatic complexity).
- Magic numbers, hardcoded values that should be constants.
- Insufficient or misleading comments and documentation.

## Finding Format

Report each finding in this format:

```text
### [SEVERITY] Short title

**File:** `path/to/file.ext:line` (or line range)
**Category:** Correctness | Security | Performance | API Design | Error Handling | Tests | Maintainability

Description of the issue, what can go wrong, and the context needed to understand it.

**Suggestion:** Concrete, actionable fix or approach. Code snippet when helpful.
```

### Severity Levels

- **CRITICAL** — Must fix before merge. Security vulnerabilities, data loss, crashes, correctness bugs in core logic.
- **WARNING** — Should fix before merge. Likely bugs, fragile patterns, missing edge case handling, insufficient tests.
- **SUGGESTION** — Optional improvement. Cleaner code, better naming, minor refactor, documentation gaps.
- **PRAISE** — Highlighting good practices worth keeping. Helps reinforce what is working well.

## Review Principles

- **Defect-first**: Prioritize finding real defects over style nits. Start with the most impactful categories (Correctness, Security) before moving to maintainability.
- **Evidence-based**: Every finding must cite the specific file, line, and code snippet. Never report a vague suspicion without grounding it in the actual diff.
- **Actionable**: Every finding must include a concrete suggestion, not just "this is wrong". If you cannot suggest a fix, say so explicitly.
- **No false positives**: If you are not confident a finding is real, downgrade severity or omit it. Noise degrades trust in all findings.
- **Read the actual code**: Do not infer behavior from filenames or commit messages. Open and read the surrounding context of each changed hunk.
- **Scope to the diff**: Review what changed, not the entire codebase. But read enough surrounding context to understand the impact of each change.
- **Read-only**: Never modify, stage, commit, or push. This skill only reports findings.

## Output Structure

Present the review in this order:

1. **Review Scope** — What was reviewed (target, files, line counts).
2. **Summary** — Count of findings by severity: `N critical, N warnings, N suggestions, N praise`.
3. **Findings** — Each finding in the [Finding Format](#finding-format) above, ordered by severity (Critical first, then Warning, Suggestion, Praise).
4. **Overall Assessment** — One-paragraph summary of the change's quality and whether it is ready to merge.

If there are zero findings, explicitly state that no defects were found and note what was reviewed.

## Slash Command Prompt

For agents that support slash commands, create `/deep-review` with the prompt in `commands/deep-review.md`. The slash command should invoke this skill, then follow the same review workflow.
