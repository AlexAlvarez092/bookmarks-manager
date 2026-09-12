#!/usr/bin/env python3
"""Sync Safari's bookmarks into another (Chromium-based) browser.

This is the entry point meant to be scheduled via ``cron``, once per
destination browser. It ties together the building blocks implemented in
this project:

1. Read Safari's bookmarks tree (:mod:`safari_reader`).
2. Convert it to the destination browser's JSON format
   (:mod:`chromium_converter`).
3. Overwrite the destination browser's ``Bookmarks`` file with it
   (:mod:`destination_writer`).

Usage:
    python3 safari_bookmarks_sync.py --target chrome
    python3 safari_bookmarks_sync.py --target brave --profile "Profile 1"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chromium_converter import convert_to_chromium_bookmarks
from destination_writer import (
    DEFAULT_PROFILE,
    SUPPORTED_BROWSERS,
    DestinationWriteError,
    UnsupportedBrowserError,
    write_chromium_bookmarks,
)
from safari_reader import DEFAULT_SAFARI_BOOKMARKS_PATH, SafariBookmarksReadError, read_safari_bookmarks


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="safari_bookmarks_sync.py",
        description=(
            "One-way sync of Safari's bookmarks into another browser. "
            "Safari is always the source of truth: the destination "
            "browser's bookmarks are fully overwritten to match Safari's."
        ),
        epilog=(
            "Examples:\n"
            "  python3 safari_bookmarks_sync.py --target chrome\n"
            "  python3 safari_bookmarks_sync.py --target brave "
            '--profile "Profile 1"\n\n'
            "Typical cron setup (every 10 minutes), one line per browser:\n"
            "  */10 * * * * /usr/bin/python3 /path/to/safari_bookmarks_sync.py "
            "--target chrome\n"
            "  */10 * * * * /usr/bin/python3 /path/to/safari_bookmarks_sync.py "
            "--target brave"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--target",
        required=True,
        choices=SUPPORTED_BROWSERS,
        help="Destination browser to sync Safari's bookmarks into.",
    )
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help=(
            "Destination browser profile directory name "
            f"(default: '{DEFAULT_PROFILE}')."
        ),
    )
    parser.add_argument(
        "--safari-bookmarks-path",
        type=Path,
        default=DEFAULT_SAFARI_BOOKMARKS_PATH,
        help=(
            "Path to Safari's Bookmarks.plist "
            f"(default: '{DEFAULT_SAFARI_BOOKMARKS_PATH}')."
        ),
    )
    return parser


def main(argv=None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    try:
        safari_tree = read_safari_bookmarks(args.safari_bookmarks_path)
        chromium_bookmarks = convert_to_chromium_bookmarks(safari_tree)
        written_path = write_chromium_bookmarks(
            args.target, chromium_bookmarks, profile=args.profile
        )
    except (SafariBookmarksReadError, UnsupportedBrowserError, DestinationWriteError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Synced Safari bookmarks into {args.target} ({written_path}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
