#!/usr/bin/env python3
"""Print a read-only Git snapshot for the git-auto-commit skill."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


SECRET_RE = re.compile(
    r"(^|[._\-/])(env|credential|credentials|token|password|passwd|secret|api[_-]?key|private[_-]?key)([._\-/]|$)|\.(pem|key|p12|pfx)$",
    re.IGNORECASE,
)

GENERATED_RE = re.compile(
    r"(^|/)(node_modules|build|dist|coverage|\.dart_tool|Pods|DerivedData|\.cache|target)(/|$)|"
    r"\.(lockb|png|jpg|jpeg|gif|webp|zip|gz|tar|tgz|7z|dmg|xcarchive)$",
    re.IGNORECASE,
)

MANIFESTS = [
    "pubspec.yaml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "build.gradle",
    "settings.gradle",
    "Package.swift",
    "pyproject.toml",
]


def run_git(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    output = proc.stdout.strip()
    if proc.stderr.strip():
        output = f"{output}\n{proc.stderr.strip()}".strip()
    return proc.returncode, output


def parse_status(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line:
            continue
        code = line[:2]
        path = line[3:] if len(line) > 3 else ""
        if " -> " in path:
            old, new = path.split(" -> ", 1)
            entries.append({"code": code, "path": new, "old_path": old})
        else:
            entries.append({"code": code, "path": path})
    return entries


def main() -> int:
    rc, root = run_git(["rev-parse", "--show-toplevel"])
    if rc != 0:
        print(json.dumps({"ok": False, "error": "not a git repository"}, ensure_ascii=False, indent=2))
        return 1

    os.chdir(root)
    _, branch = run_git(["branch", "--show-current"])
    _, status_text = run_git(["status", "--short"])
    _, stat = run_git(["diff", "--stat"])
    _, cached_stat = run_git(["diff", "--cached", "--stat"])
    _, recent_commits = run_git(["log", "--oneline", "-20"])
    _, numstat = run_git(["diff", "--numstat", "HEAD"])

    status_entries = parse_status(status_text)
    paths = [entry["path"] for entry in status_entries if entry.get("path")]
    secret_paths = [path for path in paths if SECRET_RE.search(path)]
    generated_paths = [path for path in paths if GENERATED_RE.search(path)]
    manifests = [name for name in MANIFESTS if Path(name).exists()]

    changed_files = len(paths)
    added = 0
    deleted = 0
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        if parts[0].isdigit():
            added += int(parts[0])
        if parts[1].isdigit():
            deleted += int(parts[1])

    warnings: list[str] = []
    if secret_paths:
        warnings.append("secret-like paths present")
    if changed_files > 50 or added + deleted > 1000:
        warnings.append("large diff; consider splitting")
    if generated_paths:
        warnings.append("generated/cache/binary-looking paths present")

    snapshot = {
        "ok": True,
        "repo_root": root,
        "branch": branch,
        "project_manifests": manifests,
        "changed_files": changed_files,
        "added_lines": added,
        "deleted_lines": deleted,
        "warnings": warnings,
        "secret_like_paths": secret_paths,
        "generated_like_paths": generated_paths,
        "status": status_text,
        "diff_stat": stat,
        "cached_diff_stat": cached_stat,
        "recent_commits": recent_commits,
    }
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
