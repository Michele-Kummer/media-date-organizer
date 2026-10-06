---
description: Ensure every photo in a folder has a Date Taken — fix extensions, write missing dates, convert PNG to JPEG where needed, sort by date, and clean up.
argument-hint: <path-to-photo-folder>
---

# /fix-photo-dates

Ensure every photo in `$ARGUMENTS` has a readable Date Taken.

## Prereq (first run only)

```bash
pip install -r requirements.txt
```

## Steps

1. **Fix extensions.** Run `skills/photo-date-fixer/scripts/Fix-Extensions.ps1 -Path "$ARGUMENTS"`. Use `-WhatIf` first on unfamiliar folders.

2. **Scan metadata.** Run `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --report-only`. Writes `photo-audit.xlsx`. Share the summary before anything destructive.

3. **Write Date Taken where blank.** After user confirms: `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --fill-blanks`. JPEG/PNG/TIFF files get `DateTimeOriginal` stamped into their EXIF from a date in the filename if there is one, else `<folder-date> 12:00:00` when the containing folder is named `YYYY-MM-DD`. File modified time is never used. HEIC/MOV are written with exiftool when it is installed, else flagged (need exiftool). Empty (0-byte) files are skipped and counted; if there are many, offer `--move-no-data --dry-run`, then `--move-no-data`, which moves files with no image data into `$ARGUMENTS/_no-image-data` without deleting anything.

4. **Convert PNG → JPEG (optional).** If the user wants Windows Explorer to show Date Taken for PNG screenshots, run `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --convert-png` after confirming. JPEG is lossy; the original PNG is left for the cleanup script. PNGs with transparent pixels are skipped and stay PNG.

5. **Move to date-matched folders.** `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --apply-moves`. Files whose Date Taken doesn't match the folder name are moved to a sibling folder named for their real date.

6. **Sync Date Modified and Date Created (optional).** If the user wants Explorer's "Date Modified" and "Date Created" to show the real capture time, run `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --sync-timestamps`. Only files that look unedited (EXIF ModifyDate matches DateTimeOriginal and no editor-software tag) are touched; edited files are skipped and listed.

7. **Flatten into the root folder (optional).** If the user wants the photos out of their dated subfolders, preview with `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --flatten --dry-run`, then after confirming run it without `--dry-run`. Every file that has a Date Taken moves up into `$ARGUMENTS` itself and the emptied subfolders are deleted; undated files stay put. Also available on its own as `/flatten-photos`.

8. **Cleanup.** Remind the user: `skills/photo-date-fixer/scripts/Cleanup-Pictures.ps1 -Path "$ARGUMENTS"` removes duplicate base-name files and empty folders.

## Ad images (optional, any time)

If the folder holds ad images (names like `0c4cda27-b4cc-4e92-a446-d6b780f24a64`, `bed51b94a_1595` or `gmsnet2`), preview with `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --quarantine-ads --dry-run`, share the list, then after confirming run it without `--dry-run`. Files with an ad-style name and no camera Make/Model move into `$ARGUMENTS/_ads` for the user to review and delete; nothing is deleted. Name matches that have camera info are kept. Best done before step 3.

## All in one go

Once the user has confirmed steps 3–6 together, they can be run in one command: `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --all` (add `--move-no-data`, `--quarantine-ads` or `--flatten` to include those). It ends with a `Summary of this run` block covering every phase's counts and problems; share that block with the user.

## Deliverables

- `photo-audit.xlsx` at the root of `$ARGUMENTS`.
- Summary message with counts (extensions corrected, dates written, files converted, files moved, timestamps synced, files flattened and folders removed, ad images quarantined) plus the Cleanup-Pictures.ps1 reminder.
