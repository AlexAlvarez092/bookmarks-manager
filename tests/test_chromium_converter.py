"""Tests for chromium_converter.py."""

import unittest

from chromium_converter import convert_to_chromium_bookmarks
from safari_reader import BOOKMARK_TYPE, FOLDER_TYPE


def _sample_safari_tree():
    return {
        "type": FOLDER_TYPE,
        "title": "",
        "children": [
            {
                "type": FOLDER_TYPE,
                "title": "BookmarksBar",
                "children": [
                    {"type": BOOKMARK_TYPE, "title": "Example", "url": "https://example.com"},
                    {
                        "type": FOLDER_TYPE,
                        "title": "Nested",
                        "children": [
                            {
                                "type": BOOKMARK_TYPE,
                                "title": "Nested Example",
                                "url": "https://nested.example.com",
                            }
                        ],
                    },
                ],
            },
            {
                "type": FOLDER_TYPE,
                "title": "BookmarksMenu",
                "children": [
                    {"type": BOOKMARK_TYPE, "title": "Menu Item", "url": "https://menu.example.com"}
                ],
            },
            {
                "type": FOLDER_TYPE,
                "title": "com.apple.ReadingList",
                "children": [],
            },
            {
                "type": FOLDER_TYPE,
                "title": "Custom Collection",
                "children": [
                    {"type": BOOKMARK_TYPE, "title": "Custom", "url": "https://custom.example.com"}
                ],
            },
        ],
    }


class ConvertToChromiumBookmarksTests(unittest.TestCase):
    def test_bookmarks_bar_children_go_to_bookmark_bar_root(self):
        result = convert_to_chromium_bookmarks(_sample_safari_tree())

        bar_children = result["roots"]["bookmark_bar"]["children"]
        self.assertEqual(len(bar_children), 2)
        self.assertEqual(bar_children[0]["type"], "url")
        self.assertEqual(bar_children[0]["url"], "https://example.com")
        self.assertEqual(bar_children[1]["type"], "folder")
        self.assertEqual(bar_children[1]["name"], "Nested")
        self.assertEqual(bar_children[1]["children"][0]["url"], "https://nested.example.com")

    def test_other_top_level_folders_go_to_other_root(self):
        result = convert_to_chromium_bookmarks(_sample_safari_tree())

        other_children = result["roots"]["other"]["children"]
        other_folder_names = [child["name"] for child in other_children]

        self.assertIn("BookmarksMenu", other_folder_names)
        self.assertIn("Custom Collection", other_folder_names)
        # Reading List is a Safari-specific feature, not a real bookmarks
        # folder, so it must be excluded.
        self.assertNotIn("com.apple.ReadingList", other_folder_names)

    def test_root_structure_matches_chromium_format(self):
        result = convert_to_chromium_bookmarks(_sample_safari_tree())

        self.assertEqual(result["version"], 1)
        self.assertIn("checksum", result)
        for root_name in ("bookmark_bar", "other", "synced"):
            root = result["roots"][root_name]
            self.assertEqual(root["type"], "folder")
            self.assertIn("id", root)
            self.assertIn("guid", root)
            self.assertIn("date_added", root)
            self.assertIn("date_modified", root)

    def test_ids_are_unique_across_the_whole_tree(self):
        result = convert_to_chromium_bookmarks(_sample_safari_tree())

        collected_ids = []

        def _collect(node):
            collected_ids.append(node["id"])
            for child in node.get("children", []):
                _collect(child)

        for root in result["roots"].values():
            _collect(root)

        self.assertEqual(len(collected_ids), len(set(collected_ids)))

    def test_url_nodes_have_no_children_key(self):
        result = convert_to_chromium_bookmarks(_sample_safari_tree())

        bar_children = result["roots"]["bookmark_bar"]["children"]
        url_node = bar_children[0]
        self.assertEqual(url_node["type"], "url")
        self.assertNotIn("children", url_node)


if __name__ == "__main__":
    unittest.main()
