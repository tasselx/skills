Use the `deep-review` skill from this repository or installed skills directory.

Task:
Perform a production-level, read-only code review of the current code changes and return every actionable finding.

Workflow:
- Run `git status`, `git diff`, and `git diff --cached` to identify all uncommitted changes (modified, added, deleted, renamed files).
- If no uncommitted changes exist, explain "No local changes were found." and ask whether to review the latest commit, a branch diff, or specific files.
- Read the complete changed files, surrounding code, related classes, interfaces, callers, and dependencies to understand the full context.
- Classify the change type (bug fix, feature, refactor, dependency update, configuration change, etc.) and adjust review focus accordingly.
- Review across all categories: correctness, reliability, security, performance, architecture, testing, regression, observability, and deployment safety.
- Consider common production bug patterns: state bugs, async bugs, error handling bugs, data bugs, resource bugs, and security bugs.
- For each finding, apply false positive prevention: only report issues with a clear execution path and production impact.
- Deduplicate findings by root cause.

Finding format:
For every issue, report:
- **[Severity] Title** — Severity is Critical / High / Medium / Low
- **Confidence:** Confirmed / Likely / Potential
- **Location:** file:line
- **Evidence:** Explain the code behavior that proves or suggests the issue
- **Problem:** Explain exactly what is wrong
- **Impact:** Explain possible consequences
- **Recommendation:** Provide practical solution direction

Severity levels:
- **Critical** — Must fix before merge. Security vulnerability, data loss, production crash, severe business logic failure.
- **High** — Should fix before release. Major reliability problem, incorrect behavior, serious performance issue.
- **Medium** — Important improvement. Risky implementation, missing validation, maintainability problem.
- **Low** — Minor improvement. Only report if it provides real value.

Sort findings by: severity → confidence → user impact → probability → recovery difficulty. Critical + Confirmed always first.

Final report must include:
- **Review Summary**: files reviewed, issue counts by severity, risk level (Low / Medium / High / Very High), overall result (READY TO COMMIT / NEEDS FIXES BEFORE COMMIT / HIGH RISK - INVESTIGATE)
- **Merge Recommendation**: APPROVE / APPROVE WITH COMMENTS / REQUEST CHANGES / BLOCK MERGE
- **Review Limitations**: missing runtime context, unavailable external services, unavailable production data
- **Questions for Author**: when clarification is needed

Rules:
- This skill is read-only: never modify files, create commits, rewrite code, apply fixes, or generate patches.
- Do not report false positives. Before reporting, verify: Can I point to exact code? Can I describe how it fails? Would a production engineer care?
- Do not create findings only to make the review longer. Prefer real defect over possible defect, evidence over speculation, production impact over theoretical concern.
- Do not review like a formatter. Do not focus on personal style preference, naming preference, or cosmetic changes.
