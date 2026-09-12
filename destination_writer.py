"""Locate and overwrite a Chromium-based browser's bookmarks file.

Chrome, Brave and other Chromium-based browsers keep their bookmarks in a
JSON file named ``Bookmarks`` inside each profile's directory under
``~/Library/Application Support/<Browser>/<Profile>/``. This module knows
how to find that file for the browsers this project supports, and how to
overwrite it with the JSON produced by :mod:`chromium_converter`.

The write is a full overwrite by design (per the project's requirements):
the destination browser is meant to end up as an exact copy of Safari, so
there is no merging with the browser's existing bookmarks, and no backup of
the previous file is kept. If the destination browser is open and rewrites
the file itself on close, the next scheduled sync run is expected to fix
the state again.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_PROFILE = "Default"

# Base directory (under ~/Library/Application Support) for each supported
# browser, relative to the user's home directory.
_BROWSER_BASE_DIRS = {
    "chrome": Path("Library/Application Support/Google/Chrome"),
    "brave": Path("Library/Application Support/BraveSoftware/Brave-Browser"),
}

SUPPORTED_BROWSERS = tuple(_BROWSER_BASE_DIRS.keys())


class UnsupportedBrowserError(Exception):
    """Raised when the requested destination browser isn't supported."""


class DestinationWriteError(Exception):
    """Raised when the destination bookmarks file cannot be written."""


def get_bookmarks_path(
    browser: str, profile: str = DEFAULT_PROFILE, home: Optional[Path] = None
) -> Path:
    """Return the path to a browser profile's ``Bookmarks`` file.

    Args:
        browser: One of :data:`SUPPORTED_BROWSERS` (e.g. ``"chrome"``,
            ``"brave"``).
        profile: The browser profile directory name (e.g. ``"Default"``,
            ``"Profile 1"``).
        home: Override for the user's home directory, mainly for testing.

    Raises:
        UnsupportedBrowserError: If ``browser`` isn't supported.
    """
    normalized_browser = browser.lower()
    base_dir = _BROWSER_BASE_DIRS.get(normalized_browser)
    if base_dir is None:
        raise UnsupportedBrowserError(
            f"Unsupported browser '{browser}'. Supported browsers: "
            f"{', '.join(SUPPORTED_BROWSERS)}."
        )

    home = home or Path.home()
    return home / base_dir / profile / "Bookmarks"


def write_chromium_bookmarks(
    browser: str,
    chromium_bookmarks: Dict[str, Any],
    profile: str = DEFAULT_PROFILE,
    home: Optional[Path] = None,
) -> Path:
    """Overwrite a browser profile's bookmarks file with new content.

    Args:
        browser: One of :data:`SUPPORTED_BROWSERS` (e.g. ``"chrome"``,
            ``"brave"``).
        chromium_bookmarks: The bookmarks structure to write, as produced by
            :func:`chromium_converter.convert_to_chromium_bookmarks`.
        profile: The browser profile directory name.
        home: Override for the user's home directory, mainly for testing.

    Returns:
        The path of the file that was written.

    Raises:
        UnsupportedBrowserError: If ``browser`` isn't supported.
        DestinationWriteError: If the profile directory doesn't exist (the
            browser/profile likely isn't installed) or the file can't be
            written for another reason (e.g. permissions).
    """
    bookmarks_path = get_bookmarks_path(browser, profile, home=home)

    if not bookmarks_path.parent.is_dir():
        raise DestinationWriteError(
            f"Profile directory '{bookmarks_path.parent}' does not exist. "
            f"Make sure {browser.capitalize()} is installed and the "
            f"'{profile}' profile has been created (open the browser at "
            "least once)."
        )

    try:
        with open(bookmarks_path, "w", encoding="utf-8") as bookmarks_file:
            json.dump(chromium_bookmarks, bookmarks_file, indent=3)
    except OSError as exc:
        raise DestinationWriteError(
            f"Could not write bookmarks file at '{bookmarks_path}': {exc}"
        ) from exc

    return bookmarks_path
