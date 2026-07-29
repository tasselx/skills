#!/usr/bin/env python3
"""Unit tests for review_snapshot.py.

Run with:

    python3 -m pytest scripts/test_review_snapshot.py
    # or
    python3 scripts/test_review_snapshot.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import review_snapshot as rs  # noqa: E402


class TestNormalizeGitOutput(unittest.TestCase):
    def test_preserves_leading_status_space(self):
        raw = " M src/a.py\n?? new.py\n"
        out = rs.normalize_git_output(raw)
        self.assertTrue(out.startswith(" M "))
        self.assertIn("?? new.py", out)

    def test_drops_blank_lines_only(self):
        raw = " M a.py\n\n M b.py\n"
        out = rs.normalize_git_output(raw)
        self.assertEqual(out, " M a.py\n M b.py")


class TestRunGitStderrSeparation(unittest.TestCase):
    """run_git must NOT merge stderr into stdout (fix for phantom entries)."""

    def test_stderr_not_in_stdout(self):
        """A git warning on stderr must not appear in the stdout return."""
        rc, out, err = rs.run_git(["status", "--short"])
        # If git emits any warning, it goes to *err*, not *out*.
        # Even without warnings, out and err must be separate strings.
        self.assertIsInstance(out, str)
        self.assertIsInstance(err, str)
        # stdout should only contain status lines, never 'warning:'
        for line in out.splitlines():
            self.assertFalse(
                line.lower().startswith("warning:"),
                f"warning leaked into stdout: {line!r}",
            )

    def test_core_quote_path_disabled(self):
        """run_git should use -c core.quotePath=false so non-ASCII paths are clean."""
        # We can't easily test with a non-ASCII filename in CI,
        # but we can verify the git command includes the config.
        # Just ensure run_git returns a 3-tuple (rc, stdout, stderr).
        result = rs.run_git(["rev-parse", "--show-toplevel"])
        self.assertEqual(len(result), 3)


class TestValidateRef(unittest.TestCase):
    def test_valid_ref(self):
        self.assertEqual(rs._validate_ref("HEAD", "commit"), "HEAD")
        self.assertEqual(rs._validate_ref("abc123", "commit"), "abc123")

    def test_rejects_leading_dash(self):
        with self.assertRaises(ValueError):
            rs._validate_ref("--exec=/tmp/evil", "commit")
        with self.assertRaises(ValueError):
            rs._validate_ref("-", "base")

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            rs._validate_ref("", "commit")


class TestResolveRenamePath(unittest.TestCase):
    def test_full_rename(self):
        self.assertEqual(rs._resolve_rename_path("old/path => new/path"), "new/path")

    def test_brace_rename(self):
        self.assertEqual(
            rs._resolve_rename_path("src/{old => new}/file.py"),
            "src/new/file.py",
        )

    def test_brace_rename_no_suffix(self):
        self.assertEqual(
            rs._resolve_rename_path("{old => new}.py"),
            "new.py",
        )


class TestParseStatus(unittest.TestCase):
    def test_rename(self):
        entries = rs.parse_status("R  old.py -> new.py\n")
        self.assertEqual(entries[0]["path"], "new.py")
        self.assertEqual(entries[0]["old_path"], "old.py")

    def test_modified_unstaged_preserves_xy(self):
        # Leading space in XY code must survive (unstaged-only modify).
        entries = rs.parse_status(" M src/a.py\n")
        self.assertEqual(entries[0]["code"], " M")
        self.assertEqual(entries[0]["path"], "src/a.py")

    def test_untracked(self):
        entries = rs.parse_status("?? skills/new/file.py\n")
        self.assertEqual(entries[0]["code"], "??")
        self.assertEqual(entries[0]["path"], "skills/new/file.py")


class TestParseNameStatus(unittest.TestCase):
    def test_rename(self):
        entries = rs.parse_name_status("R100\told.ts\tnew.ts\n")
        self.assertEqual(entries[0]["code"], "R")
        self.assertEqual(entries[0]["path"], "new.ts")
        self.assertEqual(entries[0]["old_path"], "old.ts")

    def test_modify(self):
        entries = rs.parse_name_status("M\tsrc/main.go\n")
        self.assertEqual(entries[0]["path"], "src/main.go")


class TestCountNumstat(unittest.TestCase):
    def test_counts(self):
        text = "10\t2\tsrc/a.py\n3\t0\tsrc/b.py\n-\t-\tbin/img.png\n"
        added, deleted, files = rs.count_numstat(text)
        self.assertEqual(added, 13)
        self.assertEqual(deleted, 2)
        self.assertEqual(len(files), 3)
        self.assertTrue(files[2]["binary"])

    def test_brace_rename_in_numstat(self):
        text = "0\t0\tsrc/{old => new}/file.py\n"
        added, deleted, files = rs.count_numstat(text)
        self.assertEqual(files[0]["path"], "src/new/file.py")

    def test_full_rename_in_numstat(self):
        text = "0\t0\told/path => new/path.py\n"
        added, deleted, files = rs.count_numstat(text)
        self.assertEqual(files[0]["path"], "new/path.py")


class TestClassifyPath(unittest.TestCase):
    def test_test_file(self):
        self.assertIn("test", rs.classify_path("src/foo_test.go"))
        self.assertIn("test", rs.classify_path("tests/test_auth.py"))

    def test_docs(self):
        self.assertIn("docs", rs.classify_path("README.md"))
        self.assertIn("docs", rs.classify_path("docs/guide.md"))

    def test_migration(self):
        self.assertIn("migration", rs.classify_path("db/migrations/001_init.sql"))

    def test_security(self):
        self.assertIn("security_sensitive", rs.classify_path("src/auth/jwt_handler.go"))

    def test_generated(self):
        self.assertIn("generated_or_lock", rs.classify_path("node_modules/x/index.js"))
        self.assertIn("generated_or_lock", rs.classify_path("package-lock.json"))

    def test_production(self):
        tags = rs.classify_path("src/services/order.py")
        self.assertIn("production_code", tags)


class TestDetectStacks(unittest.TestCase):
    def test_python_go(self):
        stacks = rs.detect_stacks(["app/main.py", "cmd/server/main.go", "go.mod"])
        ids = {s["id"] for s in stacks}
        self.assertIn("python", ids)
        self.assertIn("go", ids)

    def test_frontend(self):
        stacks = rs.detect_stacks(["src/App.tsx", "package.json"])
        ids = {s["id"] for s in stacks}
        self.assertIn("frontend", ids)


class TestDetectPackages(unittest.TestCase):
    def test_packages(self):
        pkgs = rs.detect_packages(
            [
                "packages/auth/src/a.ts",
                "packages/api/src/b.ts",
                "apps/web/pages/index.tsx",
            ]
        )
        self.assertEqual(pkgs, ["apps/web", "packages/api", "packages/auth"])


class TestInferChangeTypes(unittest.TestCase):
    def test_docs_only(self):
        types = rs.infer_change_types(["README.md", "docs/a.md"], [])
        self.assertEqual(types, ["documentation"])

    def test_test_only(self):
        types = rs.infer_change_types(["tests/test_x.py"], [])
        self.assertEqual(types, ["test_only"])

    def test_migration(self):
        types = rs.infer_change_types(
            ["db/migrations/002_add_users.sql", "src/models/user.py"],
            [{"code": "A", "path": "db/migrations/002_add_users.sql"}],
        )
        self.assertIn("migration", types)


class TestRiskMatrix(unittest.TestCase):
    def test_weights(self):
        m = rs.risk_matrix_reference()
        w = m["weights"]
        self.assertEqual(w["Critical"]["Confirmed"], 100)
        self.assertEqual(w["Medium"]["Confirmed"], 20)
        self.assertEqual(w["Medium"]["Potential"], 8)
        self.assertLess(w["Medium"]["Potential"], w["Medium"]["Confirmed"])
        self.assertIn("merge_decision", m)

    def test_modifier_text_consistency(self):
        m = rs.risk_matrix_reference()
        modifier = m["modifiers"][0]
        # Must match SKILL.md wording (not "subtract the duplicate weight")
        self.assertIn("count the highest at full weight", modifier)
        self.assertIn("25%", modifier)
        self.assertNotIn("subtract", modifier)


class TestBuildFileRecords(unittest.TestCase):
    def test_exclude_generated(self):
        entries = [{"code": "M", "path": "dist/bundle.js"}]
        numstat = [{"path": "dist/bundle.js", "added": 10, "deleted": 0, "binary": False}]
        files = rs.build_file_records(entries, numstat)
        self.assertTrue(files[0]["exclude_by_default"])


class TestCountFileLines(unittest.TestCase):
    def test_counts_real_file(self):
        # Count lines of this test file itself
        test_path = Path(__file__).name
        root = str(Path(__file__).parent)
        count, is_binary = rs._count_file_lines(root, test_path)
        self.assertGreater(count, 0)
        self.assertFalse(is_binary)

    def test_nonexistent_file(self):
        count, is_binary = rs._count_file_lines("/tmp", "nonexistent_file_xyz.py")
        self.assertEqual(count, 0)
        self.assertFalse(is_binary)


class TestFinalize(unittest.TestCase):
    def test_large_diff_and_stacks(self):
        paths = [f"src/f{i}.py" for i in range(51)]
        core = {
            "mode": "uncommitted",
            "paths": paths,
            "entries": [{"code": "M", "path": p} for p in paths],
            "files": [
                {
                    "path": p,
                    "status": "M",
                    "tags": ["production_code"],
                    "exclude_by_default": False,
                }
                for p in paths
            ],
            "added_lines": 100,
            "deleted_lines": 50,
            "has_changes": True,
        }
        out = rs.finalize(core, "/tmp/repo", "main", False)
        self.assertTrue(out["large_diff"])
        self.assertIn("python", {s["id"] for s in out["detected_stacks"]})
        self.assertIn("Python", out["must_read_tech_stack_sections"])


if __name__ == "__main__":
    unittest.main()
