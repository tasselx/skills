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
from concurrent.futures import ThreadPoolExecutor
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
DEFAULT_DIFF_BYTE_CAP = 200_000
# Instant path: snapshot-only review (no extra agent file reads).
INSTANT_MAX_FILES = 5
INSTANT_MAX_LINES = 150
INSTANT_FILE_BYTE_CAP = 48_000
INSTANT_TOTAL_EMBED_CAP = 160_000
STANDARD_MAX_FILES = 20
STANDARD_MAX_LINES = 800
# Default run mode: prefer oneshot unless user/env forces deep.
DEFAULT_FORCE_PROFILE = (os.environ.get("DEEP_REVIEW_PROFILE") or "").strip().lower()


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


def run_git_many(
    jobs: list[tuple[str, list[str]]],
    cwd: str | None = None,
) -> dict[str, tuple[int, str, str]]:
    """Run independent git commands in parallel. ``jobs`` is ``(key, args)``."""
    if not jobs:
        return {}
    if len(jobs) == 1:
        key, args = jobs[0]
        return {key: run_git(args, cwd=cwd)}

    results: dict[str, tuple[int, str, str]] = {}

    def _one(item: tuple[str, list[str]]) -> tuple[str, tuple[int, str, str]]:
        key, args = item
        return key, run_git(args, cwd=cwd)

    with ThreadPoolExecutor(max_workers=min(8, len(jobs))) as pool:
        for key, value in pool.map(_one, jobs):
            results[key] = value
    return results


def extract_stack_excerpts(
    skill_dir: str | None,
    section_titles: list[str],
) -> dict[str, object]:
    """Pull only matched headings from tech-stacks.md (avoid full-file reads)."""
    if not section_titles:
        return {"sections": {}, "path": None, "missing": []}

    tech_path = None
    if skill_dir:
        candidate = Path(skill_dir) / "references" / "tech-stacks.md"
        if candidate.is_file():
            tech_path = candidate
    if tech_path is None:
        # Script lives in <skill>/scripts/review_snapshot.py
        here = Path(__file__).resolve().parent.parent / "references" / "tech-stacks.md"
        if here.is_file():
            tech_path = here

    if tech_path is None or not tech_path.is_file():
        return {
            "sections": {},
            "path": None,
            "missing": list(section_titles),
            "error": "tech-stacks.md not found",
        }

    text = tech_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    # Map heading text -> (start_line_idx, end_line_idx exclusive)
    headings: list[tuple[str, int]] = []
    for idx, line in enumerate(lines):
        if line.startswith("## "):
            headings.append((line[3:].strip(), idx))

    def find_heading(title: str) -> int | None:
        title_l = title.lower()
        for h, idx in headings:
            if h.lower() == title_l or title_l in h.lower() or h.lower() in title_l:
                return idx
        return None

    sections: dict[str, str] = {}
    missing: list[str] = []
    for title in section_titles:
        start = find_heading(title)
        if start is None:
            missing.append(title)
            continue
        # end at next ## or EOF
        end = len(lines)
        for h, idx in headings:
            if idx > start:
                end = idx
                break
        body = "\n".join(lines[start:end]).strip()
        sections[title] = body

    return {
        "sections": sections,
        "path": str(tech_path),
        "missing": missing,
    }


def collect_diff_patch(
    root: str,
    mode: str,
    *,
    commit: str = "",
    base: str = "main",
    byte_cap: int = DEFAULT_DIFF_BYTE_CAP,
) -> dict[str, object]:
    """Fetch the mode-specific unified diff once, capped for agent context."""
    if mode == "uncommitted":
        # Combined working tree vs HEAD (staged + unstaged), matching status.
        args = ["diff", "HEAD", "--"]
    elif mode == "staged":
        args = ["diff", "--cached", "--"]
    elif mode == "commit":
        _validate_ref(commit or "HEAD", "commit ref")
        args = ["show", "--format=", "--patch", commit or "HEAD", "--"]
    elif mode == "branch-diff":
        _validate_ref(base, "base ref")
        args = ["diff", f"{base}...HEAD", "--"]
    else:
        return {
            "included": False,
            "reason": "file mode has no diff; read full file contents",
        }

    rc, out, err = run_git(args, cwd=root)
    if rc != 0:
        return {"included": False, "error": err or f"git exited {rc}"}

    raw = out
    encoded = raw.encode("utf-8", errors="replace")
    truncated = len(encoded) > byte_cap
    if truncated:
        # Truncate on a line boundary when possible
        cut = encoded[:byte_cap].decode("utf-8", errors="ignore")
        if "\n" in cut:
            cut = cut.rsplit("\n", 1)[0] + "\n"
        raw = cut

    return {
        "included": True,
        "truncated": truncated,
        "byte_cap": byte_cap,
        "bytes": len(encoded),
        "patch": raw,
    }


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
    # Parallelize independent git metadata calls (major latency win on cold FS).
    jobs = run_git_many(
        [
            ("status", ["status", "--short", "--untracked-files=all"]),
            ("numstat", ["diff", "--numstat", "HEAD"]),
            ("staged_numstat", ["diff", "--cached", "--numstat"]),
            ("unstaged_numstat", ["diff", "--numstat"]),
            ("stat", ["diff", "--stat", "HEAD"]),
            ("cached_stat", ["diff", "--cached", "--stat"]),
        ],
        cwd=root,
    )
    status_text = jobs["status"][1]
    numstat = jobs["numstat"][1]
    staged_numstat = jobs["staged_numstat"][1]
    unstaged_numstat = jobs["unstaged_numstat"][1]
    stat = jobs["stat"][1]
    cached_stat = jobs["cached_stat"][1]

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
    jobs = run_git_many(
        [
            ("name_status", ["diff", "--cached", "--name-status"]),
            ("numstat", ["diff", "--cached", "--numstat"]),
            ("stat", ["diff", "--cached", "--stat"]),
        ],
        cwd=root,
    )
    name_status = jobs["name_status"][1]
    numstat = jobs["numstat"][1]
    stat = jobs["stat"][1]
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
    jobs = run_git_many(
        [
            ("name_status", ["show", "--name-status", "--format=", sha]),
            ("numstat", ["show", "--numstat", "--format=", sha]),
            ("subject", ["log", "-1", "--format=%s", sha]),
        ],
        cwd=root,
    )
    name_status = jobs["name_status"][1]
    numstat = jobs["numstat"][1]
    subject = jobs["subject"][1]
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
    jobs = run_git_many(
        [
            ("name_status", ["diff", "--name-status", range_spec]),
            ("numstat", ["diff", "--numstat", range_spec]),
            ("stat", ["diff", "--stat", range_spec]),
            ("ahead", ["rev-list", "--count", f"{base}..HEAD"]),
        ],
        cwd=root,
    )
    name_status = jobs["name_status"][1]
    numstat = jobs["numstat"][1]
    stat = jobs["stat"][1]
    ahead = jobs["ahead"][1]
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


def is_chinese_locale_tag(value: str) -> bool:
    """True if a locale/language tag denotes Chinese."""
    s = (value or "").strip().replace("-", "_").lower()
    if not s or s in {"c", "posix"}:
        return False
    # zh, zh_cn, zh_hans_cn, zh.utf-8, chinese
    primary = s.split(".")[0].split("@")[0]
    if primary == "zh" or primary.startswith("zh_"):
        return True
    if "chinese" in s or primary in {"chn", "cn"}:
        return True
    return False


def _macos_language_signals() -> list[str]:
    """Read macOS global AppleLocale / AppleLanguages (user-facing system language)."""
    if sys.platform != "darwin":
        return []
    signals: list[str] = []
    for args in (
        ["defaults", "read", "-g", "AppleLocale"],
        ["defaults", "read", "-g", "AppleLanguages"],
    ):
        try:
            proc = subprocess.run(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=2,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if proc.returncode != 0 or not proc.stdout.strip():
            continue
        text = proc.stdout.strip()
        # AppleLanguages is a plist-like list: ( "zh-Hans-CN", "en-CN", ... )
        for raw in re.findall(r'"([^"]+)"', text):
            signals.append(raw)
        if not signals and not text.startswith("("):
            signals.append(text.splitlines()[0].strip())
    return signals


def detect_output_language() -> dict[str, object]:
    """Decide review prose language. Prefer real UI language over shell LANG.

    Many agent/CLI environments export ``LANG=en_US.UTF-8`` while the user's
    OS UI is Chinese (especially macOS). Agents must follow ``language`` here.
    """
    signals: dict[str, object] = {}

    # 1) Explicit override for automation
    for key in ("DEEP_REVIEW_LANG", "REVIEW_OUTPUT_LANG", "OUTPUT_LANG"):
        raw = (os.environ.get(key) or "").strip()
        if not raw:
            continue
        signals[key] = raw
        low = raw.lower().replace("-", "_")
        if low in {"zh", "zh_cn", "zh_tw", "chinese", "cn", "中文"}:
            return {
                "language": "zh",
                "source": key,
                "signals": signals,
            }
        if low in {"en", "en_us", "en_gb", "english"}:
            return {
                "language": "en",
                "source": key,
                "signals": signals,
            }

    # 2) POSIX locale env — only win when they clearly say Chinese
    env_keys = (
        "LC_ALL",
        "LC_MESSAGES",
        "LANG",
        "LANGUAGE",
    )
    env_values = []
    for key in env_keys:
        val = (os.environ.get(key) or "").strip()
        if val:
            signals[key] = val
            env_values.append(val)
            # LANGUAGE can be colon-separated: zh_CN:en_US
            for part in re.split(r"[:;,\s]+", val):
                if is_chinese_locale_tag(part):
                    return {
                        "language": "zh",
                        "source": key,
                        "signals": signals,
                    }

    # 3) macOS UI language (critical: often Chinese while LANG stays en_US)
    mac_signals = _macos_language_signals()
    if mac_signals:
        signals["macos_languages"] = mac_signals
        # Prefer first language in AppleLanguages order
        for tag in mac_signals:
            if is_chinese_locale_tag(tag):
                return {
                    "language": "zh",
                    "source": "macos_apple_languages",
                    "signals": signals,
                }

    # 4) Common Chinese user markers in shell/env (weak)
    for key in ("TERMINAL_LANGUAGE", "USER_LANG", "UI_LANG"):
        val = (os.environ.get(key) or "").strip()
        if val:
            signals[key] = val
            if is_chinese_locale_tag(val):
                return {
                    "language": "zh",
                    "source": key,
                    "signals": signals,
                }

    return {
        "language": "en",
        "source": "default",
        "signals": signals,
    }


def embed_workspace_files(
    root: str,
    paths: list[str],
    *,
    per_file_cap: int = INSTANT_FILE_BYTE_CAP,
    total_cap: int = INSTANT_TOTAL_EMBED_CAP,
) -> dict[str, object]:
    """Embed small text file contents so the agent needs no extra Read calls."""
    embedded: dict[str, str] = {}
    skipped: list[dict[str, object]] = []
    total = 0
    for path in paths:
        if not path or path in embedded:
            continue
        abs_path = Path(root) / path
        if not abs_path.is_file():
            skipped.append({"path": path, "reason": "missing"})
            continue
        try:
            raw = abs_path.read_bytes()
        except OSError as exc:
            skipped.append({"path": path, "reason": str(exc)})
            continue
        if b"\x00" in raw[:8192]:
            skipped.append({"path": path, "reason": "binary"})
            continue
        if len(raw) > per_file_cap:
            skipped.append(
                {"path": path, "reason": "per_file_cap", "bytes": len(raw)}
            )
            continue
        if total + len(raw) > total_cap:
            skipped.append(
                {"path": path, "reason": "total_cap", "bytes": len(raw)}
            )
            continue
        text = raw.decode("utf-8", errors="replace")
        embedded[path] = text
        total += len(raw)
    return {
        "files": embedded,
        "embedded_count": len(embedded),
        "embedded_bytes": total,
        "skipped": skipped,
        "complete": len(skipped) == 0,
    }


def classify_review_profile(
    *,
    reviewable_count: int,
    total_lines: int,
    large_diff: bool,
    security_paths: list[object],
    has_migration: bool,
    package_count: int,
    change_types: list[str],
    force_profile: str = "",
) -> str:
    """Return instant | standard | deep.

    Default bias: oneshot ``instant`` for anything that is not an everyday-large
    or security-sensitive change. ``standard`` is kept only as a soft label for
    slightly larger diffs but still uses a zero extra-tool budget unless deep.
    """
    force = (force_profile or DEFAULT_FORCE_PROFILE or "").strip().lower()
    if force in {"deep", "full", "thorough"}:
        return "deep"
    if force in {"instant", "fast", "oneshot"}:
        return "instant"
    if force in {"standard", "normal"}:
        return "standard"

    # Auto: only truly heavy/sensitive changes leave the oneshot path.
    if large_diff or package_count > 1:
        return "deep"
    if security_paths or has_migration:
        return "deep"
    risky_types = {
        "security_change",
        "migration",
        "dependency_update",
    }
    if any(t in risky_types for t in change_types):
        return "deep"

    # Expanded oneshot band (was: tiny=instant, medium=standard with 1 more batch).
    # Agents ignore "1 more batch" and wander for minutes; keep them at 0 tools.
    if (
        reviewable_count <= STANDARD_MAX_FILES
        and total_lines <= STANDARD_MAX_LINES
    ):
        return "instant"
    return "deep"


def finalize(
    core: dict[str, object],
    root: str,
    branch: str,
    detached: bool,
    *,
    include_risk_matrix: bool = False,
    force_profile: str = "",
) -> dict[str, object]:
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

    security_paths = [
        f["path"] for f in files if "security_sensitive" in (f.get("tags") or [])
    ]
    has_migration = any("migration" in (f.get("tags") or []) for f in files)

    full_file_read_paths: list[str] = []
    patch_likely_enough: list[str] = []
    for f in prioritized:
        path = str(f.get("path") or "")
        a = int(f.get("added") or 0)
        d = int(f.get("deleted") or 0)
        tags = set(f.get("tags") or [])
        status = str(f.get("status") or "")
        is_new = status.startswith("A") or "?" in status or status == "F"
        needs_full = (
            is_new
            or "security_sensitive" in tags
            or "migration" in tags
            or (a + d) > 80
            or a + d == 0
        )
        if needs_full:
            full_file_read_paths.append(path)
        else:
            patch_likely_enough.append(path)

    profile = classify_review_profile(
        reviewable_count=len(reviewable),
        total_lines=total_lines,
        large_diff=large_diff,
        security_paths=security_paths,
        has_migration=has_migration,
        package_count=len(packages),
        change_types=change_types,
        force_profile=force_profile,
    )

    # Embed aggressively so agents never need Read tools on default path.
    embed_candidates: list[str] = []
    if profile in {"instant", "standard"}:
        embed_candidates = [str(f["path"]) for f in reviewable if f.get("path")]
    elif profile == "deep":
        embed_candidates = list(full_file_read_paths)[:12]

    file_contents: dict[str, object] = {
        "files": {},
        "embedded_count": 0,
        "embedded_bytes": 0,
        "skipped": [],
        "complete": True,
    }
    if embed_candidates:
        file_contents = embed_workspace_files(root, embed_candidates)
        embedded_set = set((file_contents.get("files") or {}).keys())  # type: ignore[union-attr]
        full_file_read_paths = [
            p for p in full_file_read_paths if p not in embedded_set
        ]
        if profile in {"instant", "standard"}:
            if file_contents.get("complete"):
                full_file_read_paths = []
            patch_likely_enough = [
                str(f["path"])
                for f in reviewable
                if f.get("path") and str(f["path"]) not in embedded_set
            ]

    # Instant AND standard: zero extra tools (standard label only for size band).
    if profile in {"instant", "standard"}:
        agent_hints = {
            "review_profile": profile,
            "max_tool_batches_after_snapshot": 0,
            "tool_calls_remaining": 0,
            "forbid_extra_reads": True,
            "forbid_grep": True,
            "forbid_tests": True,
            "forbid_task_subagent": True,
            "emit_mode": "oneshot",
            "skip_git_status_repeat": True,
            "prefer_embedded_diff": True,
            "prefer_stack_excerpts": True,
            "use_file_contents": True,
            "do_not_reload_skill_md": True,
            "do_not_load_review_depth": True,
            "speed_contract": (
                "STOP. tool_calls_remaining=0. Write the FULL review NOW from "
                "diff_patch + file_contents + stack_excerpts. Calling Read/Grep/"
                "Glob/Task/Bash again is a protocol violation."
            ),
        }
    else:
        agent_hints = {
            "review_profile": "deep",
            "max_tool_batches_after_snapshot": 3,
            "tool_calls_remaining": 3,
            "forbid_extra_reads": False,
            "forbid_grep": False,
            "forbid_tests": False,
            "forbid_task_subagent": True,
            "emit_mode": "stream",
            "skip_git_status_repeat": True,
            "prefer_embedded_diff": True,
            "prefer_stack_excerpts": True,
            "parallel_file_reads": True,
            "do_not_reload_skill_md": True,
            "do_not_load_review_depth": False,
            "speed_contract": (
                "Deep profile: at most 3 tool batches after snapshot. "
                "No Task/explore subagent. Stream findings; then Summary."
            ),
        }

    result = {
        "ok": core.get("ok", True) if "ok" in core else True,
        "repo_root": root,
        "branch": branch,
        "detached_head": detached,
        "review_profile": profile,
        "tool_calls_remaining": int(agent_hints.get("tool_calls_remaining") or 0),
        "AGENT_INSTRUCTION": (
            "TOOL BUDGET EXHAUSTED — write the complete code review now. "
            "Do not call Read, Grep, Glob, Task, or Bash again."
            if profile in {"instant", "standard"}
            else "Deep review: ≤3 more tool batches, then write findings + summary."
        ),
        "large_diff": large_diff,
        "large_diff_thresholds": {
            "files": LARGE_FILE_THRESHOLD,
            "lines": LARGE_LINE_THRESHOLD,
        },
        "profile_thresholds": {
            "instant_max_files": INSTANT_MAX_FILES,
            "instant_max_lines": INSTANT_MAX_LINES,
            "standard_max_files": STANDARD_MAX_FILES,
            "standard_max_lines": STANDARD_MAX_LINES,
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
        "security_sensitive_paths": security_paths,
        "prioritized_paths": [f["path"] for f in prioritized],
        "excluded_paths": [f["path"] for f in excluded],
        "full_file_read_paths": full_file_read_paths,
        "patch_likely_enough_paths": patch_likely_enough,
        "file_contents": file_contents,
        "warnings": warnings,
        "locale_env": (
            os.environ.get("LC_ALL")
            or os.environ.get("LC_MESSAGES")
            or os.environ.get("LANG")
            or ""
        ),
        "agent_hints": agent_hints,
        "files": files,
    }
    lang_info = detect_output_language()
    result["output_language"] = lang_info["language"]
    result["output_language_source"] = lang_info["source"]
    result["output_language_signals"] = lang_info["signals"]
    # Hard requirement string for agents that ignore prose rules.
    if lang_info["language"] == "zh":
        result["output_language_rule"] = (
            "REQUIRED: Write ALL review prose in Chinese (简体中文). "
            "Keep severity/confidence/category/decision tokens and code/paths in English. "
            "Do not write the report in English."
        )
        agent_hints["output_language"] = "zh"
        agent_hints["must_write_chinese"] = True
    else:
        result["output_language_rule"] = (
            "REQUIRED: Write ALL review prose in English. "
            "Do not switch to another language unless the user explicitly asked."
        )
        agent_hints["output_language"] = "en"
        agent_hints["must_write_chinese"] = False
    result["agent_hints"] = agent_hints
    if include_risk_matrix:
        result["risk_matrix"] = risk_matrix_reference()
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
        "diff_patch",
        "stack_excerpts",
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
    p.add_argument(
        "--with-diff",
        action="store_true",
        default=True,
        help="Embed unified diff patch (default: on). Avoids a second agent git diff.",
    )
    p.add_argument(
        "--no-diff",
        action="store_true",
        help="Do not embed unified diff patch",
    )
    p.add_argument(
        "--diff-byte-cap",
        type=int,
        default=DEFAULT_DIFF_BYTE_CAP,
        help=f"Max UTF-8 bytes of embedded patch (default: {DEFAULT_DIFF_BYTE_CAP})",
    )
    p.add_argument(
        "--stack-excerpts",
        action="store_true",
        default=True,
        help="Embed only detected tech-stack sections (default: on)",
    )
    p.add_argument(
        "--no-stack-excerpts",
        action="store_true",
        help="Do not embed tech-stack excerpts",
    )
    p.add_argument(
        "--skill-dir",
        default="",
        help="Skill root for resolving references/tech-stacks.md",
    )
    p.add_argument(
        "--profile",
        choices=["auto", "instant", "standard", "deep"],
        default="auto",
        help="Force review profile (default: auto). Prefer instant for speed.",
    )
    p.add_argument(
        "--risk-matrix",
        action="store_true",
        help="Include full risk_matrix JSON (omit by default; weights live in SKILL.md)",
    )
    p.add_argument(
        "--compact",
        action="store_true",
        help="Emit minified JSON (fewer tokens)",
    )
    p.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON (default)",
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

    want_diff = args.with_diff and not args.no_diff
    want_stacks = args.stack_excerpts and not args.no_stack_excerpts
    skill_dir = args.skill_dir.strip() or str(Path(__file__).resolve().parent.parent)

    if core.get("ok") is not False and core.get("has_changes") and want_diff:
        core["diff_patch"] = collect_diff_patch(
            root,
            str(core.get("mode") or args.mode),
            commit=str(core.get("commit") or args.commit or "HEAD"),
            base=str(core.get("base") or args.base or "main"),
            byte_cap=max(10_000, int(args.diff_byte_cap)),
        )

    force_profile = "" if args.profile == "auto" else args.profile

    # finalize first to know stacks, then excerpts
    if core.get("ok") is False:
        snap = finalize(
            core,
            root,
            branch,
            detached,
            include_risk_matrix=args.risk_matrix,
            force_profile=force_profile,
        )
        indent = None if args.compact else 2
        _emit_snapshot(snap, indent=indent)
        return 1

    snap = finalize(
        core,
        root,
        branch,
        detached,
        include_risk_matrix=args.risk_matrix,
        force_profile=force_profile,
    )

    if want_stacks and snap.get("must_read_tech_stack_sections"):
        excerpts = extract_stack_excerpts(
            skill_dir,
            list(snap.get("must_read_tech_stack_sections") or []),  # type: ignore[arg-type]
        )
        snap["stack_excerpts"] = excerpts
        if excerpts.get("sections"):
            missing = excerpts.get("missing") or []
            snap["stack_excerpts_complete"] = not missing
        else:
            snap["stack_excerpts_complete"] = False
    else:
        snap["stack_excerpts"] = {"sections": {}, "path": None, "missing": []}
        snap["stack_excerpts_complete"] = not bool(
            snap.get("must_read_tech_stack_sections")
        )

    indent = None if args.compact else 2
    _emit_snapshot(snap, indent=indent)
    return 0


def _emit_snapshot(snap: dict[str, object], *, indent: int | None) -> None:
    """Print JSON to stdout; scream tool-budget on stderr for logs/humans."""
    profile = snap.get("review_profile")
    remaining = snap.get("tool_calls_remaining", "?")
    lang = snap.get("output_language", "?")
    print(
        f"[deep-review] profile={profile} tool_calls_remaining={remaining} "
        f"lang={lang} → WRITE REVIEW NOW (no more tools)"
        if profile in {"instant", "standard"}
        else f"[deep-review] profile={profile} tool_calls_remaining={remaining} lang={lang}",
        file=sys.stderr,
    )
    print(json.dumps(snap, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    sys.exit(main())
