---
description: Move every dated photo and video up out of its subfolder into the media folder itself, then move the subfolders left empty into _empty_folders. Previews only; add --apply to make the changes.
argument-hint: <path-to-media-folder> [--apply]
---

# /flatten-media

Move the dated photos and videos in the media folder up one level, out of their subfolders, and set aside the folders that end up empty.

## Dry run or apply

`$ARGUMENTS` is the media folder, optionally followed by `--apply`. Below, `<folder>` means that folder without `--apply`.

- **Without `--apply`, this is a dry run.** Run `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --flatten`. Nothing is changed. Share the counts and any `LEFT`, `COLLISION`, `WOULD MOVE (sidecar with no file)` or renamed lines with the user, then end with: to make these changes, type `/flatten-media <folder> --apply`.
- **With `--apply`**, run `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --flatten --apply`.

## What it does

- Every file one level down that has a Date Taken moves into `<folder>` itself.
- Files with no Date Taken stay where they are, so their folders are kept. Run `/fix-media-dates` first if the user wants those dated and moved too.
- Exception: inside `<folder>/_ads`, every file in a subfolder at any depth (`_ads/Temp/2020-01-06/ad.png`, as `--quarantine-ads` files them) moves up into `_ads` itself, with or without a Date Taken. Game `.raw` ads move too. A name already taken there gets a `_<subfolder-name>` suffix. The same happens when `<folder>` is itself an `_ads` folder (`E:\Pictures\2020\_ads`); its emptied subfolders go into the `_empty_folders` beside it.
- Camcorder videos (`.m2ts`, `.mts`) and older MPEG, Windows Media and AVI videos (`.mpg`, `.mpeg`, `.wmv`, `.avi`) move up as well, going by the date in the filename. One with no date in its name goes by the date in its subfolder's name and has that date appended (`7-17-2014/SDC13837.AVI` → `SDC13837_2014-07-17.AVI`). Ones with neither, or holding no data, stay.
- Sony `.modd`/`.moff` sidecar files move with the file they belong to. A sidecar whose file is not beside it is moved into `<folder>/_junk`, keeping its path, not deleted; the dry run lists these as `WOULD MOVE (sidecar with no file)`.
- A name already taken in the root gets a `_<date-taken>` suffix; if that is taken as well, the file is skipped and reported.
- Subfolders left empty are moved into `_empty_folders` inside the media folder, keeping their path, instead of being deleted (a path already there gets a ` (2)` ending). Folders still holding anything are kept. The user can delete `_empty_folders` once they have looked at it.
- It ends with an `OPPOSITE TYPE` line saying how many files of the less common kind `<folder>` itself holds once flattened (videos in a photo folder, or photos in a video folder). Tell the user that number.

## Deliverables

- The run (and the dry run) is recorded in the Run log and Run counts sheets of the audit workbook (`<folder name>_<photos|videos>_media_audit_<date>.xlsx`) at the root of `<folder>`.
- Summary message with counts (moved, ads moved, sidecars moved, orphan sidecars moved to `_junk`, renamed, left undated, empty folders moved, folders kept, videos in photo folder or photos in video folder), saying "would" for a dry run.
- After a dry run: the line `/flatten-media <folder> --apply` for the user to type.
