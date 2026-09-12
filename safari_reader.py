"""Read Safari's bookmarks and expose them as a normalized in-memory tree.

Safari stores its bookmarks in a property list (plist) file at
``~/Library/Safari/Bookmarks.plist``. This module is responsible for
locating, reading and parsing that file, turning it into a simple tree
structure that the rest of the project can consume regardless of the
destination browser's own format.

The resulting tree is made of two kinds of nodes:

- Folder nodes: ``{"type": "folder", "title": str, "children": [...]}``.
- Bookmark nodes: ``{"type": "bookmark", "title": str, "url": str}``.
"""

from __future__ import annotations

import plistlib
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_SAFARI_BOOKMARKS_PATH = Path.home() / "Library" / "Safari" / "Bookmarks.plist"

FOLDER_TYPE = "folder"
BOOKMARK_TYPE = "bookmark"

# Safari's own type identifiers within the plist.
_WEB_BOOKMARK_TYPE_LIST = "WebBookmarkTypeList"
_WEB_BOOKMARK_TYPE_LEAF = "WebBookmarkTypeLeaf"


class SafariBookmarksReadError(Exception):
    """Raised when Safari's bookmarks file cannot be read or parsed."""


def _extract_title(node: Dict[str, Any]) -> str:
    """Return the best available title for a plist node."""
    if node.get("Title"):
        return node["Title"]
    uri_dictionary = node.get("URIDictionary", {})
    return uri_dictionary.get("title", "")


def _convert_node(node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Recursively convert a raw plist node into our normalized format.

    Returns ``None`` for node types we don't understand or that carry no
    useful data (e.g. bookmarks without a URL), so callers can filter them
    out.
    """
    node_type = node.get("WebBookmarkType")

    if node_type == _WEB_BOOKMARK_TYPE_LIST:
        children = []
        for raw_child in node.get("Children", []):
            converted_child = _convert_node(raw_child)
            if converted_child is not None:
                children.append(converted_child)
        return {
            "type": FOLDER_TYPE,
            "title": _extract_title(node),
            "children": children,
        }

    if node_type == _WEB_BOOKMARK_TYPE_LEAF:
        url = node.get("URLString")
        if not url:
            return None
        return {
            "type": BOOKMARK_TYPE,
            "title": _extract_title(node),
            "url": url,
        }

    # Unsupported node types (e.g. proxy bookmarks, reading list metadata)
    # are simply skipped.
    return None


def read_safari_bookmarks(
    path: Path = DEFAULT_SAFARI_BOOKMARKS_PATH,
) -> Dict[str, Any]:
    """Read Safari's bookmarks file and return it as a normalized tree.

    Args:
        path: Path to Safari's ``Bookmarks.plist`` file. Defaults to the
            standard location for the current user.

    Returns:
        The root folder node of the normalized bookmarks tree.

    Raises:
        SafariBookmarksReadError: If the file is missing, unreadable, or
            cannot be parsed as a valid Safari bookmarks plist.
    """
    try:
        with open(path, "rb") as bookmarks_file:
            raw_root = plistlib.load(bookmarks_file)
    except FileNotFoundError as exc:
        raise SafariBookmarksReadError(
            f"Safari bookmarks file not found at '{path}'. Make sure Safari "
            "is installed and has at least one bookmark."
        ) from exc
    except PermissionError as exc:
        raise SafariBookmarksReadError(
            f"Permission denied reading '{path}'. Grant 'Full Disk Access' "
            "to the process running this script (e.g. Terminal) in "
            "System Settings > Privacy & Security."
        ) from exc
    except (plistlib.InvalidFileException, ValueError) as exc:
        raise SafariBookmarksReadError(
            f"Could not parse Safari bookmarks file at '{path}': {exc}"
        ) from exc

    tree = _convert_node(raw_root)
    if tree is None:
        raise SafariBookmarksReadError(
            f"Unexpected format in Safari bookmarks file at '{path}'."
        )
    return tree


def _main() -> None:
    """Print the parsed bookmarks tree as JSON, for manual verification."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        description=(
            "Read Safari's bookmarks and print them as JSON, for manual "
            "verification."
        )
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_SAFARI_BOOKMARKS_PATH,
        help="Path to Safari's Bookmarks.plist (default: %(default)s)",
    )
    args = parser.parse_args()

    try:
        tree = read_safari_bookmarks(args.path)
    except SafariBookmarksReadError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(tree, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    _main()
