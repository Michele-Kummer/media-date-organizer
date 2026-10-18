---
name: find-duplicates
description: Use this skill when the user wants to find duplicate photos or videos in a folder. Triggers include "find duplicates," "find duplicate photos," "which files are copies," "do I have the same picture twice," "find identical files," "find near duplicates," "how much space are duplicates taking," or "check this folder for duplicate videos." It searches a folder at every depth and reports files that are byte-for-byte identical, plus pairs that are likely the same picture or recording saved twice (a re-saved, resized or re-tagged copy), each with a confidence level. It only reports - no photo or video is moved, renamed or deleted. Do NOT use to fix dates or move files (that is the media-date-organizer skill), or to check what is left after organizing (that is the final-check-report skill).
---

# find-duplicates

Reports photos and videos that are the same file twice, or likely the same picture or recording, and records the report in the audit workbook. It runs on its own: none of the media-date-organizer phases need to have run first.

## Required inputs

- `MediaRoot`: the folder to search. Either one year (`D:\Pictures\2012`) or the folder that holds the year folders (`D:\Pictures`), which also finds copies filed under different years. Ask once if not given.

## How to run

`python skills/find-duplicates/scripts/find_duplicates.py --root "<MediaRoot>"`

Nothing is changed, so no confirmation is needed. The script borrows its date reading and picture comparing from the media-date-organizer skill's `organize.py`, so that skill must sit beside this one, and it needs the same packages (`pip install pillow openpyxl`). Comparing videos also needs ffmpeg (`pip install imageio-ffmpeg`).

A whole `D:\Pictures` can take a while: every file's date is read, and files that share a size are read in full.

## What it looks at

- Every photo and video under `<MediaRoot>`, at any depth, including older camcorder video (AVI, MPG, WMV, M2TS).
- `_ads` and `_incomplete` folders are left out. Empty (0-byte) files are counted as `empty-file` and skipped.

## What it reports

Three kinds of line, surest first:

- **`IDENTICAL (confidence certain, byte for byte): <copy> | <first>`** - the two files hold exactly the same bytes. A true duplicate: one of the two can go with nothing lost. `<first>` is the file nearest `<MediaRoot>`; three copies of one file give two lines, each against the same `<first>`. Counted as `identical-copies` (the extra copies), `identical-groups`, and `identical-copies-bytes` (the space the extra copies take).
- **`DUPLICATE (confidence high|medium): <file> | <file> - <why>`** - different bytes, but the pictures look the same: a copy that was re-saved, resized, re-compressed or had its metadata rewritten. Counted as `duplicate-high` and `duplicate-medium`.
- **`POSSIBLE (confidence low): <file> | <file> - <why>`** - worth a look. Either the pictures are close but not clearly the same (`possible-low`), or they could not be compared, with the reason given (`possible-not-compared`): a HEIC file Pillow cannot open, or a video when ffmpeg is not installed.

`<why>` says what the two files have in common and what the comparison found, e.g. `same Date Taken 2012-06-01 10:00:00, same name; pixel difference 0.4%, sizes 4000x3000 vs 1600x1200`.

It ends with a `DUPLICATES` total line: files checked, identical copies and the space they take, likely pairs and possible pairs.

### Which files are compared

Comparing every file with every other would take hours, so only files with something in common are compared by their pixels. Two files of the same kind (two photos, or two videos) are compared when they share any of:

- the same Date Taken (photos) or Media Created (videos), to the second;
- the same name, ignoring the extension and copy endings: ` (1)`, ` - Copy`, and the `_YYYY-MM-DD` ending `--flatten` adds;
- the same size in bytes.

Pairs that turn out to be different pictures are counted as `alike-but-different` and not listed: burst shots taken in the same second, or two cameras that both used `IMG_0001`.

Photos are compared as whole pictures; videos by four frames and their length. The thresholds are the ones `--visual-compare` uses.

### What it can miss, and what to check by eye

- A copy with a different name, a different or missing date, and a different size is not found, because nothing puts the two files side by side.
- A rotated or cropped copy is judged different.
- Burst shots from a camera held still can look the same at the size compared, so a `DUPLICATE` pair whose only link is the date, with two consecutive camera names (`IMG_0101.jpg | IMG_0102.jpg`), may be two real shots. `same name` in `<why>` is the stronger sign of a copy.

## Deliverables

1. A short summary: files checked, identical copies with the space they take, likely duplicate pairs, possible pairs.
2. For short lists, the pairs themselves, grouped by kind of line; for long ones, point to the Run log sheet of the audit workbook, where the run is recorded in full with a Confidence column to filter on.
3. The audit workbook: `<MediaRoot folder name>_<photos|videos>_media_audit_<date>.xlsx` in `<MediaRoot>`, the same workbook the media-date-organizer phases write to. The run is appended to its Run log and Run counts sheets as phase `find_duplicates`. It must be closed in Excel while the script runs, or the run is not recorded.

## What to suggest next

Suggest, do not do; deleting is the user's call and needs their go-ahead for the specific files.

- `IDENTICAL` pairs: one of the two can be deleted. Ask which copy to keep when they sit in different folders (usually the one in the better-named folder).
- `DUPLICATE` pairs: the user looks at both and keeps the better one, normally the larger picture or the one that still has its Date Taken.
- `POSSIBLE` pairs: the user looks at both. For videos listed as not compared, install ffmpeg and run again.
