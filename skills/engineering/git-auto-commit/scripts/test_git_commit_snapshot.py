#!/usr/bin/env python3
"""Unit tests for git_commit_snapshot.py.

Run with:

    python3 -m pytest scripts/test_git_commit_snapshot.py
    # or
    python3 scripts/test_git_commit_snapshot.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import unittest

# Make the script importable as a module
sys.path.insert(0, str(Path(__file__).parent))
import git_commit_snapshot as gcs  # noqa: E402


# ---------------------------------------------------------------------------
# SECRET_RE
# ---------------------------------------------------------------------------

class TestSecretRE(unittest.TestCase):
    """Tests for SECRET_RE pattern matching."""

    # --- should match ---

    def test_matches_env_files(self):
        should_match = [
            ".env",
            ".envrc",
            "config/.env",
            "project/.envrc",
            ".env.local",
            "env.production",
        ]
        for path in should_match:
            with self.subTest(path=path):
                self.assertIsNotNone(
                    gcs.SECRET_RE.search(path),
                    f"Expected SECRET_RE to match: {path}",
                )

    def test_matches_credential_keywords(self):
        should_match = [
            "credentials.json",
            "config/credentials.yaml",
            "api_key.txt",
            "secret_token.yaml",
            "private_key.pem",
            "passwords.csv",
            "passwd",
            "app.secret",
        ]
        for path in should_match:
            with self.subTest(path=path):
                self.assertIsNotNone(
                    gcs.SECRET_RE.search(path),
                    f"Expected SECRET_RE to match: {path}",
                )

    def test_matches_ssh_private_keys(self):
        should_match = [
            "id_rsa",
            ".ssh/id_rsa",
            "id_dsa",
            "id_ecdsa",
            "id_ed25519",
            "home/user/.ssh/id_rsa",
        ]
        for path in should_match:
            with self.subTest(path=path):
                self.assertIsNotNone(
                    gcs.SECRET_RE.search(path),
                    f"Expected SECRET_RE to match: {path}",
                )

    def test_matches_sensitive_extensions(self):
        should_match = [
            "server.pem",
            "cert.p12",
            "key.pfx",
            "app.keystore",
            "release.jks",
            "vault.kdbx",
            "vpn.ovpn",
            "config/private_key.key",
        ]
        for path in should_match:
            with self.subTest(path=path):
                self.assertIsNotNone(
                    gcs.SECRET_RE.search(path),
                    f"Expected SECRET_RE to match: {path}",
                )

    def test_matches_dotfiles(self):
        should_match = [
            ".netrc",
            ".htpasswd",
            ".htaccess",
            ".npmrc",
            ".pypirc",
        ]
        for path in should_match:
            with self.subTest(path=path):
                self.assertIsNotNone(
                    gcs.SECRET_RE.search(path),
                    f"Expected SECRET_RE to match: {path}",
                )

    # --- should NOT match ---

    def test_matches_ssh_private_key_backups(self):
        """Backup variants like id_rsa.bak should also be flagged."""
        should_match = [
            "id_rsa.bak",
            "id_rsa.old",
            "id_rsa.backup",
            ".ssh/id_dsa.bak",
            "id_ecdsa.old",
            "id_ed25519.backup",
        ]
        for path in should_match:
            with self.subTest(path=path):
                self.assertIsNotNone(
                    gcs.SECRET_RE.search(path),
                    f"Expected SECRET_RE to match: {path}",
                )

    def test_does_not_match_ssh_public_keys(self):
        should_not_match = [
            "id_rsa.pub",
            ".ssh/id_ed25519.pub",
        ]
        for path in should_not_match:
            with self.subTest(path=path):
                self.assertIsNone(
                    gcs.SECRET_RE.search(path),
                    f"Expected SECRET_RE to NOT match: {path}",
                )

    def test_does_not_match_normal_files(self):
        should_not_match = [
            "environment.ts",
            "tokens.py",
            "README.md",
            "src/main.py",
            "package.json",
            "setup.py",
            "config.ts",
        ]
        for path in should_not_match:
            with self.subTest(path=path):
                self.assertIsNone(
                    gcs.SECRET_RE.search(path),
                    f"Expected SECRET_RE to NOT match: {path}",
                )


# ---------------------------------------------------------------------------
# GENERATED_RE
# ---------------------------------------------------------------------------

class TestGeneratedRE(unittest.TestCase):
    """Tests for GENERATED_RE pattern matching."""

    def test_matches_generated_paths(self):
        should_match = [
            "node_modules/react/index.js",
            "dist/bundle.js",
            "build/app.js",
            "coverage/lcov.info",
            ".dart_tool/package_info.json",
            "Pods/AFNetworking/AFNetworking.h",
            "target/release/app",
            "image.png",
            "photo.jpg",
            "archive.zip",
            "data.tar.gz",
        ]
        for path in should_match:
            with self.subTest(path=path):
                self.assertIsNotNone(
                    gcs.GENERATED_RE.search(path),
                    f"Expected GENERATED_RE to match: {path}",
                )

    def test_matches_python_cache_paths(self):
        should_match = [
            "__pycache__/module.cpython-313.pyc",
            "src/__pycache__/helper.cpython-311.pyc",
            ".pytest_cache/v/cache/lastfailed",
            ".mypy_cache/3.13/data.json",
            ".ruff_cache/0.5.7/meta.json",
            ".venv/lib/python3.13/site-packages/django/__init__.py",
            "venv/bin/python",
            "app.pyc",
        ]
        for path in should_match:
            with self.subTest(path=path):
                self.assertIsNotNone(
                    gcs.GENERATED_RE.search(path),
                    f"Expected GENERATED_RE to match: {path}",
                )

    def test_does_not_match_source_files(self):
        should_not_match = [
            "src/index.ts",
            "lib/utils.py",
            "README.md",
            "main.go",
            "src/App.swift",
        ]
        for path in should_not_match:
            with self.subTest(path=path):
                self.assertIsNone(
                    gcs.GENERATED_RE.search(path),
                    f"Expected GENERATED_RE to NOT match: {path}",
                )


# ---------------------------------------------------------------------------
# parse_status
# ---------------------------------------------------------------------------

class TestParseStatus(unittest.TestCase):
    """Tests for parse_status function."""

    def test_parses_simple_status(self):
        text = " M src/main.py\n A new_file.txt"
        entries = gcs.parse_status(text)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["code"], " M")
        self.assertEqual(entries[0]["path"], "src/main.py")
        self.assertEqual(entries[1]["code"], " A")
        self.assertEqual(entries[1]["path"], "new_file.txt")

    def test_parses_rename_status(self):
        text = "R  old_name.txt -> new_name.txt"
        entries = gcs.parse_status(text)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["code"], "R ")
        self.assertEqual(entries[0]["path"], "new_name.txt")
        self.assertEqual(entries[0]["old_path"], "old_name.txt")

    def test_skips_empty_lines(self):
        text = " M src/main.py\n\n A new_file.txt\n"
        entries = gcs.parse_status(text)
        self.assertEqual(len(entries), 2)

    def test_handles_empty_string(self):
        entries = gcs.parse_status("")
        self.assertEqual(len(entries), 0)

    def test_handles_short_line(self):
        """Lines shorter than 4 chars should yield an empty path."""
        text = "??"
        entries = gcs.parse_status(text)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["code"], "??")
        self.assertEqual(entries[0]["path"], "")


# ---------------------------------------------------------------------------
# run_git
# ---------------------------------------------------------------------------

class TestRunGit(unittest.TestCase):
    """Tests for run_git function."""

    @patch("git_commit_snapshot.subprocess.run")
    def test_returns_stdout_on_success(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "main\n"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        rc, output = gcs.run_git(["branch", "--show-current"])
        self.assertEqual(rc, 0)
        self.assertEqual(output, "main")

    @patch("git_commit_snapshot.subprocess.run")
    def test_includes_stderr_on_error(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "fatal: not a git repository"
        mock_run.return_value = mock_proc

        rc, output = gcs.run_git(["rev-parse", "--show-toplevel"])
        self.assertEqual(rc, 1)
        self.assertIn("not a git repository", output)

    @patch("git_commit_snapshot.subprocess.run")
    def test_combines_stdout_and_stderr(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "feature-branch"
        mock_proc.stderr = "warning: some advice"
        mock_run.return_value = mock_proc

        rc, output = gcs.run_git(["branch", "--show-current"])
        self.assertEqual(rc, 0)
        self.assertIn("feature-branch", output)
        self.assertIn("warning", output)


# ---------------------------------------------------------------------------
# count_numstat
# ---------------------------------------------------------------------------

class TestCountNumstat(unittest.TestCase):
    """Tests for count_numstat function."""

    def test_normal_output(self):
        text = "10\t5\tfile1.py\n3\t0\tfile2.py\n"
        added, deleted = gcs.count_numstat(text)
        self.assertEqual(added, 13)
        self.assertEqual(deleted, 5)

    def test_handles_binary_files(self):
        # Binary files show '-' instead of numbers
        text = "-\t-\tbinary.png\n10\t5\tfile1.py\n"
        added, deleted = gcs.count_numstat(text)
        self.assertEqual(added, 10)
        self.assertEqual(deleted, 5)

    def test_handles_empty_string(self):
        added, deleted = gcs.count_numstat("")
        self.assertEqual(added, 0)
        self.assertEqual(deleted, 0)

    def test_handles_lines_with_fewer_tabs(self):
        # Lines with only 2 parts should be skipped
        text = "10\tfile1.py\n"
        added, deleted = gcs.count_numstat(text)
        self.assertEqual(added, 0)
        self.assertEqual(deleted, 0)

    def test_handles_renames(self):
        # Renames in numstat: "0\t0\told => new"
        text = "0\t0\told_name.py => new_name.py\n5\t2\tmain.py\n"
        added, deleted = gcs.count_numstat(text)
        self.assertEqual(added, 5)
        self.assertEqual(deleted, 2)


if __name__ == "__main__":
    unittest.main()
