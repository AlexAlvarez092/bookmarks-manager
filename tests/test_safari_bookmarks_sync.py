"""Tests for safari_bookmarks_sync.py (the CLI entry point)."""

import io
import json
import plistlib
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import destination_writer
import safari_bookmarks_sync


def _sample_plist_root():
    return {
        "WebBookmarkType": "WebBookmarkTypeList",
        "Children": [
            {
                "WebBookmarkType": "WebBookmarkTypeList",
                "Title": "BookmarksBar",
                "Children": [
                    {
                        "WebBookmarkType": "WebBookmarkTypeLeaf",
                        "URLString": "https://example.com",
                        "URIDictionary": {"title": "Example"},
                    }
                ],
            }
        ],
    }


class MainCliTests(unittest.TestCase):
    def setUp(self):
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        self.tmp_path = Path(tmp_dir.name)

        self.plist_path = self.tmp_path / "Bookmarks.plist"
        with open(self.plist_path, "wb") as fh:
            plistlib.dump(_sample_plist_root(), fh)

        self.home = self.tmp_path / "home"
        chrome_profile_dir = (
            self.home / "Library/Application Support/Google/Chrome/Default"
        )
        chrome_profile_dir.mkdir(parents=True)

    def _run_main(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with mock.patch.object(Path, "home", return_value=self.home):
                exit_code = safari_bookmarks_sync.main(argv)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_successful_sync_writes_expected_bookmarks_file(self):
        argv = [
            "--target",
            "chrome",
            "--safari-bookmarks-path",
            str(self.plist_path),
        ]

        exit_code, stdout, _ = self._run_main(argv)

        self.assertEqual(exit_code, 0)
        self.assertIn("Synced Safari bookmarks into chrome", stdout)

        bookmarks_path = (
            self.home
            / "Library/Application Support/Google/Chrome/Default/Bookmarks"
        )
        with open(bookmarks_path, encoding="utf-8") as fh:
            written = json.load(fh)
        bar_children = written["roots"]["bookmark_bar"]["children"]
        self.assertEqual(len(bar_children), 1)
        self.assertEqual(bar_children[0]["url"], "https://example.com")

    def test_missing_safari_file_returns_error_exit_code(self):
        argv = [
            "--target",
            "chrome",
            "--safari-bookmarks-path",
            str(self.tmp_path / "does-not-exist.plist"),
        ]

        exit_code, _, stderr = self._run_main(argv)

        self.assertEqual(exit_code, 1)
        self.assertIn("Error:", stderr)

    def test_invalid_target_is_rejected_by_argparse(self):
        with self.assertRaises(SystemExit) as ctx:
            with redirect_stderr(io.StringIO()):
                safari_bookmarks_sync.main(["--target", "firefox"])
        self.assertNotEqual(ctx.exception.code, 0)

    def test_missing_required_target_is_rejected_by_argparse(self):
        with self.assertRaises(SystemExit) as ctx:
            with redirect_stderr(io.StringIO()):
                safari_bookmarks_sync.main([])
        self.assertNotEqual(ctx.exception.code, 0)

    def test_missing_destination_profile_returns_error_exit_code(self):
        argv = [
            "--target",
            "chrome",
            "--profile",
            "Nonexistent Profile",
            "--safari-bookmarks-path",
            str(self.plist_path),
        ]

        exit_code, _, stderr = self._run_main(argv)

        self.assertEqual(exit_code, 1)
        self.assertIn("Error:", stderr)


if __name__ == "__main__":
    unittest.main()
