---
description: Ensure every photo and video in a folder has a Date Taken — fix extensions, write missing dates, convert PNG to JPEG where needed, sort by date, and clean up. Previews only; add --apply to make the changes.
argument-hint: <path-to-media-folder> [--all [--quarantine-ads] [--flatten]] [--apply]
---

# /fix-media-dates

Ensure every photo and video in the media folder has a readable Date Taken (Media Created for video).

## Dry run or apply

`$ARGUMENTS` is the media folder, optionally followed by `--all` (with `--quarantine-ads` or `--flatten` to opt in to those), `--apply`, or both. Below, `<folder>` means that folder without these flags.

- **With `--all`**, skip the step-by-step walk below and follow "All in one go" instead. `--all` alone is a dry run of every step; `--all --apply` makes all the changes.

- **Without `--apply`, this is a dry run.** Run every step below exactly as written. Each one only lists what it would do (`WOULD RENAME`, `WOULD WRITE`, `WOULD MOVE`, ...) and changes nothing. Each step is previewed against the folder as it is now, so a later step may do more once the earlier ones have run. Share the results, ask which optional steps (4, 6, 7 and ads) the user wants, then end with: to make these changes, type `/fix-media-dates <folder> --apply`.
- **With `--apply`**, run the same steps with `--apply` added to each `organize.py` command and `-Apply` added to each PowerShell script, so the changes are made. Run an optional step only if the user asked for it. Steps that only report (2) run the same either way.

## Prereq (first run only)

Python 3.9 or later, then:

```bash
pip install -r requirements.txt
# or:
pip install "pillow>=10.0" "openpyxl>=3.1"
```

## Steps

1. **Fix extensions.** `skills/media-date-organizer/scripts/Fix-Extensions.ps1 -Path "<folder>"`. Lists photos and videos whose extension doesn't match their content (`WOULD RENAME`), and renames them with `-Apply`.

2. **Scan metadata.** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --report-only`. Writes the audit workbook, `<folder name>_<photos|videos>_media_audit_<date>.xlsx`. Changes no photo or video. Share the summary.

3. **Write Date Taken where blank.** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --fill-blanks`. Photos and videos are picked up at any depth under `<folder>`. JPEG/PNG/TIFF files get `DateTimeOriginal` stamped into their EXIF from a date in the filename if there is one, else `<folder-date> 12:00:00` when the containing folder's name holds a date (`2019-08-30`, `2026-08-19 11-44-31`, `08-19-2026`, `Aug 19 2026`). File modified time is never used. HEIC/MOV are written with exiftool when it is installed, else flagged (need exiftool). Videos (MOV/MP4/M4V/3GP) with a blank Media Created get it from a date in the filename, else the nearest containing folder name holding a full date (`2019-08-30`, `11-11-2019`). A year-only folder name is not used; videos with neither source are listed as `SKIPPED (no date in filename or folder names)`, so share that list. Empty (0-byte) files are skipped and counted; if there are many, offer `--move-incomplete`, which moves incomplete files (0 bytes, all null bytes, or videos with no video header) into `<folder>/_incomplete`, keeping their dated subfolder, without deleting anything.

4. **Convert PNG → JPEG (optional).** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --convert-png`. For users who want Windows Explorer to show Date Taken for PNG screenshots. JPEG is lossy; the original PNG is left for the cleanup script. PNGs with transparent pixels are skipped and stay PNG.

5. **Move to date-matched folders.** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --apply-moves`. Files whose Date Taken doesn't match the folder name are moved to a sibling folder named for their real date.

6. **Sync Date Modified and Date Created (optional).** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --sync-timestamps`. For users who want Explorer's "Date Modified" and "Date Created" to show the real capture time. Files are picked up at any depth under `<folder>`. Date Modified is set only on files that look unedited (EXIF ModifyDate matches DateTimeOriginal and no editor-software tag); edited files keep their Date Modified, get Date Created set, and are listed.

7. **Flatten into the root folder (optional).** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --flatten`. For users who want the photos and videos out of their dated subfolders. Every file that has a Date Taken moves up into `<folder>` itself and the emptied subfolders are moved into `<folder>/_empty_folders`, keeping their path (not deleted); undated files stay put. Also available on its own as `/flatten-media`.

8. **Cleanup.** `skills/media-date-organizer/scripts/Cleanup-Pictures.ps1 -Path "<folder>"`. Lists PNGs already converted to JPG and empty folders; with `-Apply` it deletes those PNGs and moves the empty folders into `_empty_folders`. In the dry run, remind the user it comes last.

## Ad images and videos (optional)

If the folder holds ad images or videos (names like `0c4cda27-b4cc-4e92-a446-d6b780f24a64`, `bed51b94a_1595`, `gmsnet2`, `news_images%2F1714658759372`, `UnityAdsCache-<hash>` or `54ac2fda0a6755305200011c-b30-600`), run `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --quarantine-ads` before step 3 and share the list. Files with an ad-style name and no camera Make/Model move into `<folder>/_ads` for the user to review and delete; nothing is deleted. Name matches that have camera info are kept.

## All in one go

`/fix-media-dates <folder> --all` runs `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --all`. It deletes `.AAE` sidecar files, `Thumbs.db` thumbnail caches and macOS `._` sidecars, moves incomplete files into `<folder>/_incomplete`, then runs steps 3–6 (fill blanks, convert PNG, apply moves, sync timestamps).

- **Left out unless opted in:** ad quarantine and flatten. They run only if the user adds `--quarantine-ads` or `--flatten` to the slash command (`/fix-media-dates <folder> --all --flatten --apply`); pass those flags on to `organize.py`. Fixing extensions (step 1) and cleanup (step 8) are not part of `--all`; run them on their own.
- **`--all` without `--apply`** is a dry run: nothing is changed. Each phase is previewed against the folder as it is now, so a later phase may do more once the earlier ones have run. Warn the user that the applied run permanently deletes the sidecars and thumbnail caches listed as `WOULD DELETE`, then end with: to make all these changes, type `/fix-media-dates <folder> --all --apply` (with the same `--quarantine-ads` or `--flatten`, if any).
- **`--all --apply`** runs the same command with `--apply` added.

It ends with a `Summary of this run` block covering every phase's counts and problems; share that block with the user.

## Deliverables

- `<folder name>_<photos|videos>_media_audit_<date>.xlsx` at the root of `<folder>`. Every step above, the two PowerShell scripts and dry runs included, appends what it did to its Run log and Run counts sheets. The workbook must be closed in Excel while a step runs, or that step is not recorded.
- Summary message with counts (extensions corrected, dates written, files converted, files moved, timestamps synced, files flattened and empty folders moved to `_empty_folders`, ad files quarantined), saying "would" for a dry run.
- After a dry run: the line `/fix-media-dates <folder> --apply` (or `/fix-media-dates <folder> --all --apply` after `--all`) for the user to type. After `--apply`: the Cleanup-Pictures.ps1 reminder if it was not run.
