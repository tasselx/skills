Use the `deep-review` skill from this repository or installed skills directory.

Task:
Perform a production-level, read-only code review of the current code changes and return every actionable finding.

Quick Workflow:
1. Run `git status`, `git diff`, and `git diff --cached` to identify all uncommitted changes (modified, added, deleted, renamed files). Read complete changed files, surrounding code, related classes, interfaces, callers, dependencies. If no uncommitted changes, explain "No local changes were found." and ask which target to review.
2. Beyond the changed files themselves, read surrounding code, related classes, interfaces, callers, and dependencies to understand the full impact.
3. Classify the change type (bug fix, feature, refactor, dependency update, configuration change, etc.) and adjust review focus.
4. Reconstruct change intent: goal, approach, affected components, expected behavior. Compare expected vs actual.
5. Analyze impact: trace callers, dependencies, data flow, API contracts. Look for breaking changes and side effects.
6. Review across all categories in priority order: correctness → reliability → security → performance → architecture → testing → regression → observability → deployment safety. Apply technology-specific checks when applicable (see references/tech-stacks.md).
7. Scan for common production bug patterns: state, async, error handling, data, resource, security.
8. Verify, deduplicate, finalize: (a) verify triggerability — Can I point to exact code? Can I describe how it fails? Would a production engineer care? Drop if any answer is no. (b) Deduplicate — combine findings caused by the same root cause. (c) Self-verify — Is there enough evidence? Could existing code prevent it? Would it happen in production? Remove weak findings.
9. Compile findings with severity + confidence, sorted by severity → confidence → impact → probability → recovery difficulty.
10. Calculate risk score (severity × confidence) and merge decision.

Review targets:
- uncommitted (default): `git diff HEAD` + `git diff --cached`
- staged: `git diff --cached`
- commit: `git show <sha>`
- branch-diff: `git diff <base>...HEAD`
- file: read full file content directly
- If no uncommitted changes, explain "No local changes were found." and ask which target to review.
- If diff exceeds 50 files or 2000 lines, warn that the change set is too large and recommend reviewing critical modules first.

Finding format (use exactly):
```text
### [SEVERITY] Short title

**Confidence:** Confirmed | Likely | Potential
**Location:** `path/to/file.ext:line` (or line range)
**Category:** Correctness | Reliability | Security | Performance | Architecture | Testing | Regression | Observability | Deployment | Maintainability

Description of the issue, what can go wrong, and the context needed to understand it.

**Evidence:** Cite the specific code behavior that proves or suggests the issue.

**Recommendation:** Concrete, actionable fix or approach. Code snippet when helpful.
```

Severity levels:
- **Critical** — Must fix before merge. Security vulnerability, data loss, production crash, severe business logic failure.
- **High** — Should fix before release. Major reliability problem, incorrect behavior, serious performance issue.
- **Medium** — Important improvement. Risky implementation, missing validation, maintainability problem.
- **Low** — Minor improvement. Only report if it provides real value.

Confidence levels:
- **Confirmed** — Evidence clearly proves the problem exists.
- **Likely** — Strong possibility based on code behavior.
- **Potential** — Only happens under specific conditions.

Risk Score (severity × confidence):
- Critical (Confirmed/Likely) → Very High
- Critical (Potential) → High
- High (Confirmed/Likely) → High
- High (Potential) → Medium
- Any Medium → Medium
- 5+ Low → Medium
- Only Low or no findings → Low
- If all findings are Potential, cap at Medium

Final report must include:
- **Review Summary**: files reviewed, issue counts by severity, risk level
- **Merge Decision**: APPROVE / APPROVE WITH COMMENTS / REQUEST CHANGES / BLOCK MERGE
- **Review Limitations**: missing runtime context, unavailable external services, unavailable production data, inaccessible files
- **Questions for Author**: when clarification is needed

Rules:
- This skill is read-only: never modify files, create commits, rewrite code, apply fixes, or generate patches.
- Do not report false positives. Before reporting, verify: Can I point to exact code? Can I describe how it fails? Would a production engineer care? If any answer is no, drop it.
- Do not create findings only to make the review longer. Prefer real defect over possible defect, evidence over speculation, production impact over theoretical concern.
- Do not review like a formatter. Do not focus on personal style preference, naming preference, or cosmetic changes.
- If the diff contains multiple unrelated changes, flag it. List the change groups, recommend splitting, and organize findings by group.
- Write findings with neutral, factual tone. Describe what the code does, not what the author did wrong. No condescending language, no speculation about intent.
- Check cross-file consistency: interface changes propagated to all callers and tests?
- For monorepo multi-package changes, trace the dependency graph between changed packages and highlight cross-package contract issues.
- For generated code, skip unless the generator config changed. For docs-only, focus on accuracy. For test-only, focus on test correctness. For binary files, flag only size/type/metadata issues.
- When context is incomplete, identify the gap, assess impact, downgrade confidence, and flag in Review Limitations. Do not fabricate behavior of inaccessible code.
