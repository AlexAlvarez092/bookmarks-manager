"""Tests for safari_reader.py."""

import plistlib
import tempfile
import unittest
from pathlib import Path

from safari_reader import (
    BOOKMARK_TYPE,
    FOLDER_TYPE,
    SafariBookmarksReadError,
    read_safari_bookmarks,
)


def _sample_plist_root():
    """Build a minimal, representative Safari bookmarks plist structure."""
    return {
        "WebBookmarkType": "WebBookmarkTypeList",
        "Children": [
            {
                "WebBookmarkType": "WebBookmarkTypeList",
                "Title": "Favorites",
                "Children": [
                    {
                        "WebBookmarkType": "WebBookmarkTypeLeaf",
                        "URLString": "https://example.com",
                        "URIDictionary": {"title": "Example"},
                    },
                    {
                        "WebBookmarkType": "WebBookmarkTypeList",
                        "Title": "Nested Folder",
                        "Children": [
                            {
                                "WebBookmarkType": "WebBookmarkTypeLeaf",
                                "URLString": "https://nested.example.com",
                                "URIDictionary": {"title": "Nested"},
                            }
                        ],
                    },
                    # A leaf with no URL should be skipped.
                    {
                        "WebBookmarkType": "WebBookmarkTypeLeaf",
                        "URIDictionary": {"title": "No URL"},
                    },
                    # An unsupported node type should be skipped.
                    {"WebBookmarkType": "WebBookmarkTypeProxy"},
                ],
            }
        ],
    }


class ReadSafariBookmarksTests(unittest.TestCase):
    def _write_plist(self, root):
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        path = Path(tmp_dir.name) / "Bookmarks.plist"
        with open(path, "wb") as fh:
            plistlib.dump(root, fh)
        return path

    def test_parses_nested_folders_and_bookmarks(self):
        path = self._write_plist(_sample_plist_root())

        tree = read_safari_bookmarks(path)

        self.assertEqual(tree["type"], FOLDER_TYPE)
        favorites = tree["children"][0]
        self.assertEqual(favorites["type"], FOLDER_TYPE)
        self.assertEqual(favorites["title"], "Favorites")

        # Only the valid bookmark and the nested folder should remain;
        # the URL-less leaf and the unsupported proxy node are skipped.
        self.assertEqual(len(favorites["children"]), 2)

        example_bookmark = favorites["children"][0]
        self.assertEqual(example_bookmark["type"], BOOKMARK_TYPE)
        self.assertEqual(example_bookmark["title"], "Example")
        self.assertEqual(example_bookmark["url"], "https://example.com")

        nested_folder = favorites["children"][1]
        self.assertEqual(nested_folder["type"], FOLDER_TYPE)
        self.assertEqual(nested_folder["title"], "Nested Folder")
        self.assertEqual(len(nested_folder["children"]), 1)
        self.assertEqual(
            nested_folder["children"][0]["url"], "https://nested.example.com"
        )

    def test_missing_file_raises_clear_error(self):
        missing_path = Path(tempfile.gettempdir()) / "does-not-exist.plist"

        with self.assertRaises(SafariBookmarksReadError) as ctx:
            read_safari_bookmarks(missing_path)

        self.assertIn("not found", str(ctx.exception))

    def test_invalid_plist_raises_clear_error(self):
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        path = Path(tmp_dir.name) / "Bookmarks.plist"
        path.write_bytes(b"this is not a valid plist")

        with self.assertRaises(SafariBookmarksReadError) as ctx:
            read_safari_bookmarks(path)

        self.assertIn("Could not parse", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
