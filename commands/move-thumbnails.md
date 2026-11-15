---
description: Move the phone gallery thumbnails in a media folder (1234.jpg, small, no camera info) into _thumbnails, once they have a Date Taken. Optional; run it after the dates are written. Previews only; add --apply to make the changes.
argument-hint: <path-to-media-folder> [--apply]
---

# /move-thumbnails

Set aside the phone gallery thumbnails an import brought along, after `/fix-media-dates` has written their dates.

## Dry run or apply

`$ARGUMENTS` is the media folder, optionally followed by `--apply`. Below, `<folder>` means that folder without `--apply`.

- **Without `--apply`, this is a dry run.** Run `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --move-thumbnails`. Nothing is changed. Share the counts and any `LEFT` or `COLLISION` lines with the user, then end with: to make these changes, type `/move-thumbnails <folder> --apply`.
- **With `--apply`**, run `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --move-thumbnails --apply`.

## What it does

- A phone thumbnail is a JPEG named only by a number (`46.jpg`, or `46 (2).jpg`), at most 1024 pixels on its long side, with no camera Make or Model. Photos that only look like one (a camera photo, a full-size picture, `IMG_46.jpg`) are left alone.
- Every thumbnail in `<folder>` and its subfolders at any depth that **already has a Date Taken** moves straight into `<folder>/_thumbnails`, with no subfolders. A name already taken there gets a `_<subfolder-name>` suffix (`46_2026-11-03.jpg`); if that is taken too, the file stays and is listed as a `COLLISION`.
- A thumbnail with **no Date Taken yet** stays where it is and is listed as `LEFT (no Date Taken yet; run --fill-blanks first)`. Every step skips `_thumbnails`, so a thumbnail moved there before it is dated would lose its folder's date for good. If the user sees `LEFT` lines, suggest running `/fix-media-dates <folder>` (step 8, writing Date Taken where blank) first, then this command again.
- Nothing is deleted. Some thumbnails may be the only copy left of a photo deleted from the phone, so tell the user to compare `_thumbnails` with their photos before deleting any.
- It is optional and not part of `/fix-media-dates --all`. To include it in a full run, add `--move-thumbnails`: `/fix-media-dates <folder> --all --move-thumbnails --apply` runs it after the dates are written and before `--apply-moves` or `--flatten`.

## Deliverables

- The run (and the dry run) is recorded in the Run log and Run counts sheets of the audit workbook (`<folder name>_<photos|videos>_media_audit_<date>.xlsx`) at the root of `<folder>`.
- Summary message with counts (thumbnails moved, thumbnails left because they have no date yet, collisions), saying "would" for a dry run.
- After a dry run: the line `/move-thumbnails <folder> --apply` for the user to type.
