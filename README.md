# bookmarks-manager

Automatically synchronizes bookmarks from **Safari** to other browsers on
macOS, in a one-way fashion: Safari is always the source of truth, and the
destination browsers end up with an exact copy of its bookmark tree
(including folders).

## Motivation

Safari is the main browser used to manage bookmarks, but other browsers
(Chrome, Brave, ...) are used day to day as well. There is no native
synchronization between them, so this project automates:

- Reading the full bookmark structure from Safari.
- Writing it to the destination browser, **overwriting** its bookmarks file
  so it ends up identical to Safari's (new bookmarks are added, existing
  ones are updated, and ones no longer in Safari are removed).

## Current scope

- macOS only.
- One-way sync: Safari → other browser (never the other way around).
- Supported destination browsers: **Chrome** and **Brave** (Chromium-based).
- Designed to run periodically via `cron`, one line per destination browser,
  passing the necessary parameters (browser, profile, etc.) as
  command-line arguments.
- No backups of the destination bookmarks file are kept, and there is no
  locking if the destination browser is open: if the browser overwrites the
  file when it closes, the next scheduled run will fix it automatically.

## Technology

- **Python 3** (bundled with macOS), no external dependencies:
  - `plistlib` to read `~/Library/Safari/Bookmarks.plist`.
  - `json` to read/write the `Bookmarks` file used by Chrome/Brave.

## Usage (planned)

```bash
python3 safari_bookmarks_sync.py --target chrome [--profile "Default"]
python3 safari_bookmarks_sync.py --target brave  [--profile "Default"]
```

Example `cron` configuration (every 10 minutes):

```cron
*/10 * * * * /usr/bin/python3 /path/to/repo/safari_bookmarks_sync.py --target chrome
*/10 * * * * /usr/bin/python3 /path/to/repo/safari_bookmarks_sync.py --target brave
```

> Note: reading Safari's bookmarks may require granting "Full Disk Access" to
> the process running the script (e.g. Terminal or `cron`), since Safari's
> bookmarks file is protected by macOS.
