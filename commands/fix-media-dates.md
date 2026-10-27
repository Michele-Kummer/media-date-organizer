---
description: Ensure every photo and video in a folder has a Date Taken — fix extensions, set junk aside, write missing dates, convert PNG to JPEG where needed, sort by date, and clean up. Previews only; add --apply to make the changes.
argument-hint: <path-to-media-folder> [--all [--quarantine-ads] [--flatten]] [--apply]
---

# /fix-media-dates

Ensure every photo and video in the media folder has a readable Date Taken (Media Created for video).

## Dry run or apply

`$ARGUMENTS` is the media folder, optionally followed by `--all` (with `--quarantine-ads` or `--flatten` to opt in to those), `--apply`, or both. Below, `<folder>` means that folder without these flags.

- **With `--all`**, skip the step-by-step walk below and follow "All in one go" instead. `--all` alone is a dry run of every step it includes; `--all --apply` makes all the changes.

- **Without `--apply`, this is a dry run.** Run every step below exactly as written. Each one only lists what it would do (`WOULD RENAME`, `WOULD WRITE`, `WOULD MOVE`, ...) and changes nothing. Each step is previewed against the folder as it is now, so a later step may do more once the earlier ones have run. Share the results, then ask which optional steps (5, 7, 9, 11, 12 and 13) the user wants. Always ask about step 13, cleaning up converted files, since it is the one step that deletes. End with: to make these changes, type `/fix-media-dates <folder> --apply`.
- **With `--apply`**, run the same steps with `--apply` added to each `organize.py` command and `-Apply` added to each PowerShell script, so the changes are made. Run an optional step only if the user asked for it; if they have not said whether they want step 13, ask before running it. Steps that only report (2 and 6) run the same either way.

## Prereq (first run only)

Python 3.9 or later, then:

```bash
pip install -r requirements.txt
# or:
pip install "pillow>=10.0" "openpyxl>=3.1"
```

## Steps

1. **Fix extensions.** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --fix-extensions`. Lists photos and videos whose extension doesn't match their content (`WOULD RENAME: IMG_1.PNG -> IMG_1.HEIC (really HEIC)`), and renames them with `--apply`. A name already taken is a `COLLISION` and the file keeps its name.

2. **Scan metadata.** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --report-only`. Writes the audit workbook, `<folder name>_<photos|videos>_media_audit_<date>.xlsx`. Changes no photo or video. Share the summary.

3. **Set junk aside.** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --move-junk`. Moves `.AAE` iPhone edit files, `Thumbs.db` thumbnail caches and macOS `._` sidecars into `<folder>/_junk`, keeping their subfolder path. Nothing is deleted; the user looks over `_junk` and deletes it.

4. **Set incomplete files aside.** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --move-incomplete`. Moves 0-byte files, files of nothing but null bytes, and videos with no video header into `<folder>/_incomplete`, keeping their dated subfolder. Nothing is deleted.

5. **Set ads aside (optional).** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --quarantine-ads`. For ad images and videos (names like `0c4cda27-b4cc-4e92-a446-d6b780f24a64`, `bed51b94a_1595`, `gmsnet2`, `news_images%2F1714658759372`, `UnityAdsCache-<hash>`, `54ac2fda0a6755305200011c-b30-600`, or game ads such as `492887-1648448524975-3d62u` or `lbay6fy2_fftxeca_itehyhqsmpyyszx7`). Files with an ad-style name and no camera Make/Model move into `<folder>/_ads` for the user to review and delete; nothing is deleted. When `<folder>` holds year folders, an ad in a year folder goes into that year's own `_ads`, such as `<folder>/2022/_ads`. Name matches that have camera info are kept. Share the list.

6. **Find plist and XMP files.** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --find-plists`. Lists files with a photo name that hold plist or XMP text (`IMG_E5239.JPG`). Changes nothing; every other step leaves them alone. Share the list and let the user decide.

7. **Convert BMP → JPEG (optional).** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --convert-bmp`. BMP cannot hold a date at all, so each BMP's JPEG is given the date from its filename or folder. The original BMP is left for step 13.

8. **Write Date Taken where blank.** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --fill-blanks`. Photos and videos are picked up at any depth under `<folder>`. JPEG/PNG/TIFF files get `DateTimeOriginal` stamped into their EXIF from a date in the filename if there is one, else `<folder-date> 12:00:00` when the containing folder's name holds a date (`2019-08-30`, `2026-08-19 11-44-31`, `08-19-2026`, `Aug 19 2026`). File modified time is never used. HEIC/MOV are written with exiftool when it is installed, else flagged (need exiftool). Videos (MOV/MP4/M4V/3GP) with a blank Media Created get it from a date in the filename, else the nearest containing folder name holding a full date (`2019-08-30`, `11-11-2019`). A year-only folder name is not used; videos with neither source are listed as `SKIPPED (no date in filename or folder names)`, so share that list.

9. **Convert PNG → JPEG (optional).** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --convert-png`. For users who want Windows Explorer to show Date Taken for PNG screenshots. Runs after step 8 so the date written into the PNG is carried into the JPEG. JPEG is lossy; the original PNG is left for step 13. PNGs with transparent pixels are skipped and stay PNG.

10. **Move to date-matched folders.** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --apply-moves`. Files whose Date Taken doesn't match the folder name are moved to a sibling folder named for their real date. If the user wants to flatten (step 12), this step can be left out.

11. **Sync Date Modified and Date Created (optional).** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --sync-timestamps`. For users who want Explorer's "Date Modified" and "Date Created" to show the real capture time. Files are picked up at any depth under `<folder>`. Date Modified is set only on files that look unedited (EXIF ModifyDate matches DateTimeOriginal and no editor-software tag); edited files keep their Date Modified, get Date Created set, and are listed.

12. **Flatten into the root folder (optional).** `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --flatten`. For users who want the photos and videos out of their dated subfolders. Every file that has a Date Taken moves up into `<folder>` itself and the emptied subfolders are moved into `<folder>/_empty_folders`, keeping their path (not deleted); undated files stay put. Also available on its own as `/flatten-media`.

13. **Clean up converted files (optional; always ask).** `skills/media-date-organizer/scripts/Cleanup-Pictures.ps1 -Path "<folder>"`. Lists PNGs and BMPs already converted to JPEG (same name, same size, same pixels) and empty folders; with `-Apply` it deletes those PNGs and BMPs and moves the empty folders into `_empty_folders`. This is the one step that deletes, so ask the user whether they want it, and offer `--visual-compare` first if they want to see the pairs. Its summary ends with how many photos and videos are from a different year than the folder (`Media from a different year`), each listed as `OTHER YEAR (<year>)`. In the dry run, remind the user it comes last.

## All in one go

`/fix-media-dates <folder> --all` runs `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --all`. It fixes extensions (step 1), moves junk into `<folder>/_junk` (step 3) and incomplete files into `<folder>/_incomplete` (step 4), then fills blanks, converts PNG, applies moves and syncs timestamps (steps 8–11). It deletes nothing and asks no questions: every step it includes runs.

- **Left out unless opted in:** ad quarantine and flatten. They run only if the user adds `--quarantine-ads` or `--flatten` to the slash command (`/fix-media-dates <folder> --all --flatten --apply`); pass those flags on to `organize.py`.
- **Not part of `--all`:** the scan report (step 2), the plist report (step 6), BMP conversion (step 7) and cleaning up converted files (step 13). Run them on their own; after `--all --apply`, ask the user whether they want step 13.
- **`--all` without `--apply`** is a dry run: nothing is changed. Each phase is previewed against the folder as it is now, so a later phase may do more once the earlier ones have run. End with: to make all these changes, type `/fix-media-dates <folder> --all --apply` (with the same `--quarantine-ads` or `--flatten`, if any).
- **`--all --apply`** runs the same command with `--apply` added.

It ends with a `Summary of this run` block covering every phase's counts and problems; share that block with the user.

## Deliverables

- `<folder name>_<photos|videos>_media_audit_<date>.xlsx` at the root of `<folder>`. Every step above, the cleanup script and dry runs included, appends what it did to its Run log and Run counts sheets. The workbook must be closed in Excel while a step runs, or that step is not recorded.
- Summary message with counts (extensions corrected, junk files set aside, incomplete files set aside, ad files quarantined, dates written, files converted, files moved, timestamps synced, files flattened and empty folders moved to `_empty_folders`), saying "would" for a dry run.
- After a dry run: the line `/fix-media-dates <folder> --apply` (or `/fix-media-dates <folder> --all --apply` after `--all`) for the user to type. After `--apply`: if step 13 was not run, ask whether the user wants to clean up converted files.
