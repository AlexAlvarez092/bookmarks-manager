"""Tests for destination_writer.py."""

import json
import tempfile
import unittest
from pathlib import Path

from destination_writer import (
    DestinationWriteError,
    UnsupportedBrowserError,
    get_bookmarks_path,
    write_chromium_bookmarks,
)


class GetBookmarksPathTests(unittest.TestCase):
    def test_chrome_path(self):
        home = Path("/Users/someone")
        path = get_bookmarks_path("chrome", profile="Default", home=home)
        self.assertEqual(
            path,
            home
            / "Library/Application Support/Google/Chrome/Default/Bookmarks",
        )

    def test_brave_path(self):
        home = Path("/Users/someone")
        path = get_bookmarks_path("brave", profile="Profile 1", home=home)
        self.assertEqual(
            path,
            home
            / "Library/Application Support/BraveSoftware/Brave-Browser/Profile 1/Bookmarks",
        )

    def test_browser_name_is_case_insensitive(self):
        home = Path("/Users/someone")
        path = get_bookmarks_path("Chrome", home=home)
        self.assertTrue(str(path).endswith("Google/Chrome/Default/Bookmarks"))

    def test_unsupported_browser_raises(self):
        with self.assertRaises(UnsupportedBrowserError):
            get_bookmarks_path("firefox")


class WriteChromiumBookmarksTests(unittest.TestCase):
    def setUp(self):
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        self.home = Path(tmp_dir.name)

    def _create_profile_dir(self, browser, profile="Default"):
        path = get_bookmarks_path(browser, profile=profile, home=self.home)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def test_writes_json_content_to_expected_path(self):
        expected_path = self._create_profile_dir("chrome")
        payload = {"version": 1, "roots": {}}

        written_path = write_chromium_bookmarks("chrome", payload, home=self.home)

        self.assertEqual(written_path, expected_path)
        with open(written_path, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), payload)

    def test_overwrites_existing_file_completely(self):
        path = self._create_profile_dir("brave")
        path.write_text('{"old": "content"}', encoding="utf-8")

        new_payload = {"version": 1, "roots": {"other": "value"}}
        write_chromium_bookmarks("brave", new_payload, home=self.home)

        with open(path, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), new_payload)

    def test_missing_profile_directory_raises_clear_error(self):
        with self.assertRaises(DestinationWriteError) as ctx:
            write_chromium_bookmarks("chrome", {"version": 1}, home=self.home)

        self.assertIn("does not exist", str(ctx.exception))

    def test_unsupported_browser_raises(self):
        with self.assertRaises(UnsupportedBrowserError):
            write_chromium_bookmarks("firefox", {"version": 1}, home=self.home)


if __name__ == "__main__":
    unittest.main()
