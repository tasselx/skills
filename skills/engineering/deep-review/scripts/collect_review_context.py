#!/usr/bin/env python3
"""Print a read-only review-context snapshot for the deep-review skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


SECRET_RE = re.compile(
    r"(^|[._\-/])(env|envrc|credential|credentials|token|passwords?|passwd|secret"
    r"|api[_-]?key|private[_-]?key|netrc|htpasswd|htaccess|npmrc|pypirc"
    r")([._\-/]|$)"
    r"|(^|/)id_(rsa|dsa|ecdsa|ed25519)(\.(?!pub)[^/]*)?$"
    r"|\.(pem|key|p12|pfx|keystore|jks|kdbx|ovpn)$",
    re.IGNORECASE,
)

GENERATED_RE = re.compile(
    r"(^|/)(node_modules|build|dist|coverage|\.dart_tool|Pods|DerivedData|\.cache|target"
    r"|__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|\.venv|venv"
    r")(/|$)|"
    r"\.(lockb|png|jpg|jpeg|gif|webp|zip|gz|tar|tgz|7z|dmg|xcarchive|pyc|pyo)$",
    re.IGNORECASE,
)

CONFLICT_CODES = {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}

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


def count_numstat(text: str) -> tuple[int, int]:
    """Parse ``git diff --numstat`` output; return (added, deleted) line counts."""
    added = 0
    deleted = 0
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        if parts[0].isdigit():
            added += int(parts[0])
        if parts[1].isdigit():
            deleted += int(parts[1])
    return added, deleted


def changed_file_list(text: str) -> list[str]:
    """Parse ``git diff --name-only`` output; return list of file paths."""
    files = []
    for line in text.splitlines():
        if line.strip():
            files.append(line.strip())
    return files


def detect_languages(files: list[str]) -> list[str]:
    """Detect programming languages from file extensions."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".kt": "kotlin",
        ".swift": "swift",
        ".go": "go",
        ".rs": "rust",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".scala": "scala",
        ".dart": "dart",
        ".lua": "lua",
        ".sh": "shell",
        ".sql": "sql",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".vue": "vue",
        ".svelte": "svelte",
    }
    languages: set[str] = set()
    for f in files:
        ext = Path(f).suffix.lower()
        if ext in ext_map:
            languages.add(ext_map[ext])
    return sorted(languages)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect review context for the deep-review skill."
    )
    parser.add_argument(
        "--commit",
        type=str,
        default=None,
        help="Review a specific commit SHA.",
    )
    parser.add_argument(
        "--base",
        type=str,
        default=None,
        help="Review all commits on the current branch vs this base branch.",
    )
    parser.add_argument(
        "--cached",
        action="store_true",
        help="Review only staged (cached) changes.",
    )
    args = parser.parse_args()

    rc, root = run_git(["rev-parse", "--show-toplevel"])
    if rc != 0:
        print(json.dumps({"ok": False, "error": "not a git repository"}, ensure_ascii=False, indent=2))
        return 1

    os.chdir(root)

    # Determine the review target
    target = "uncommitted"
    diff_args: list[str] = []
    name_only_args: list[str] = []
    numstat_args: list[str] = []
    stat_args: list[str] = []
    log_args: list[str] = []

    if args.commit:
        target = "commit"
        commit_sha = args.commit
        diff_args = ["show", commit_sha, "--format="]
        name_only_args = ["diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha]
        numstat_args = ["diff-tree", "--no-commit-id", "--numstat", "-r", commit_sha]
        stat_args = ["show", "--stat", "--format=", commit_sha]
        log_args = ["log", "--oneline", "-5", commit_sha]
    elif args.base:
        target = "branch-diff"
        merge_base_rc, merge_base = run_git(["merge-base", args.base, "HEAD"])
        if merge_base_rc != 0:
            print(json.dumps(
                {"ok": False, "error": f"could not find merge-base with '{args.base}'"},
                ensure_ascii=False, indent=2,
            ))
            return 1
        diff_args = ["diff", merge_base, "HEAD"]
        name_only_args = ["diff", "--name-only", merge_base, "HEAD"]
        numstat_args = ["diff", "--numstat", merge_base, "HEAD"]
        stat_args = ["diff", "--stat", merge_base, "HEAD"]
        log_args = ["log", "--oneline", f"{merge_base}..HEAD"]
    elif args.cached:
        target = "staged"
        diff_args = ["diff", "--cached"]
        name_only_args = ["diff", "--cached", "--name-only"]
        numstat_args = ["diff", "--cached", "--numstat"]
        stat_args = ["diff", "--cached", "--stat"]
        log_args = ["log", "--oneline", "-10"]
    else:
        target = "uncommitted"
        diff_args = ["diff", "HEAD"]
        name_only_args = ["diff", "--name-only", "HEAD"]
        numstat_args = ["diff", "--numstat", "HEAD"]
        stat_args = ["diff", "--stat", "HEAD"]
        log_args = ["log", "--oneline", "-10"]

    # Branch info
    branch_rc, branch = run_git(["branch", "--show-current"])
    detached_head = branch_rc != 0 or not branch

    # Gather context
    _, status_text = run_git(["status", "--short"])
    _, stat = run_git(stat_args)
    _, recent_commits = run_git(log_args)
    _, numstat = run_git(numstat_args)
    _, name_only = run_git(name_only_args)
    _, full_diff = run_git(diff_args)

    status_entries = parse_status(status_text)
    all_paths = [entry["path"] for entry in status_entries if entry.get("path")]
    changed_files = changed_file_list(name_only)
    secret_paths = [p for p in all_paths if SECRET_RE.search(p)]
    generated_paths = [p for p in all_paths if GENERATED_RE.search(p)]
    manifests = [name for name in MANIFESTS if Path(name).exists()]

    added, deleted = count_numstat(numstat)
    languages = detect_languages(changed_files)

    # Detect merge / rebase and conflicts
    merge_in_progress = Path(".git/MERGE_HEAD").exists()
    rebase_in_progress = (
        Path(".git/rebase-merge").exists()
        or Path(".git/rebase-apply").exists()
    )
    conflicted_paths = [
        entry["path"]
        for entry in status_entries
        if entry.get("code", "") in CONFLICT_CODES
    ]
    has_conflicts = bool(conflicted_paths)

    # Warnings specific to review context
    warnings: list[str] = []
    if has_conflicts:
        warnings.append("unresolved merge conflicts present")
    if merge_in_progress:
        warnings.append("merge in progress")
    if rebase_in_progress:
        warnings.append("rebase in progress")
    if secret_paths:
        warnings.append("secret-like paths present in working tree")
    if len(changed_files) == 0 and not full_diff.strip():
        warnings.append("no changes detected for the selected review target")
    if len(changed_files) > 50 or added + deleted > 2000:
        warnings.append("large diff; review may take longer")

    snapshot = {
        "ok": True,
        "review_target": target,
        "repo_root": root,
        "branch": branch,
        "detached_head": detached_head,
        "project_manifests": manifests,
        "languages": languages,
        "changed_files_count": len(changed_files),
        "changed_files": changed_files,
        "added_lines": added,
        "deleted_lines": deleted,
        "has_conflicts": has_conflicts,
        "conflicted_paths": conflicted_paths,
        "merge_in_progress": merge_in_progress,
        "rebase_in_progress": rebase_in_progress,
        "warnings": warnings,
        "secret_like_paths": secret_paths,
        "generated_like_paths": generated_paths,
        "diff_stat": stat,
        "status": status_text,
        "recent_commits": recent_commits,
        "full_diff": full_diff,
    }
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
