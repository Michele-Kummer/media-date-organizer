---
name: photo-date-fixer
description: Use this skill when the user wants every photo in a folder to have a readable Date Taken. Triggers include "fix the dates on my photos," "make sure all my pictures have Date Taken," "my photos don't show Date Taken in Explorer," "convert these PNGs so I can see the date," "sort my photos by when they were taken," or any mention of blank/missing/wrong Date Taken on image files. The skill reads real EXIF and container metadata (HEIC/HEIF, MOV/MP4, PNG/JPEG) without external tools, writes Date Taken where it is missing, converts PNG to JPEG when the user needs Windows Explorer to surface the date, moves files to date-matched folders, optionally syncs Windows file timestamps to Date Taken for unedited files, and produces an XLSX audit. Works on photos from any source. Do NOT use for RAW camera files or video libraries larger than a few thousand items — the sandbox parse would be slow.
---

# photo-date-fixer

Ensures every photo has a Date Taken. Seven phases, each independently runnable.

## Prerequisites

The scripts rely on two Python packages: `Pillow` (image handling + EXIF) and `openpyxl` (audit workbook). On first run in a fresh Python environment, install both before invoking any phase:

```bash
pip install -r requirements.txt
# or:
pip install pillow openpyxl
```

Scanning still works without `openpyxl` — only the XLSX report is skipped. Writing EXIF or converting PNG requires `Pillow`.

## When to run

- The user has a folder of photos and wants Date Taken populated everywhere.
- Dates are showing blank in Windows Explorer for some files (PNG screenshots especially).
- Files have the wrong extension or are in a wrong folder relative to their real date.
- The user wants an audit of which files have Date Taken and which don't.
- The user wants Explorer's "Date Modified" and "Date Created" to reflect the real capture time on untouched files.

## Required inputs

- `PhotoRoot`: the folder to process. Ask once if not given.
- Confirmation before each destructive step (write EXIF, rename, move, convert, delete, timestamp sync).

## Workflow

Each phase below can be run on its own, or several can be given on one command line. `python scripts/organize.py --root "<PhotoRoot>" --all` deletes `.AAE` sidecars and then runs Phases 3–6 (`--delete-aae --fill-blanks --convert-png --apply-moves --sync-timestamps`); add `--move-no-data`, `--quarantine-ads` or `--flatten` to include those. Phases always run in this order whatever order the flags are typed in: delete-aae, move-no-data, quarantine-ads, fill-blanks, convert-png, apply-moves, sync-timestamps, flatten. A multi-phase run ends with a `Summary of this run` block listing every phase's counts and the problem lines (`FAILED`, `SKIPPED`, `COLLISION`, `NOTE`) it reported, up to 50 per phase. Use it only after the user has confirmed every phase it includes; `--report-only` cannot be combined with other phases.

### Phase 1 — Fix extensions
`scripts/Fix-Extensions.ps1 -Path "<PhotoRoot>"`. Reads magic bytes and renames files whose extensions lie about the actual format. Preview with `-WhatIf` first.

### Phase 2 — Scan metadata
`python scripts/organize.py --root "<PhotoRoot>" --report-only`. Reads Date Taken from the real format of each file:
- HEIC/HEIF → embedded TIFF/EXIF `DateTimeOriginal`
- MOV/MP4/M4V → `mvhd` atom `creation_time`
- PNG/JPEG/TIFF → standard EXIF via Pillow

Writes `photo-audit.xlsx` summarizing which files have Date Taken, which don't, and which are in a folder that doesn't match their date. Share the summary with the user before Phase 3.

### Phase 3 — Write Date Taken where it's missing
`python scripts/organize.py --root "<PhotoRoot>" --fill-blanks`. For every file whose Date Taken is blank:
- If the filename contains a date (e.g. Snapchat exports `2023-12-20_<id>-main.jpg`, or `IMG_20231220_142355.jpg`), write that as `DateTimeOriginal` (JPEG, PNG, TIFF), using the time from the name if present, else `12:00:00`.
- Otherwise, if the containing folder is named `YYYY-MM-DD`, write `DateTimeOriginal = <folder-date> 12:00:00`.
- The file's modified time is never used as a source — it usually reflects the import, not the capture.
- JPEGs get the EXIF segment swapped in place; the image data is not re-encoded.
- HEIC/MOV files are written with `exiftool` when it is installed (on PATH, or in winget's default folder). Without it they are flagged as `SKIPPED (needs exiftool)` — offer to install it (`winget install --id OliverBetz.ExifTool -e --source winget`), or convert HEIC → JPEG in Phase 4.
- Empty (0-byte) files are skipped and reported as one `NOTE:` count. GIF/BMP/WEBP have no Date Taken field and are counted as `unsupported-format`. If the count of empty files is large, suggest `--move-no-data` (below).

### Phase 4 — Convert formats Windows can't read Date Taken from
`python scripts/organize.py --root "<PhotoRoot>" --convert-png`. Converts PNG files to JPEG at quality 95, preserving EXIF, so Windows Explorer surfaces Date Taken. Only run after confirming with the user — JPEG is lossy and the original PNG is left in place for the cleanup script to remove. PNGs with any transparent pixels are never converted (JPEG has no transparency) and are counted as `skipped-transparent`; they stay PNG. PNGs named `*-overlay.png` (Snapchat's transparent caption layers) are skipped too.

### Phase 5 — Move to date-matched folders
`python scripts/organize.py --root "<PhotoRoot>" --apply-moves`. Any file whose Date Taken differs from its current folder's `YYYY-MM-DD` name is moved to a sibling folder named for its real date, creating that folder if needed.

### Phase 6 — Sync file-system timestamps (optional)
`python scripts/organize.py --root "<PhotoRoot>" --sync-timestamps`. Sets each file's "Date Modified" and "Date Created" to its EXIF Date Taken, **but only for files that look unedited**. An "unedited" file is one whose EXIF `DateTime` tag (file-level modify time) equals `DateTimeOriginal` (or is missing) AND whose EXIF `Software` tag does not match a known editor (Photoshop, Lightroom, Camera Raw, GIMP, Affinity, Luminar, Pixelmator, Snapseed, VSCO, Instagram). Files that fail the check are skipped and listed — neither timestamp is touched. "Date Created" is set through the Win32 `SetFileTime` API, so on non-Windows systems only "Date Modified" is synced (reported as `created-unsupported`).

### Phase 7 — Flatten into the root folder (optional)
`python scripts/organize.py --root "<PhotoRoot>" --flatten`. Moves every file that has a Date Taken up one level, out of its `YYYY-MM-DD` subfolder and into `<PhotoRoot>` itself, then deletes the subfolders left empty. Preview first with `--flatten --dry-run`, which lists every move and folder removal without touching anything.
- Files with no Date Taken are left where they are — the folder name may be the only record of their date — so their folders are kept.
- Folders that still hold anything else (undated files, non-media files) are kept.
- If a name is already taken in the root (e.g. two days each have an `IMG_0001.JPG`), the incoming file gets a `_<date-taken>` suffix; if that is taken too, it is skipped and reported.

Run this last: once files are in the root, the other phases no longer see them (they only look inside subfolders).

### Quarantine ad images (optional, any time)
`python scripts/organize.py --root "<PhotoRoot>" --quarantine-ads`. Moves ad images out of `<PhotoRoot>` and every subfolder into `<PhotoRoot>/_ads`, keeping their subfolder path, so the user can look through them and delete the folder themselves. Nothing is deleted. Preview first with `--quarantine-ads --dry-run`. A file is treated as an ad only when both hold:
1. The whole filename stem is one of:
   - a UUID, e.g. `0c4cda27-b4cc-4e92-a446-d6b780f24a64`
   - a 9-character hex id plus a number, e.g. `bed51b94a_1595`
   - `gmsnet` plus an optional number, e.g. `gmsnet2`
2. It carries no camera Make/Model (EXIF for images, the device-make tag for video).

Name matches that do have camera info are real photos; they are kept and listed as `KEPT`. Share those and the quarantined count with the user.

Best run before Phase 3 so ads are not dated and moved with the real photos. The other phases ignore `_ads`. Emptied folders are left for Phase 7 or the cleanup script.

### Move files with no image data (optional, any time)
`python scripts/organize.py --root "<PhotoRoot>" --move-no-data`. Moves media files that are 0 bytes, or contain nothing but null bytes (the remains of a failed copy or phone transfer), out of `<PhotoRoot>` and every subfolder into `<PhotoRoot>/_no-image-data`, keeping their subfolder path. Nothing is deleted. Preview first with `--move-no-data --dry-run`. The other phases ignore `_no-image-data`. These files cannot be repaired; the names tell the user what to re-copy from the phone or a backup.

### Delete AAE sidecars (optional, any time; part of `--all`)
`python scripts/organize.py --root "<PhotoRoot>" --delete-aae`. Permanently deletes every `.AAE` file in `<PhotoRoot>` and every subfolder. These are the edit-instruction sidecars an iPhone exports next to a photo (`IMG_1234.AAE`); they contain no image and nothing on Windows reads them. Preview first with `--delete-aae --dry-run`. This is a real delete, not a move — confirm with the user before running it or `--all`.

### Cleanup
Remind the user to run `scripts/Cleanup-Pictures.ps1 -Path "<PhotoRoot>"` at the end. It removes duplicate base-name files (keeps the preferred format: HEIC > JPG > MOV > … > PNG) and empty folders.

## Output

Every scan writes `photo-audit.xlsx` to the root folder with Summary, Plan, and Only-moves sheets. End the response with:

1. A short summary of counts (extensions corrected, dates written, files converted, files moved, timestamps synced, files flattened and folders removed, ad images quarantined, no-data files moved).
2. A reminder to run `.\Cleanup-Pictures.ps1` from `<PhotoRoot>` (and any extra PowerShell for leftovers the sandbox could not delete).
3. A link to the audit XLSX.

## Safety rails

- Ask before each phase that writes, moves, or deletes.
- Preview with `--report-only` or `-WhatIf` on first contact with an unfamiliar folder.
- Never rename or move files outside `<PhotoRoot>`.
- When converting PNG → JPEG, never delete the original PNG in the same step — leave removal to `Cleanup-Pictures.ps1` so the user sees it.
- Date-writing is destructive to EXIF; back up before Phase 3 on precious photo libraries.
- `--delete-aae` (and so `--all`) permanently deletes `.AAE` sidecars; it is the only phase of `organize.py` that deletes files.
- Files with no image data are moved to `_no-image-data`, never deleted.
- Ad images are quarantined in `_ads`, never deleted. Deleting that folder is the user's call after they have looked through it.
- Timestamp sync only touches files that pass the unedited-heuristic. Edited files are skipped and reported, never silently overwritten.
