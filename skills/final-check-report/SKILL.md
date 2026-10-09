---
name: final-check-report
description: Use this skill when the user wants a last look at what is left over after their photos and videos have been organized. Triggers include "run the final check," "final check report," "what's left behind," "what still needs cleaning up," "are my year folders clean," "anything left in _ads or _incomplete," "which folders didn't get flattened," or "what audit files are lying around." It reports, for each year folder, files still sitting in _ads, files still in _incomplete, photos filed among videos (or videos among photos), subfolders that were not flattened, name collisions (each pair, identical or different), and audit workbooks left behind. Its only change is renaming audit workbooks so each carries its folder name and media type; no photo or video is moved, renamed or deleted. Do NOT use to fix dates or move files — that is the media-date-organizer skill.
---

# final-check-report

Reports the oddities left behind once the media-date-organizer phases have run, and records the report in the audit workbook.

## Required inputs

- `MediaRoot`: the folder that **holds the year folders** (`D:\Videos`, `D:\Pictures`), not one year. Ask once if not given. To check photos and videos both, run it once for each.

## How to run

1. **Preview.** `python skills/media-date-organizer/scripts/organize.py --root "<MediaRoot>" --final-check --dry-run`. Changes nothing. This is the full report; the only difference from a real run is that audit workbooks are listed as `WOULD RENAME` and left alone.

2. **Run.** If the preview lists any `WOULD RENAME AUDIT FILE` lines, tell the user which workbooks will be renamed, and after they confirm run it without `--dry-run`. If it lists none, the preview is the report and there is nothing more to run.

The script lives in the media-date-organizer skill and needs the same packages (`pip install pillow openpyxl`).

## What it reports

Every folder in `<MediaRoot>` whose name starts with a year (`2014`, `2013 West`) is checked. Other folders in `<MediaRoot>`, and media files loose in it, are not looked at. If there are no year folders, `<MediaRoot>` itself is reported as one folder.

- **Files in `_ads`** — `IN ADS: 2014/_ads (120 file(s))`. Ads `--quarantine-ads` set aside that the user has not yet reviewed and deleted. Counted as `ads-files`.
- **Files in `_incomplete`** — `INCOMPLETE: 2014/_incomplete (4 file(s))`. Empty or broken files `--move-incomplete` set aside (an older `_no-image-data` folder counts too). Counted as `incomplete-files`.
- **Opposite-type files** — `PHOTO IN VIDEO FOLDER: 2016/DSC00323.JPG` or `VIDEO IN PHOTO FOLDER: ...`, one line per file. Whichever kind `<MediaRoot>` holds more of decides what it is; `_ads` and `_incomplete` are not counted. A file's kind goes by its extension. Counted as `photos-in-video-folders` or `videos-in-photo-folders`.
- **Folders not flattened** — `NOT FLATTENED: 2014/7-17-2014 (3 file(s))`. Each subfolder still inside a year folder, with how many files it holds at any depth. `--flatten` leaves a folder when it holds undated files, name collisions or non-media files. Counted as `folders-not-flattened`.
- **Collisions** — one line per pair of files that share a name, saying whether the two are the same file and how `--flatten` handled the clash:
  - `COLLISION, identical files (renamed with a date): 2014/IMG_1_2014-07-17.jpg | 2014/IMG_1.jpg` — the name was taken in the year folder, so the incoming file got a `_<date>` suffix.
  - `COLLISION, different files (left in its subfolder): 2014/7-17-2014/IMG_1.jpg | 2014/IMG_1.jpg` — the suffixed name was taken as well, so the file stayed where it was.

  `identical` means byte for byte the same, a true duplicate; `different` means the two only share a name. Counted as `collisions`, `collisions-identical` and `collisions-different`. Only these name clashes are found; the ones `--apply-moves` skips between dated folders need every file's date read, so use `--compare-collisions` on that year folder for those.
- **Audit workbooks** — `AUDIT FILE: 2014/2014_videos_media_audit_2026-10-07.xlsx`. Every `*media_audit*.xlsx` in a year folder (at any depth) or loose in `<MediaRoot>`, except the workbook this run is recorded in. Counted as `audit-files`.

It ends with one line per year folder (`2014: 120 in _ads, 4 in _incomplete, 0 photo(s) among videos, 3 folder(s) not flattened, 2 collision(s), 1 audit file(s)`, or `2015: clean`) and a `FINAL CHECK` total line.

## The one change it makes

An audit workbook whose name does not start with its folder's name and media type is renamed so that it does: `2014/media_audit_2026-10-07.xlsx` becomes `2014_videos_media_audit_2026-10-07.xlsx`. Workbooks from different folders can then be told apart, and gathered in one place without their names clashing.

- The prefix is the name of the folder the workbook sits in, then `photos` or `videos`, whichever kind that folder holds more of. A folder with no media gets the folder name alone.
- Listed as `RENAMED AUDIT FILE: <old> -> <new>` (`WOULD RENAME` in a dry run), counted as `audit-files-renamed`.
- If the new name is already taken the workbook is left and reported as `COLLISION, not renaming` (counted as `audit-files-not-renamed`). A workbook open in Excel cannot be renamed and is reported as `FAILED to rename`.
- New workbooks already get this name from every phase, so only ones written by earlier versions need renaming.

## Deliverables

1. A short summary: the six totals (collisions split into identical and different) and how many year folders have something left.
2. A table of the year folders that are not clean, one row each, with the six counts.
3. For short lists, the files and folders themselves; for long ones, point to the Run log sheet of the audit workbook, where the run is recorded in full.
4. The audit workbook: `<MediaRoot folder name>_<photos|videos>_media_audit_<date>.xlsx` in `<MediaRoot>` (`Videos_videos_media_audit_2026-10-09.xlsx`). The run, and the dry run, are appended to its Run log and Run counts sheets. It must be closed in Excel while the check runs, or the run is not recorded.

## What to suggest next

Suggest, do not do; each of these changes files and needs the user's go-ahead.

- `_ads` files: the user reviews and deletes them by hand.
- `_incomplete` files: the user re-copies them from the original source, or deletes them.
- Opposite-type files: the user moves them to the matching year folder under the other root.
- Folders not flattened: run `--flatten --dry-run` on that year folder to see why each file was left (`LEFT`, `COLLISION`), then `--fill-blanks` or `--compare-collisions` as the reason calls for.
- Collisions: an `identical` pair is a duplicate, so one of the two can be deleted (the user's call which). For a `different` pair, `--visual-compare --dry-run` on that year folder says whether they are the same picture saved twice or two unrelated files.
- Audit workbooks: once the user no longer needs the history, they can gather them into one folder or delete them.
