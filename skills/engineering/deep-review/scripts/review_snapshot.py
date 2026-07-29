#!/usr/bin/env python3
"""Print a read-only Git review snapshot for the deep-review skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


GENERATED_RE = re.compile(
    r"(^|/)(node_modules|build|dist|coverage|\.dart_tool|Pods|DerivedData|\.cache|target"
    r"|__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|\.venv|venv"
    r"|vendor/bundle|\.gradle|\.idea)(/|$)|"
    r"\.(lockb|png|jpg|jpeg|gif|webp|ico|svg|woff2?|ttf|eot|zip|gz|tar|tgz|7z|dmg"
    r"|xcarchive|pyc|pyo|class|o|a|so|dylib|dll|exe|wasm|pb\.go|pb\.cc|generated\.)",
    re.IGNORECASE,
)

LOCKFILE_RE = re.compile(
    r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|Cargo\.lock|poetry\.lock"
    r"|Pipfile\.lock|composer\.lock|Gemfile\.lock|go\.sum|bun\.lockb?)(/|$)",
    re.IGNORECASE,
)

BINARY_RE = re.compile(
    r"\.(png|jpg|jpeg|gif|webp|ico|woff2?|ttf|eot|zip|gz|tar|tgz|7z|dmg|pdf"
    r"|mp3|mp4|mov|wav|bin|exe|dll|so|dylib|wasm|pb|model|onnx|gguf)$",
    re.IGNORECASE,
)

DOCS_RE = re.compile(
    r"(^|/)(docs?|changelog|changes|history)(/|$)|"
    r"(^|/)(readme|contributing|code_of_conduct|security|license)(\.[^/]+)?$|"
    r"\.(md|mdx|rst|adoc|txt)$",
    re.IGNORECASE,
)

TEST_RE = re.compile(
    r"(^|/)(tests?|__tests__|spec|specs)(/|$)|"
    r"(_test|\.test|\.spec|_spec|Test|Spec)\.[^/]+$|"
    r"(^|/)test_[^/]+$|"
    r"(^|/)[^/]+_test\.[^/]+$",
    re.IGNORECASE,
)

CONFIG_RE = re.compile(
    r"(^|/)(\.github|\.gitlab|deploy|deployment|infra|infrastructure|k8s|helm|terraform"
    r"|docker|ci|cd)(/|$)|"
    r"(Dockerfile|docker-compose|compose\.ya?ml|\.ya?ml|\.toml|\.ini|\.cfg|\.conf"
    r"|\.env\.example|Makefile|Justfile|\.gitignore|\.editorconfig)$|"
    r"(tsconfig|jsconfig|vite\.config|webpack\.config|rollup\.config|babel\.config"
    r"|eslint|prettier|ruff|mypy|pytest|pyproject|setup\.cfg|Cargo\.toml|go\.mod"
    r"|package\.json|pubspec\.yaml|build\.gradle|settings\.gradle|Podfile"
    r"|Gemfile|composer\.json|\.tf)$",
    re.IGNORECASE,
)

MIGRATION_RE = re.compile(
    r"(^|/)(migrations?|alembic|flyway|liquibase|db/migrate|prisma/migrations)(/|$)|"
    r"(migration|_migrat).*\.(sql|py|rb|ts|js)$",
    re.IGNORECASE,
)

SECURITY_PATH_RE = re.compile(
    r"(auth|oauth|jwt|session|password|credential|permission|rbac|acl|crypto|tls|ssl|"
    r"secret|token|security|encrypt|decrypt|sanitize|csrf|cors)",
    re.IGNORECASE,
)

# Extension / path → tech-stacks.md section id
STACK_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\.(dart)$|(^|/)pubspec\.ya?ml$", re.I), "flutter-dart"),
    (re.compile(r"\.(tsx?|jsx?|vue|svelte)$|(^|/)(react|next|vite|nuxt)", re.I), "frontend"),
    (re.compile(r"\.(swift|m|mm)$|(^|/)Package\.swift$", re.I), "ios"),
    (re.compile(r"\.(kt|kts|java)$|(^|/)(AndroidManifest\.xml|build\.gradle)", re.I), "android"),
    (re.compile(r"(^|/)(Dockerfile|.*\.tf$|.*\.tfvars$|helm/|k8s/|\.github/workflows/)", re.I), "devops"),
    (re.compile(r"\.(py)$|(^|/)(pyproject\.toml|requirements.*\.txt|setup\.py)$", re.I), "python"),
    (re.compile(r"\.(go)$|(^|/)go\.mod$", re.I), "go"),
    (re.compile(r"\.(rs)$|(^|/)Cargo\.toml$", re.I), "rust"),
    (re.compile(r"\.(cs|fs|vb)$|(^|/)(.*\.csproj|.*\.fsproj|.*\.sln)$", re.I), "dotnet"),
    (re.compile(r"\.(rb|erb|rake)$|(^|/)(Gemfile|Rakefile)$", re.I), "ruby-rails"),
    (re.compile(r"\.(php)$|(^|/)composer\.json$", re.I), "php"),
    (re.compile(r"\.(c|cc|cpp|cxx|h|hpp|hxx)$", re.I), "c-cpp"),
    (re.compile(r"\.(graphql|gql)$", re.I), "graphql"),
    (re.compile(r"\.(sql)$|(^|/)(prisma/|drizzle/|migrations?/)", re.I), "database-sql"),
    (re.compile(r"(react-native|expo)", re.I), "react-native"),
    (re.compile(r"(Assets/|ProjectSettings/|\.unity$|\.uproject$|Content/)", re.I), "game"),
    (re.compile(r"\.(ts|js|mjs|cjs)$|(^|/)package\.json$", re.I), "nodejs-typescript"),
    (re.compile(r"\.(java|kt)$|(^|/)(pom\.xml|build\.gradle\.kts)$", re.I), "jvm"),
]

STACK_SECTION_TITLES = {
    "flutter-dart": "Flutter / Dart",
    "frontend": "Frontend (React / Vue / Angular / Svelte)",
    "ios": "iOS (Swift / Objective-C)",
    "android": "Android (Kotlin / Java)",
    "devops": "DevOps / Infrastructure (Terraform / K8s / CI-CD)",
    "python": "Python",
    "go": "Go",
    "rust": "Rust",
    "dotnet": ".NET / C#",
    "ruby-rails": "Ruby / Rails",
    "php": "PHP",
    "c-cpp": "C / C++",
    "graphql": "GraphQL",
    "database-sql": "Database / SQL",
    "react-native": "Mobile (Cross-Platform: React Native / Expo)",
    "game": "Game (Unity / Unreal)",
    "nodejs-typescript": "Node.js / TypeScript",
    "jvm": "Java / Kotlin (JVM)",
    "backend": "Backend (Server / API / Microservice)",
}

BACKEND_HINT_RE = re.compile(
    r"(^|/)(api|server|backend|svc|service|services|handlers?|controllers?|routes?|"
    r"middleware|rpc|grpc)(/|$)",
    re.IGNORECASE,
)

PACKAGE_ROOT_RE = re.compile(
    r"^(packages?|apps?|services?|modules?|libs?|workspaces?)/([^/]+)/",
    re.IGNORECASE,
)

LARGE_FILE_THRESHOLD = 50
LARGE_LINE_THRESHOLD = 2000


def normalize_git_output(text: str) -> str:
    """Normalize Git stdout/stderr without destroying meaningful leading spaces.

    ``str.strip()`` on the whole blob would turn ``" M file"`` into ``"M file"``,
    which breaks ``git status --short`` XY status codes. Only drop completely blank
    lines (after per-line rstrip of trailing whitespace / CR).
    """
    lines = [line.rstrip("\r\n") for line in text.splitlines()]
    # Keep internal blank lines out; preserve leading spaces on content lines.
    return "\n".join(line for line in lines if line.strip() != "")


def run_git(args: list[str], cwd: str | None = None) -> tuple[int, str, str]:
    """Run a git command. Returns ``(returncode, stdout, stderr)``.

    Uses ``-c core.quotePath=false`` so non-ASCII filenames are not
    octal-escaped / quoted by git. stderr is kept **separate** from stdout
    so that git warnings (e.g. CRLF notices) are not mis-parsed as status
    entries.
    """
    proc = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    out = normalize_git_output(proc.stdout)
    err = normalize_git_output(proc.stderr)
    return proc.returncode, out, err


def _validate_ref(ref: str, name: str) -> str:
    """Validate a user-supplied git ref to prevent option injection.

    Rejects values starting with ``-`` (e.g. ``--exec=...``) that git would
    interpret as options rather than refs.
    """
    if not ref or ref.startswith("-"):
        raise ValueError(f"invalid {name}: {ref!r} (must not start with '-')")
    return ref


def parse_status(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        # status --short: two-char XY code, then space, then path
        if len(line) < 2:
            continue
        code = line[:2]
        path = line[3:] if len(line) > 3 else ""
        if " -> " in path:
            old, new = path.split(" -> ", 1)
            entries.append({"code": code, "path": new, "old_path": old})
        else:
            entries.append({"code": code, "path": path})
    return entries


def parse_name_status(text: str) -> list[dict[str, str]]:
    """Parse `git diff --name-status` / `git show --name-status` lines."""
    entries: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if not parts:
            continue
        code = parts[0].strip()
        # Rename/copy: R100\told\tnew
        if code.startswith(("R", "C")) and len(parts) >= 3:
            entries.append({"code": code[0], "path": parts[2], "old_path": parts[1]})
        elif len(parts) >= 2:
            entries.append({"code": code[0] if code else "M", "path": parts[1]})
    return entries


def _resolve_rename_path(path: str) -> str:
    """Resolve a ``=>`` rename in numstat path to the final path.

    Handles both styles:

    - Full rename: ``old/path => new/path`` → ``new/path``
    - Brace rename: ``prefix/{old => new}/suffix`` → ``prefix/new/suffix``
    """
    parts = path.split(" => ")
    if len(parts) != 2:
        # Fallback: take last segment and strip braces
        return parts[-1].replace("{", "").replace("}", "")
    left, right = parts
    # Brace rename: "prefix/{old" + "new}/suffix"
    # Detect by { in left and } in right.
    brace_idx = left.rfind("{")
    close_idx = right.find("}")
    if brace_idx != -1 and close_idx != -1:
        prefix = left[:brace_idx]
        new_name = right[:close_idx]
        suffix = right[close_idx + 1:]
        return f"{prefix}{new_name}{suffix}"
    # Full rename: take right side, strip any surrounding quotes
    return right.strip('"')


def _count_file_lines(root: str, path: str) -> tuple[int, bool]:
    """Count lines in a file for untracked-file stats.

    Returns ``(line_count, is_binary)``. If the file cannot be read,
    returns ``(0, False)``.
    """
    abs_path = Path(root) / path
    if not abs_path.exists() or not abs_path.is_file():
        return 0, False
    try:
        with open(abs_path, "rb") as f:
            content = f.read()
        # Detect binary: NUL byte in first 8 KB
        if b"\x00" in content[:8192]:
            return 0, True
        text = content.decode("utf-8", errors="replace")
        if not text:
            return 0, False
        count = text.count("\n")
        if not text.endswith("\n"):
            count += 1
        return count, False
    except (OSError, PermissionError):
        return 0, False


def count_numstat(text: str) -> tuple[int, int, list[dict[str, object]]]:
    """Parse numstat; return (added, deleted, per_file)."""
    added = 0
    deleted = 0
    per_file: list[dict[str, object]] = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        a_raw, d_raw, path = parts[0], parts[1], parts[2]
        if " => " in path:
            path = _resolve_rename_path(path)
        a = int(a_raw) if a_raw.isdigit() else 0
        d = int(d_raw) if d_raw.isdigit() else 0
        binary = not (a_raw.isdigit() and d_raw.isdigit())
        added += a
        deleted += d
        per_file.append(
            {
                "path": path,
                "added": a,
                "deleted": d,
                "binary": binary,
            }
        )
    return added, deleted, per_file


def classify_path(path: str) -> list[str]:
    tags: list[str] = []
    if GENERATED_RE.search(path) or LOCKFILE_RE.search(path):
        tags.append("generated_or_lock")
    if BINARY_RE.search(path):
        tags.append("binary")
    if DOCS_RE.search(path) and not TEST_RE.search(path):
        tags.append("docs")
    if TEST_RE.search(path):
        tags.append("test")
    if MIGRATION_RE.search(path):
        tags.append("migration")
    if CONFIG_RE.search(path):
        tags.append("config")
    if SECURITY_PATH_RE.search(path):
        tags.append("security_sensitive")
    if not tags:
        tags.append("production_code")
    return tags


def detect_stacks(paths: list[str]) -> list[dict[str, str]]:
    found: dict[str, int] = Counter()
    for path in paths:
        for pattern, stack_id in STACK_RULES:
            if pattern.search(path):
                found[stack_id] += 1
        if BACKEND_HINT_RE.search(path):
            found["backend"] += 1
    # Prefer more specific frontend/mobile over generic node when both match
    if found.get("frontend") and found.get("nodejs-typescript"):
        # keep both; agent can use both sections
        pass
    if found.get("android") and found.get("jvm"):
        del found["jvm"]
    result = []
    for stack_id, count in found.most_common():
        result.append(
            {
                "id": stack_id,
                "section": STACK_SECTION_TITLES.get(stack_id, stack_id),
                "file_count": str(count),
            }
        )
    return result


def detect_packages(paths: list[str]) -> list[str]:
    packages: set[str] = set()
    for path in paths:
        m = PACKAGE_ROOT_RE.match(path.replace("\\", "/"))
        if m:
            packages.add(f"{m.group(1)}/{m.group(2)}")
    return sorted(packages)


def infer_change_types(paths: list[str], entries: list[dict[str, str]]) -> list[str]:
    tag_sets = [set(classify_path(p)) for p in paths if p]
    if not tag_sets:
        return ["unknown"]

    all_tags = set().union(*tag_sets) if tag_sets else set()
    types: list[str] = []

    pure_docs = all_tags <= {"docs", "generated_or_lock"}
    pure_test = all_tags <= {"test", "docs", "generated_or_lock"}
    pure_config = all_tags <= {"config", "docs", "generated_or_lock"}

    if pure_docs and "docs" in all_tags:
        types.append("documentation")
    elif pure_test and "test" in all_tags:
        types.append("test_only")
    elif pure_config and "config" in all_tags:
        types.append("configuration")
    else:
        # Heuristics from paths/names
        joined = " ".join(paths).lower()
        codes = {e.get("code", "") for e in entries}
        if "migration" in all_tags:
            types.append("migration")
        if "security_sensitive" in all_tags:
            types.append("security_change")
        if any(k in joined for k in ("fix", "bug", "hotfix", "patch")):
            types.append("bug_fix")
        if any(k in joined for k in ("refactor", "rename", "cleanup", "chore")):
            types.append("refactor")
        if any(k in joined for k in ("perf", "optim", "performance")):
            types.append("performance")
        if any(
            k in joined
            for k in (
                "package.json",
                "cargo.toml",
                "go.mod",
                "pyproject.toml",
                "requirements",
                "podfile",
                "pubspec",
            )
        ):
            types.append("dependency_update")
        if "production_code" in all_tags or ("A" in "".join(codes) and "production_code" not in all_tags):
            if "feature" not in types and "bug_fix" not in types:
                types.append("feature_or_logic")
        if "config" in all_tags and "configuration" not in types:
            types.append("configuration")
        if "test" in all_tags and "test_only" not in types:
            types.append("includes_tests")
        if "docs" in all_tags and "documentation" not in types:
            types.append("includes_docs")

    if not types:
        types.append("mixed_or_unknown")
    return types


def top_level_groups(paths: list[str]) -> list[str]:
    groups: set[str] = set()
    for path in paths:
        parts = path.replace("\\", "/").split("/")
        if len(parts) >= 2:
            groups.add(parts[0] if parts[0] not in {"src", "lib", "app"} else "/".join(parts[:2]))
        elif parts:
            groups.add(parts[0])
    return sorted(groups)


def risk_matrix_reference() -> dict[str, object]:
    """Quantified severity × confidence weight table for agents."""
    # Points contribute to a raw score; level bands below.
    weights = {
        "Critical": {"Confirmed": 100, "Likely": 80, "Potential": 45},
        "High": {"Confirmed": 55, "Likely": 40, "Potential": 22},
        "Medium": {"Confirmed": 20, "Likely": 14, "Potential": 8},
        "Low": {"Confirmed": 4, "Likely": 3, "Potential": 1},
    }
    return {
        "weights": weights,
        "level_bands": {
            "Very High": ">= 80 OR any Critical+Confirmed/Likely",
            "High": "45-79 OR Critical+Potential OR High+Confirmed/Likely",
            "Medium": "15-44 OR any Medium+Confirmed/Likely OR 5+ Low",
            "Low": "0-14 with only Low/none (or only Medium+Potential with score < 15)",
        },
        "modifiers": [
            "If 3+ findings share one root cause, count the highest at full weight and each extra shared finding at 25% weight (one fix clears the cluster).",
            "If every finding is Potential, cap risk level at Medium.",
            "If highest is Medium+Potential only (no Confirmed/Likely Medium+), treat as Low unless score >= 15 from many findings.",
        ],
        "merge_decision": {
            "BLOCK MERGE": "Very High",
            "REQUEST CHANGES": "High, or any Critical, or High+Confirmed",
            "APPROVE WITH COMMENTS": "Medium, or High+Potential only",
            "APPROVE": "Low with no Critical/High",
        },
    }


def build_file_records(
    entries: list[dict[str, str]],
    numstat_files: list[dict[str, object]],
) -> list[dict[str, object]]:
    stats_by_path = {str(f["path"]): f for f in numstat_files}
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for entry in entries:
        path = entry.get("path") or ""
        if not path or path in seen:
            continue
        seen.add(path)
        st = stats_by_path.get(path, {})
        tags = classify_path(path)
        records.append(
            {
                "path": path,
                "status": entry.get("code", ""),
                "old_path": entry.get("old_path"),
                "added": st.get("added", 0),
                "deleted": st.get("deleted", 0),
                "binary": bool(st.get("binary")) or "binary" in tags,
                "tags": tags,
                "exclude_by_default": bool(
                    {"generated_or_lock", "binary"} & set(tags)
                ),
            }
        )
    # numstat-only paths (rare)
    for path, st in stats_by_path.items():
        if path in seen:
            continue
        tags = classify_path(path)
        records.append(
            {
                "path": path,
                "status": "M",
                "old_path": None,
                "added": st.get("added", 0),
                "deleted": st.get("deleted", 0),
                "binary": bool(st.get("binary")) or "binary" in tags,
                "tags": tags,
                "exclude_by_default": bool(
                    {"generated_or_lock", "binary"} & set(tags)
                ),
            }
        )
    return records


def snapshot_uncommitted(root: str) -> dict[str, object]:
    # Expand untracked directories to individual paths so new files are reviewable.
    _, status_text, _ = run_git(
        ["status", "--short", "--untracked-files=all"],
        cwd=root,
    )
    _, numstat, _ = run_git(["diff", "--numstat", "HEAD"], cwd=root)
    _, staged_numstat, _ = run_git(["diff", "--cached", "--numstat"], cwd=root)
    _, unstaged_numstat, _ = run_git(["diff", "--numstat"], cwd=root)
    _, stat, _ = run_git(["diff", "--stat", "HEAD"], cwd=root)
    _, cached_stat, _ = run_git(["diff", "--cached", "--stat"], cwd=root)

    entries = parse_status(status_text)
    added, deleted, per_file = count_numstat(numstat)
    s_added, s_deleted, _ = count_numstat(staged_numstat)
    u_added, u_deleted, _ = count_numstat(unstaged_numstat)
    # Untracked files do not appear in diff --numstat vs HEAD;
    # count actual lines so added_lines / large_diff are accurate.
    stats_paths = {str(f["path"]) for f in per_file}
    for entry in entries:
        path = entry.get("path") or ""
        code = entry.get("code", "")
        if path and path not in stats_paths and "?" in code:
            line_count, is_binary = _count_file_lines(root, path)
            per_file.append(
                {"path": path, "added": line_count, "deleted": 0, "binary": is_binary}
            )
            added += line_count
    files = build_file_records(entries, per_file)
    paths = [str(f["path"]) for f in files]

    return {
        "mode": "uncommitted",
        "status": status_text,
        "diff_stat": stat,
        "cached_diff_stat": cached_stat,
        "added_lines": added,
        "deleted_lines": deleted,
        "staged_added_lines": s_added,
        "staged_deleted_lines": s_deleted,
        "unstaged_added_lines": u_added,
        "unstaged_deleted_lines": u_deleted,
        "files": files,
        "paths": paths,
        "entries": entries,
        "has_changes": bool(paths),
        "empty_hint": (
            "No local changes were found. Ask whether to review: staged, "
            "latest commit (HEAD), a specific commit, branch diff, or specific files."
            if not paths
            else None
        ),
    }


def snapshot_staged(root: str) -> dict[str, object]:
    _, name_status, _ = run_git(["diff", "--cached", "--name-status"], cwd=root)
    _, numstat, _ = run_git(["diff", "--cached", "--numstat"], cwd=root)
    _, stat, _ = run_git(["diff", "--cached", "--stat"], cwd=root)
    entries = parse_name_status(name_status)
    added, deleted, per_file = count_numstat(numstat)
    files = build_file_records(entries, per_file)
    paths = [str(f["path"]) for f in files]
    return {
        "mode": "staged",
        "diff_stat": stat,
        "added_lines": added,
        "deleted_lines": deleted,
        "files": files,
        "paths": paths,
        "entries": entries,
        "has_changes": bool(paths),
        "empty_hint": "No staged changes were found." if not paths else None,
    }


def snapshot_commit(root: str, sha: str) -> dict[str, object]:
    _validate_ref(sha, "commit ref")
    rc, show_stat, err = run_git(["show", "--stat", "--format=fuller", "--no-patch", sha], cwd=root)
    if rc != 0:
        return {
            "mode": "commit",
            "ok": False,
            "error": f"invalid commit ref: {sha}: {err}",
            "has_changes": False,
            "paths": [],
            "files": [],
            "entries": [],
            "added_lines": 0,
            "deleted_lines": 0,
        }
    _, name_status, _ = run_git(["show", "--name-status", "--format=", sha], cwd=root)
    _, numstat, _ = run_git(["show", "--numstat", "--format=", sha], cwd=root)
    _, subject, _ = run_git(["log", "-1", "--format=%s", sha], cwd=root)
    entries = parse_name_status(name_status)
    added, deleted, per_file = count_numstat(numstat)
    files = build_file_records(entries, per_file)
    paths = [str(f["path"]) for f in files]
    return {
        "mode": "commit",
        "commit": sha,
        "commit_subject": subject,
        "commit_meta": show_stat,
        "added_lines": added,
        "deleted_lines": deleted,
        "files": files,
        "paths": paths,
        "entries": entries,
        "has_changes": bool(paths),
    }


def snapshot_branch_diff(root: str, base: str) -> dict[str, object]:
    _validate_ref(base, "base ref")
    range_spec = f"{base}...HEAD"
    rc, _, err = run_git(["rev-parse", "--verify", base], cwd=root)
    if rc != 0:
        return {
            "mode": "branch-diff",
            "ok": False,
            "error": f"invalid base ref: {base}: {err}",
            "base": base,
            "has_changes": False,
            "paths": [],
            "files": [],
            "entries": [],
            "added_lines": 0,
            "deleted_lines": 0,
        }
    _, name_status, _ = run_git(["diff", "--name-status", range_spec], cwd=root)
    _, numstat, _ = run_git(["diff", "--numstat", range_spec], cwd=root)
    _, stat, _ = run_git(["diff", "--stat", range_spec], cwd=root)
    _, ahead, _ = run_git(["rev-list", "--count", f"{base}..HEAD"], cwd=root)
    entries = parse_name_status(name_status)
    added, deleted, per_file = count_numstat(numstat)
    files = build_file_records(entries, per_file)
    paths = [str(f["path"]) for f in files]
    return {
        "mode": "branch-diff",
        "base": base,
        "range": range_spec,
        "commits_ahead": int(ahead) if ahead.isdigit() else ahead,
        "diff_stat": stat,
        "added_lines": added,
        "deleted_lines": deleted,
        "files": files,
        "paths": paths,
        "entries": entries,
        "has_changes": bool(paths),
        "empty_hint": f"No diff between {base} and HEAD." if not paths else None,
    }


def snapshot_files(root: str, file_paths: list[str]) -> dict[str, object]:
    files: list[dict[str, object]] = []
    paths: list[str] = []
    for raw in file_paths:
        p = raw.strip()
        if not p:
            continue
        paths.append(p)
        abs_path = Path(root) / p
        exists = abs_path.exists()
        tags = classify_path(p)
        size = abs_path.stat().st_size if exists and abs_path.is_file() else 0
        files.append(
            {
                "path": p,
                "status": "F",
                "old_path": None,
                "added": 0,
                "deleted": 0,
                "binary": "binary" in tags,
                "tags": tags,
                "exists": exists,
                "size_bytes": size,
                "exclude_by_default": bool({"generated_or_lock", "binary"} & set(tags)),
            }
        )
    return {
        "mode": "file",
        "files": files,
        "paths": paths,
        "entries": [{"code": "F", "path": p} for p in paths],
        "added_lines": 0,
        "deleted_lines": 0,
        "has_changes": bool(paths),
        "note": "Full-file review mode: read each file completely; line stats are not diff-based.",
    }


def finalize(core: dict[str, object], root: str, branch: str, detached: bool) -> dict[str, object]:
    paths = [str(p) for p in core.get("paths", [])]  # type: ignore[arg-type]
    entries = list(core.get("entries", []))  # type: ignore[arg-type]
    files = list(core.get("files", []))  # type: ignore[arg-type]
    added = int(core.get("added_lines", 0) or 0)
    deleted = int(core.get("deleted_lines", 0) or 0)
    total_lines = added + deleted
    changed_files = len(paths)

    reviewable = [f for f in files if not f.get("exclude_by_default")]
    excluded = [f for f in files if f.get("exclude_by_default")]
    prioritized = [
        f
        for f in reviewable
        if "security_sensitive" in (f.get("tags") or [])
        or "production_code" in (f.get("tags") or [])
        or "migration" in (f.get("tags") or [])
    ]

    stacks = detect_stacks(paths)
    packages = detect_packages(paths)
    change_types = infer_change_types(paths, entries)  # type: ignore[arg-type]
    groups = top_level_groups(paths)

    warnings: list[str] = []
    large_diff = changed_files > LARGE_FILE_THRESHOLD or total_lines > LARGE_LINE_THRESHOLD
    if large_diff:
        warnings.append(
            f"large diff ({changed_files} files, {total_lines} lines); "
            "review critical modules first in batches"
        )
    if len(packages) > 1:
        warnings.append("multi-package monorepo change; trace cross-package contracts")
    # Mixed change heuristic: 3+ unrelated top-level tags among docs/test/config/prod
    tag_counter: Counter[str] = Counter()
    for f in files:
        for t in f.get("tags") or []:
            if t in {"docs", "test", "config", "production_code", "migration"}:
                tag_counter[str(t)] += 1
    substantive = [t for t, c in tag_counter.items() if c > 0]
    mixed = len(substantive) >= 3 and "production_code" in substantive
    if mixed:
        warnings.append(
            "possible mixed unrelated changes; group findings and consider split commits"
        )
    if excluded:
        warnings.append(
            f"{len(excluded)} generated/lock/binary path(s) excluded by default"
        )

    must_read_sections = [s["section"] for s in stacks]

    result = {
        "ok": core.get("ok", True) if "ok" in core else True,
        "repo_root": root,
        "branch": branch,
        "detached_head": detached,
        "large_diff": large_diff,
        "large_diff_thresholds": {
            "files": LARGE_FILE_THRESHOLD,
            "lines": LARGE_LINE_THRESHOLD,
        },
        "changed_files": changed_files,
        "reviewable_files": len(reviewable),
        "excluded_files": len(excluded),
        "added_lines": added,
        "deleted_lines": deleted,
        "total_changed_lines": total_lines,
        "paths": paths,
        "change_types": change_types,
        "detected_stacks": stacks,
        "must_read_tech_stack_sections": must_read_sections,
        "tech_stacks_path": "references/tech-stacks.md",
        "package_roots": packages,
        "top_level_groups": groups,
        "mixed_changes_suspected": mixed,
        "security_sensitive_paths": [
            f["path"] for f in files if "security_sensitive" in (f.get("tags") or [])
        ],
        "prioritized_paths": [f["path"] for f in prioritized],
        "excluded_paths": [f["path"] for f in excluded],
        "warnings": warnings,
        "risk_matrix": risk_matrix_reference(),
        "files": files,
    }
    # Merge core mode-specific fields (without duplicating heavy raw entries)
    for key in (
        "mode",
        "status",
        "diff_stat",
        "cached_diff_stat",
        "staged_added_lines",
        "staged_deleted_lines",
        "unstaged_added_lines",
        "unstaged_deleted_lines",
        "has_changes",
        "empty_hint",
        "commit",
        "commit_subject",
        "commit_meta",
        "base",
        "range",
        "commits_ahead",
        "note",
        "error",
    ):
        if key in core:
            result[key] = core[key]
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="deep-review read-only snapshot")
    p.add_argument(
        "--mode",
        choices=["uncommitted", "staged", "commit", "branch-diff", "file"],
        default="uncommitted",
        help="Review target mode (default: uncommitted)",
    )
    p.add_argument("--commit", default="", help="Commit SHA for --mode commit")
    p.add_argument("--base", default="main", help="Base ref for --mode branch-diff")
    p.add_argument(
        "--file",
        action="append",
        default=[],
        dest="files",
        help="File path for --mode file (repeatable)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rc, root, _ = run_git(["rev-parse", "--show-toplevel"])
    if rc != 0:
        print(
            json.dumps(
                {"ok": False, "error": "not a git repository"},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    os.chdir(root)
    branch_rc, branch, _ = run_git(["branch", "--show-current"])
    detached = branch_rc != 0 or not branch

    if args.mode == "uncommitted":
        core = snapshot_uncommitted(root)
    elif args.mode == "staged":
        core = snapshot_staged(root)
    elif args.mode == "commit":
        sha = args.commit or "HEAD"
        core = snapshot_commit(root, sha)
    elif args.mode == "branch-diff":
        core = snapshot_branch_diff(root, args.base)
    else:
        if not args.files:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": "--mode file requires one or more --file paths",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1
        core = snapshot_files(root, args.files)

    if core.get("ok") is False:
        print(json.dumps(finalize(core, root, branch, detached), ensure_ascii=False, indent=2))
        return 1

    snap = finalize(core, root, branch, detached)
    print(json.dumps(snap, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
