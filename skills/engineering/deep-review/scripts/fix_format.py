#!/usr/bin/env python3
"""Update SKILL.md finding format and examples with colored blockquote style."""

path = "skills/engineering/deep-review/SKILL.md"
with open(path, "r") as f:
    content = f.read()

replacements = [
    # 1. Finding Output Format + Severity Color Markers
    (
        """# Finding Output Format

For every issue, use this exact format:

```text
### [SEVERITY] Short title

**Confidence:** Confirmed | Likely | Potential
**Location:** `path/to/file.ext:line` (or line range)
**Category:** Correctness | Reliability | Security | Performance | Architecture | Testing | Regression | Observability | Deployment | Maintainability

Description of the issue, what can go wrong, and the context needed to understand it.

**Evidence:** Cite the specific code behavior that proves or suggests the issue.

**Recommendation:** Concrete, actionable fix or approach. Code snippet when helpful.
```

## Severity Color Markers

Use a colored emoji marker at the start of each finding heading so reviewers can
visually scan severity at a glance:

| Severity | Marker | Meaning |
|----------|--------|---------|
| Critical | :red_circle: `[CRITICAL]` | Must fix before merge |
| High | :orange_circle: `[HIGH]` | Should fix before release |
| Medium | :yellow_circle: `[MEDIUM]` | Important improvement |
| Low | :green_circle: `[LOW]` | Minor improvement |""",
        """# Finding Output Format

For every issue, use this exact format. The colored blockquote bar gives instant visual scanning:

```text
> ### <MARKER> [SEVERITY] Short title
>
> **Confidence:** Confirmed | Likely | Potential  
> **Location:** `path/to/file.ext:line` (or line range)  
> **Category:** Correctness | Reliability | Security | Performance | Architecture | Testing | Regression | Observability | Deployment | Maintainability

Description of the issue, what can go wrong, and the context needed to understand it.

**Evidence:** Cite the specific code behavior that proves or suggests the issue.

**Recommendation:** Concrete, actionable fix or approach. Code snippet when helpful.
```

## Severity Color Markers

Use a colored emoji marker and blockquote bar at the start of each finding so reviewers can
visually scan severity at a glance:

| Severity | Marker | Bar | Meaning |
|----------|--------|-----|---------|
| Critical | \U0001f534 `[CRITICAL]` | `> \U0001f534` | Must fix before merge |
| High | \U0001f7e0 `[HIGH]` | `> \U0001f7e0` | Should fix before release |
| Medium | \U0001f7e1 `[MEDIUM]` | `> \U0001f7e1` | Important improvement |
| Low | \U0001f7e2 `[LOW]` | `> \U0001f7e2` | Minor improvement |"""
    ),
    # 2. Example 1
    (
        '### :red_circle: `[CRITICAL]` SQL injection',
        '### \U0001f534 [CRITICAL] SQL injection'
    ),
    (
        """```text
### :red_circle: [CRITICAL] SQL injection via unsanitized user input in search endpoint

**Confidence:** Confirmed
**Location:** `src/api/search.py:42`
**Category:** Security""",
        """```text
> ### \U0001f534 [CRITICAL] SQL injection via unsanitized user input in search endpoint
>
> **Confidence:** Confirmed  
> **Location:** `src/api/search.py:42`  
> **Category:** Security"""
    ),
    # 3. Example 2
    (
        """```text
### :orange_circle: [HIGH] Off-by-one error in pagination loop skips first result page

**Confidence:** Likely
**Location:** `src/services/paginator.go:28-35`
**Category:** Correctness""",
        """```text
> ### \U0001f7e0 [HIGH] Off-by-one error in pagination loop skips first result page
>
> **Confidence:** Likely  
> **Location:** `src/services/paginator.go:28-35`  
> **Category:** Correctness"""
    ),
    # 4. Example 3
    (
        """```text
### :yellow_circle: [MEDIUM] Missing timeout on outbound HTTP call may hang indefinitely

**Confidence:** Potential
**Location:** `src/clients/payment.go:67`
**Category:** Reliability""",
        """```text
> ### \U0001f7e1 [MEDIUM] Missing timeout on outbound HTTP call may hang indefinitely
>
> **Confidence:** Potential  
> **Location:** `src/clients/payment.go:67`  
> **Category:** Reliability"""
    ),
    # 5. Example 4
    (
        """```text
### :green_circle: [LOW] Magic number without named constant reduces readability

**Confidence:** Confirmed
**Location:** `src/utils/pricing.ts:15`
**Category:** Maintainability""",
        """```text
> ### \U0001f7e2 [LOW] Magic number without named constant reduces readability
>
> **Confidence:** Confirmed  
> **Location:** `src/utils/pricing.ts:15`  
> **Category:** Maintainability"""
    ),
]

count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new, 1)
        count += 1
    else:
        print(f"NOT FOUND: {old[:60]}...")

with open(path, "w") as f:
    f.write(content)
print(f"OK: replaced {count}/{len(replacements)} blocks")
