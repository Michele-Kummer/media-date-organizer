---
name: media-date-organizer
description: Use this skill when the user wants every photo and video in a folder to have a readable Date Taken (Media Created for video). Triggers include "fix the dates on my photos," "make sure all my pictures have Date Taken," "my photos don't show Date Taken in Explorer," "convert these PNGs so I can see the date," "sort my photos and videos by when they were taken," "my videos have no Media Created date," or any mention of blank/missing/wrong Date Taken on photo or video files. The skill reads real EXIF and container metadata (HEIC/HEIF, MOV/MP4, PNG/JPEG) without external tools, writes Date Taken where it is missing, converts PNG to JPEG when the user needs Windows Explorer to surface the date, moves files to date-matched folders, optionally syncs Windows file timestamps to Date Taken for unedited files, and produces an XLSX audit. Works on photos and videos from any source. Do NOT use for RAW camera files or video libraries larger than a few thousand items — the sandbox parse would be slow.
---

# media-date-organizer

Ensures every photo and video has a Date Taken (Media Created for video). Seven phases, each independently runnable.

## Prerequisites

The scripts rely on two Python packages: `Pillow` (image handling + EXIF) and `openpyxl` (audit workbook). On first run in a fresh Python environment, install both before invoking any phase:

```bash
pip install -r requirements.txt
# or:
pip install pillow openpyxl
```

Scanning still works without `openpyxl` — only the XLSX report is skipped. Writing EXIF or converting PNG requires `Pillow`.

## When to run

- The user has a folder of photos and videos and wants Date Taken populated everywhere.
- Dates are showing blank in Windows Explorer for some files (PNG screenshots especially).
- Files have the wrong extension or are in a wrong folder relative to their real date.
- The user wants an audit of which files have Date Taken and which don't.
- The user wants Explorer's "Date Modified" and "Date Created" to reflect the real capture time on untouched files.

## Required inputs

- `MediaRoot`: the folder to process. Ask once if not given.
- Confirmation before each destructive step (write EXIF, rename, move, convert, delete, timestamp sync).

## Workflow

Each phase below can be run on its own, or several can be given on one command line. `python scripts/organize.py --root "<MediaRoot>" --all` deletes `.AAE` sidecars, moves incomplete files into `_incomplete` and then runs Phases 3–6 (`--delete-junk --move-incomplete --fill-blanks --convert-png --apply-moves --sync-timestamps`); add `--quarantine-ads` or `--flatten` to include those. Phases always run in this order whatever order the flags are typed in: delete-junk, move-incomplete, quarantine-ads, fill-blanks, convert-png, apply-moves, sync-timestamps, flatten. A multi-phase run ends with a `Summary of this run` block listing every phase's counts and the problem lines (`FAILED`, `SKIPPED`, `COLLISION`, `NOTE`) it reported, up to 50 per phase. Use it only after the user has confirmed every phase it includes; `--report-only` cannot be combined with other phases.

### Phase 1 — Fix extensions
`scripts/Fix-Extensions.ps1 -Path "<MediaRoot>"`. Reads magic bytes and renames files whose extensions lie about the actual format. Preview with `-WhatIf` first. 3GP/3G2 videos keep their own extension (they are not renamed to `.mp4`). AVCHD camcorder files (`.m2ts`/`.mts`) are recognised and left as they are; `organize.py` never dates or converts them, and only `--flatten` moves them. Empty (0-byte) files are listed as `EMPTY` and left alone; `UNKNOWN` means a non-empty file in a format the script does not recognise.

### Phase 2 — Scan metadata
`python scripts/organize.py --root "<MediaRoot>" --report-only`. Reads Date Taken from the real format of each file:
- HEIC/HEIF → embedded TIFF/EXIF `DateTimeOriginal`
- MOV/MP4/M4V/3GP/3G2 → `mvhd` atom `creation_time` (Explorer's "Media created"), converted from UTC to local time
- PNG/JPEG/TIFF → standard EXIF via Pillow

Writes `media_audit_<date>.xlsx` summarizing which files have Date Taken, which don't, and which are in a folder that doesn't match their date. Share the summary with the user before Phase 3.

### Phase 3 — Write Date Taken where it's missing
`python scripts/organize.py --root "<MediaRoot>" --fill-blanks`. For every file whose Date Taken is blank:
- If the filename contains a date (e.g. Snapchat exports `2023-12-20_<id>-main.jpg`, or `IMG_20231220_142355.jpg`), write that as `DateTimeOriginal` (JPEG, PNG, TIFF), using the time from the name if present, else `12:00:00`.
- Otherwise, if the containing folder is named `YYYY-MM-DD`, write `DateTimeOriginal = <folder-date> 12:00:00`.
- The file's modified time is never used as a source — it usually reflects the import, not the capture.
- JPEGs get the EXIF segment swapped in place; the image data is not re-encoded.
- HEIC/MOV files are written with `exiftool` when it is installed (on PATH, or in winget's default folder). Without it they are flagged as `SKIPPED (needs exiftool)` — offer to install it (`winget install --id OliverBetz.ExifTool -e --source winget`), or convert HEIC → JPEG in Phase 4.
- Videos (MOV/MP4/M4V/3GP/3G2) whose Media Created is blank are found in `<MediaRoot>` and every subfolder at any depth (photos are only looked at one level down). Media Created is written with `exiftool`, from the first of:
  1. a date in the filename (e.g. `WP_20131115_002.mp4`, `20190630_090136.mp4`), with its time if present, else `12:00:00`;
  2. the nearest containing folder whose name holds a full date (`2019-08-30`, `11-11-2019`), at `12:00:00`.

  A folder name holding only a year (`2014`, `2013 West`) is never used. Videos with neither source are listed as `SKIPPED (no date in filename or folder names)`; share that list with the user. The time is treated as local time and stored as UTC, so Explorer's Media Created column shows it unchanged. AVI and MPG files are not handled.
- Preview with `--fill-blanks --dry-run`, which lists every date that would be written without touching anything.
- Empty (0-byte) files are skipped and reported as one `NOTE:` count. GIF/BMP/WEBP have no Date Taken field and are counted as `unsupported-format`. If the count of empty files is large, suggest `--move-incomplete` (below).

### Phase 4 — Convert formats Windows can't read Date Taken from
`python scripts/organize.py --root "<MediaRoot>" --convert-png`. Converts PNG files to JPEG at quality 95, preserving EXIF, so Windows Explorer surfaces Date Taken. Only run after confirming with the user — JPEG is lossy and the original PNG is left in place for the cleanup script to remove. PNGs with any transparent pixels are never converted (JPEG has no transparency) and are counted as `skipped-transparent`; they stay PNG. PNGs named `*-overlay.png` (Snapchat's transparent caption layers) are skipped too.

### Phase 5 — Move to date-matched folders
`python scripts/organize.py --root "<MediaRoot>" --apply-moves`. Any file whose Date Taken differs from its current folder's `YYYY-MM-DD` name is moved to a sibling folder named for its real date, creating that folder if needed.

### Phase 6 — Sync file-system timestamps (optional)
`python scripts/organize.py --root "<MediaRoot>" --sync-timestamps`. Sets each file's "Date Modified" and "Date Created" to its EXIF Date Taken, **but only for files that look unedited**. An "unedited" file is one whose EXIF `DateTime` tag (file-level modify time) equals `DateTimeOriginal` (or is missing) AND whose EXIF `Software` tag does not match a known editor (Photoshop, Lightroom, Camera Raw, GIMP, Affinity, Luminar, Pixelmator, Snapseed, VSCO, Instagram). Files that fail the check are skipped and listed — neither timestamp is touched. "Date Created" is set through the Win32 `SetFileTime` API, so on non-Windows systems only "Date Modified" is synced (reported as `created-unsupported`).

### Phase 7 — Flatten into the root folder (optional)
`python scripts/organize.py --root "<MediaRoot>" --flatten`. Moves every file that has a Date Taken up one level, out of its `YYYY-MM-DD` subfolder and into `<MediaRoot>` itself, then deletes the subfolders left empty. Preview first with `--flatten --dry-run`, which lists every move and folder removal without touching anything.
- Files with no Date Taken are left where they are — the folder name may be the only record of their date — so their folders are kept.
- Exception: inside `<MediaRoot>/_ads`, every file moves up from its subfolder into `_ads` itself whether or not it has a Date Taken (ads rarely do), counted as `ads-moved`. A name already taken in `_ads` gets a `_<subfolder-name>` suffix, which keeps the date the ad was filed under.
- Camcorder videos (`.m2ts`, `.mts`) are flattened too, going by the date in the filename (`20180116122434.m2ts`), since their internal date is not read. One with no date in its name is `LEFT (no date in filename)`; one that is empty or all null bytes is `LEFT (no video data)`.
- Sony sidecar files named `<file name>.modd` / `<file name>.moff` (usually hidden) move with their file and take its new name if it was renamed; counted as `sidecars-moved`. The user has Sony's software, so sidecars are kept wherever their file is.
- A `.modd`/`.moff` in `<MediaRoot>` or one of its subfolders whose file is not beside it is permanently deleted (`DELETED (sidecar with no file)`, counted as `orphan-sidecars-deleted`). `_ads` and `_incomplete` are not touched. This is a real delete: show the `--dry-run` list and confirm first.
- Folders that still hold anything else (undated files, non-media files) are kept.
- If a name is already taken in the root (e.g. two days each have an `IMG_0001.JPG`), the incoming file gets a `_<date-taken>` suffix; if that is taken too, it is skipped and reported.

Run this last: once files are in the root, the other phases no longer see them (they only look inside subfolders).

### Quarantine ad images and videos (optional, any time)
`python scripts/organize.py --root "<MediaRoot>" --quarantine-ads`. Moves ad images and videos out of `<MediaRoot>` and every subfolder into `<MediaRoot>/_ads`, keeping their subfolder path, so the user can look through them and delete the folder themselves. Nothing is deleted. Preview first with `--quarantine-ads --dry-run`. A file is treated as an ad only when both hold:
1. The whole filename stem is one of:
   - a UUID, e.g. `0c4cda27-b4cc-4e92-a446-d6b780f24a64`
   - a 9-character hex id plus a number, e.g. `bed51b94a_1595`
   - `gmsnet` plus an optional number, e.g. `gmsnet2`
   - `news_images%2F` plus a number, e.g. `news_images%2F1714658759372`
   - `UnityAdsCache-` plus a 64-character hex hash, e.g. `UnityAdsCache-3d4c8e33a716c48d4cf7daad6049cb87960c0ef042c3c6014d7ba81eb18d2091`
   - a name that contains pixel dimensions and ends in `___` plus a 6-character id, e.g. `Update_Now_Video_V2_720x1280_15s___fudxlv`, `720x1280_ENDCARD___fo9w1l`
   - for videos only: 20 lowercase letters and digits with at least one letter, e.g. `32129eda9b8e718c5277`, `vuyyzy0brvod5gcaocnv`, `agqnsutqkbwulksalejd`
   - for videos only: a 32-character lowercase hex hash, e.g. `d5a210d011c47b8300bb8034048719a9`
   - for videos only: a name ending `-<width>x<height>-Q2` or `-<width>x<height>-h264-Q2`, e.g. `313e81d7e1f03f326004da8f41daa11f.mp4-720x1280-h264-Q2`, `peacock_hand_4pics_fantasy_cute_45sec_1080x1920_rev-720x1280-Q2`

   Each may be followed by the `_YYYY-MM-DD` suffix `--flatten` adds, or a ` (2)` copy marker.
2. It carries no camera Make/Model (EXIF for images, the device-make tag for video).

Name matches that do have camera info are real photos or videos; they are kept and listed as `KEPT`. Share those and the quarantined count with the user.

Best run before Phase 3 so ads are not dated and moved with the real photos and videos. The other phases ignore `_ads`, except Phase 7, which flattens the subfolders inside it. Emptied folders are left for Phase 7 or the cleanup script.

### Move incomplete files (any time; part of `--all`)
`python scripts/organize.py --root "<MediaRoot>" --move-incomplete`. Moves incomplete media files out of `<MediaRoot>` and every subfolder into `<MediaRoot>/_incomplete`, keeping their subfolder path, so each file stays in its dated folder (`_incomplete/2018-08-19/clip.mp4`). A file is incomplete when it is 0 bytes (`empty`), contains nothing but null bytes (`null-filled`), or is a video with no video header (`no-video-header`: a stub of a few bytes or a truncated copy that no player can open). These are the remains of a failed copy or phone transfer. Nothing is deleted. Preview first with `--move-incomplete --dry-run`. The other phases ignore `_incomplete`, and `--flatten` never empties it. A `_no-image-data` folder left by an earlier version is folded into `_incomplete`; `--move-no-data` still works as the old name of the flag. These files cannot be repaired; the names tell the user what to re-copy from the phone or a backup.

### Delete junk files (optional, any time; part of `--all`)
`python scripts/organize.py --root "<MediaRoot>" --delete-junk`. Permanently deletes every `.AAE` file and every Windows thumbnail cache (`Thumbs.db`, `ehthumbs.db`, `ehthumbs_vista.db`, hidden or not; counted as `deleted-thumbs`) in `<MediaRoot>` and every subfolder, `_ads` and `_incomplete` included. Thumbnail caches are matched by whole file name only, so a photo such as `west sucking thumb.jpg` is never touched. These are the edit-instruction sidecars an iPhone exports next to a photo (`IMG_1234.AAE`); they contain no image and nothing on Windows reads them. Preview first with `--delete-junk --dry-run`. This is a real delete, not a move — confirm with the user before running it or `--all`.

### Cleanup
Remind the user to run `scripts/Cleanup-Pictures.ps1 -Path "<MediaRoot>"` at the end. It removes duplicate base-name files (keeps the preferred format: HEIC > JPG > MOV > … > PNG) and empty folders.

## Output

Everything writes to one audit workbook per day, `media_audit_<date>.xlsx` in the root folder, where `<date>` is the day of the run (`media_audit_2026-10-07.xlsx`). Runs on the same day share a workbook; the first run on a new day starts a new one, and earlier days' workbooks are left as they are.

- Every scan (`--report-only`, `--apply-moves`) rebuilds the Summary, Plan and Only-moves sheets.
- Every run of every phase of `organize.py`, and every run of `Fix-Extensions.ps1` and `Cleanup-Pictures.ps1`, appends to two history sheets that are never cleared: **Run log** (one row per reported line: run time, phase, dry run yes/no, action such as `MOVED`, `WROTE`, `DELETED`, `FAILED`, and the detail) and **Run counts** (each phase's counts). Dry runs and `-WhatIf` previews are recorded too, marked `yes` in the Dry run column.
- The PowerShell scripts record through `Write-AuditLog.ps1`, which needs Python with `openpyxl`.
- If the workbook is open in Excel the run still happens but cannot be recorded; the output says `This run is NOT recorded in the audit workbook`. Tell the user to close it before the next phase.

End the response with:

1. A short summary of counts (extensions corrected, dates written, files converted, files moved, timestamps synced, files flattened and folders removed, ad files quarantined, incomplete files moved).
2. A reminder to run `.\Cleanup-Pictures.ps1` from `<MediaRoot>` (and any extra PowerShell for leftovers the sandbox could not delete).
3. A link to the audit XLSX.

## Safety rails

- Ask before each phase that writes, moves, or deletes.
- Preview with `--report-only` or `-WhatIf` on first contact with an unfamiliar folder.
- Never rename or move files outside `<MediaRoot>`.
- When converting PNG → JPEG, never delete the original PNG in the same step — leave removal to `Cleanup-Pictures.ps1` so the user sees it.
- Date-writing is destructive to EXIF; back up before Phase 3 on precious photo and video libraries.
- `--delete-junk` (and so `--all`) permanently deletes `.AAE` sidecars and `Thumbs.db` thumbnail caches; the only other deletion `organize.py` makes is `--flatten` removing `.modd`/`.moff` sidecars whose file is gone.
- Incomplete files are moved to `_incomplete` in their dated folders, never deleted.
- Ad images and videos are quarantined in `_ads`, never deleted. Deleting that folder is the user's call after they have looked through it.
- Timestamp sync only touches files that pass the unedited-heuristic. Edited files are skipped and reported, never silently overwritten.
