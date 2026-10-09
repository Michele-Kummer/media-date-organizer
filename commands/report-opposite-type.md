---
description: Report photos filed in a video folder, or videos filed in a photo folder, with a count for each year folder. Changes nothing.
argument-hint: <path-to-folder-holding-the-year-folders>
---

# /report-opposite-type

List the photos sitting among the videos in `$ARGUMENTS`, or the videos sitting among the photos, year folder by year folder.

## Steps

1. **Report.** Run `python skills/media-date-organizer/scripts/organize.py --root "$ARGUMENTS" --opposite-type`. Nothing is changed, so no confirmation is needed.

2. **Share the result.** Give the user the total, the count for each year folder that has any, and the listed files (or where to find them if there are many).

## What it does

- `$ARGUMENTS` is the folder that holds the year folders (`D:\Videos`, `D:\Pictures`), not one year. To check both, run it once for each.
- Whichever kind `$ARGUMENTS` holds more of decides what it is: a video folder is checked for photos, a photo folder for videos.
- Every folder whose name starts with a year (`2014`, `2013 West`) is searched at every depth. Other folders in `$ARGUMENTS`, and files loose in it, are not looked at.
- `_ads` and `_incomplete` folders are not counted.
- A file's kind goes by its extension, so run `Fix-Extensions.ps1` first if extensions may be wrong.
- Each file found is listed as `PHOTO IN VIDEO FOLDER: 2014/7-17-2014/IMG_0001.jpg` (or `VIDEO IN PHOTO FOLDER: ...`), followed by one line per year folder (`2014: 3 photo(s), 412 video(s)`) and an `OPPOSITE TYPE` total.
- If `$ARGUMENTS` has no year folders, it is reported as one folder.

## Deliverables

- The run is recorded in the Run log and Run counts sheets of the audit workbook (`<folder name>_<photos|videos>_media_audit_<date>.xlsx`) at the root of `$ARGUMENTS`.
- Summary message with the total, the number of year folders affected, and the count for each year folder.
