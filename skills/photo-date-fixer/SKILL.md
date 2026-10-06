---
name: photo-date-fixer
description: Use this skill when the user wants every photo in a folder to have a readable Date Taken. Triggers include "fix the dates on my photos," "make sure all my pictures have Date Taken," "my photos don't show Date Taken in Explorer," "convert these PNGs so I can see the date," "sort my photos by when they were taken," or any mention of blank/missing/wrong Date Taken on image files. The skill reads real EXIF and container metadata (HEIC/HEIF, MOV/MP4, PNG/JPEG) without external tools, writes Date Taken where it is missing, converts PNG to JPEG when the user needs Windows Explorer to surface the date, moves files to date-matched folders, optionally syncs Windows file timestamps to Date Taken for unedited files, and produces an XLSX audit. Works on photos from any source. Do NOT use for RAW camera files or video libraries larger than a few thousand items — the sandbox parse would be slow.
---

# photo-date-fixer

Ensures every photo has a Date Taken. Six phases, each independently runnable.

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
- If the containing folder is named `YYYY-MM-DD`, write `DateTimeOriginal = <folder-date> 12:00:00` into the file's EXIF (JPEG, PNG, TIFF).
- HEIC/MOV files without existing EXIF are flagged — writing new EXIF into those containers reliably needs `exiftool`. Offer to install it, or convert HEIC → JPEG in Phase 4.

### Phase 4 — Convert formats Windows can't read Date Taken from
`python scripts/organize.py --root "<PhotoRoot>" --convert-png`. Converts PNG files to JPEG at quality 95, preserving EXIF, so Windows Explorer surfaces Date Taken. Only run after confirming with the user — JPEG is lossy and the original PNG is left in place for the cleanup script to remove.

### Phase 5 — Move to date-matched folders
`python scripts/organize.py --root "<PhotoRoot>" --apply-moves`. Any file whose Date Taken differs from its current folder's `YYYY-MM-DD` name is moved to a sibling folder named for its real date, creating that folder if needed.

### Phase 6 — Sync file-system timestamps (optional)
`python scripts/organize.py --root "<PhotoRoot>" --sync-timestamps`. Sets each file's "Date Modified" and "Date Created" to its EXIF Date Taken, **but only for files that look unedited**. An "unedited" file is one whose EXIF `DateTime` tag (file-level modify time) equals `DateTimeOriginal` (or is missing) AND whose EXIF `Software` tag does not match a known editor (Photoshop, Lightroom, Camera Raw, GIMP, Affinity, Luminar, Pixelmator, Snapseed, VSCO, Instagram). Files that fail the check are skipped and listed — neither timestamp is touched. "Date Created" is set through the Win32 `SetFileTime` API, so on non-Windows systems only "Date Modified" is synced (reported as `created-unsupported`).

### Cleanup
Remind the user to run `scripts/Cleanup-Pictures.ps1 -Path "<PhotoRoot>"` at the end. It removes duplicate base-name files (keeps the preferred format: HEIC > JPG > MOV > … > PNG) and empty folders.

## Output

Every scan writes `photo-audit.xlsx` to the root folder with Summary, Plan, and Only-moves sheets. End the response with:

1. A short summary of counts (extensions corrected, dates written, files converted, files moved, timestamps synced).
2. A reminder to run `.\Cleanup-Pictures.ps1` from `<PhotoRoot>` (and any extra PowerShell for leftovers the sandbox could not delete).
3. A link to the audit XLSX.

## Safety rails

- Ask before each phase that writes, moves, or deletes.
- Preview with `--report-only` or `-WhatIf` on first contact with an unfamiliar folder.
- Never rename or move files outside `<PhotoRoot>`.
- When converting PNG → JPEG, never delete the original PNG in the same step — leave removal to `Cleanup-Pictures.ps1` so the user sees it.
- Date-writing is destructive to EXIF; back up before Phase 3 on precious photo libraries.
- Timestamp sync only touches files that pass the unedited-heuristic. Edited files are skipped and reported, never silently overwritten.
