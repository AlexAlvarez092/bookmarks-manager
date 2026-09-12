"""Convert the normalized Safari bookmarks tree into Chromium's bookmarks format.

Chrome and Brave (and other Chromium-based browsers) store bookmarks in a
JSON file with a well known structure: a ``roots`` object containing
``bookmark_bar``, ``other`` and ``synced`` folders, each one recursively
containing ``folder``/``url`` nodes with their own ``id``, ``guid`` and
``date_added``/``date_modified`` timestamps (expressed as the number of
microseconds since 1601-01-01, the "WebKit epoch").

This module takes the tree produced by :mod:`safari_reader` and maps it onto
that structure:

- Safari's top-level ``BookmarksBar`` folder becomes Chromium's
  ``bookmark_bar`` root, so bookmarks that are on Safari's bookmarks bar end
  up on the destination browser's bookmarks bar too.
- Every other top-level folder (e.g. ``BookmarksMenu`` or any custom
  top-level folder/collection the user created in Safari) is kept as a
  sub-folder under Chromium's ``other`` root, preserving its name and
  contents.
- Safari's Reading List (``com.apple.ReadingList``) is not a user-managed
  bookmarks folder, so it is intentionally excluded from the conversion.
"""

from __future__ import annotations

import itertools
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, Optional

from safari_reader import BOOKMARK_TYPE, FOLDER_TYPE

# Microseconds between the WebKit/Chrome epoch (1601-01-01) and the Unix
# epoch (1970-01-01), used to convert to Chrome's timestamp format.
_WEBKIT_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)

_BOOKMARKS_BAR_SAFARI_TITLE = "BookmarksBar"
_SAFARI_INTERNAL_PREFIXES = ("com.apple.",)

_BOOKMARK_BAR_ROOT_NAME = "Bookmarks bar"
_OTHER_ROOT_NAME = "Other bookmarks"
_SYNCED_ROOT_NAME = "Mobile bookmarks"


def _chrome_timestamp(moment: Optional[datetime] = None) -> str:
    """Return ``moment`` (default: now) as a Chrome-style timestamp string."""
    moment = moment or datetime.now(timezone.utc)
    microseconds = int((moment - _WEBKIT_EPOCH).total_seconds() * 1_000_000)
    return str(microseconds)


def _new_guid() -> str:
    return str(uuid.uuid4())


def _is_safari_internal_folder(node: Dict[str, Any]) -> bool:
    title = node.get("title", "")
    return node["type"] == FOLDER_TYPE and title.startswith(_SAFARI_INTERNAL_PREFIXES)


def _convert_node(
    node: Dict[str, Any], ids: Iterator[int], timestamp: str
) -> Dict[str, Any]:
    """Recursively convert a normalized Safari node into a Chromium node."""
    common = {
        "date_added": timestamp,
        "date_last_used": "0",
        "guid": _new_guid(),
        "id": str(next(ids)),
        "name": node["title"],
    }

    if node["type"] == FOLDER_TYPE:
        return {
            **common,
            "type": "folder",
            "date_modified": timestamp,
            "children": [
                _convert_node(child, ids, timestamp)
                for child in node["children"]
                if not _is_safari_internal_folder(child)
            ],
        }

    # BOOKMARK_TYPE
    return {
        **common,
        "type": "url",
        "url": node["url"],
    }


def _make_root(name: str, root_id: int, timestamp: str) -> Dict[str, Any]:
    return {
        "date_added": timestamp,
        "date_last_used": "0",
        "date_modified": timestamp,
        "guid": _new_guid(),
        "id": str(root_id),
        "name": name,
        "type": "folder",
        "children": [],
    }


def convert_to_chromium_bookmarks(safari_tree: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a normalized Safari bookmarks tree into Chromium's format.

    Args:
        safari_tree: The root folder node returned by
            :func:`safari_reader.read_safari_bookmarks`.

    Returns:
        A dict ready to be serialized as a Chromium ``Bookmarks`` file
        (i.e. matching the structure Chrome/Brave expect at
        ``<Profile>/Bookmarks``).
    """
    timestamp = _chrome_timestamp()
    ids = itertools.count(start=4)  # 1-3 are reserved for the root folders.

    bookmark_bar_root = _make_root(_BOOKMARK_BAR_ROOT_NAME, 1, timestamp)
    other_root = _make_root(_OTHER_ROOT_NAME, 2, timestamp)
    synced_root = _make_root(_SYNCED_ROOT_NAME, 3, timestamp)

    for top_level_node in safari_tree.get("children", []):
        if top_level_node["type"] != FOLDER_TYPE:
            continue
        if _is_safari_internal_folder(top_level_node):
            continue

        if top_level_node["title"] == _BOOKMARKS_BAR_SAFARI_TITLE:
            bookmark_bar_root["children"] = [
                _convert_node(child, ids, timestamp)
                for child in top_level_node["children"]
                if not _is_safari_internal_folder(child)
            ]
        else:
            other_root["children"].append(_convert_node(top_level_node, ids, timestamp))

    return {
        "checksum": "",
        "roots": {
            "bookmark_bar": bookmark_bar_root,
            "other": other_root,
            "synced": synced_root,
        },
        "version": 1,
    }
