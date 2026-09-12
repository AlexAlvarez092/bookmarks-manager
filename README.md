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

## Usage

```bash
python3 safari_bookmarks_sync.py --target chrome [--profile "Default"]
python3 safari_bookmarks_sync.py --target brave  [--profile "Default"]
```

Run `python3 safari_bookmarks_sync.py --help` for the full list of options.

## Scheduling with cron

Add one `cron` line per destination browser you want to keep in sync. For
example, to sync every 10 minutes:

```cron
*/10 * * * * /usr/bin/python3 /path/to/repo/safari_bookmarks_sync.py --target chrome
*/10 * * * * /usr/bin/python3 /path/to/repo/safari_bookmarks_sync.py --target brave
```

Steps:

1. Find the absolute path to this repo and to `python3` (`which python3`).
2. Run `crontab -e` and add the lines above, adjusting the paths. Add
   `--profile "Profile 1"` (or whichever profile name applies) if you don't
   use the default profile.
3. Grant **Full Disk Access** to `cron` itself (not just Terminal), since
   `cron` runs the script outside of Terminal's own permissions: go to
   **System Settings > Privacy & Security > Full Disk Access**, click `+`,
   press `Cmd+Shift+G` and enter `/usr/sbin/cron`, then enable it. Without
   this, reads of Safari's `Bookmarks.plist` will fail with a permission
   error.
4. Make a change in Safari's bookmarks (add, rename, or delete one) and wait
   for the next scheduled run — it should be reflected in the destination
   browser(s) automatically. You can also trigger a run manually at any time
   with the commands above to verify sooner.

This has been manually verified end-to-end: syncing real Safari bookmarks
into both Chrome and Brave profiles correctly reproduces Safari's bookmarks
bar and every other top-level folder, with no manual steps beyond the
initial cron/Full Disk Access setup.
