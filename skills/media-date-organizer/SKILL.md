---
name: media-date-organizer
description: Use this skill when the user wants every photo and video in a folder to have a readable Date Taken (Media Created for video). Triggers include "fix the dates on my photos," "make sure all my pictures have Date Taken," "my photos don't show Date Taken in Explorer," "convert these PNGs so I can see the date," "sort my photos and videos by when they were taken," "my videos have no Media Created date," or any mention of blank/missing/wrong Date Taken on photo or video files. Also "check for plist files," "find XMP or AAE files named as photos," or a "Not a valid JPG (looks more like a XMP)" error. The skill reads real EXIF and container metadata (HEIC/HEIF, MOV/MP4, PNG/JPEG) without external tools, writes Date Taken where it is missing, converts PNG to JPEG when the user needs Windows Explorer to surface the date, moves files to date-matched folders, optionally syncs Windows file timestamps to Date Taken for unedited files, and produces an XLSX audit. Works on photos and videos from any source. Do NOT use for RAW camera files or video libraries larger than a few thousand items — the sandbox parse would be slow.
---

# media-date-organizer

Ensures every photo and video has a Date Taken (Media Created for video). Seven phases, each independently runnable.

## Prerequisites

The scripts need Python 3.9 or later and two Python packages: `Pillow` 10.0+ (image handling + EXIF) and `openpyxl` 3.1+ (audit workbook). On first run in a fresh Python environment, install both before invoking any phase:

```bash
pip install -r requirements.txt
# or:
pip install "pillow>=10.0" "openpyxl>=3.1"
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
- Confirmation before each destructive step (write EXIF, rename, move, convert, delete, timestamp sync): that is, before adding `--apply`.

## Workflow

**Dry run first, then `--apply`.** Every step that changes files only lists what it would do (`WOULD WRITE`, `WOULD MOVE`, `WOULD DELETE`, ...) and changes nothing, unless `--apply` is added (`-Apply` for the PowerShell cleanup script). For each such step, run the command as written below, share the preview with the user, and once they confirm run the same command again with `--apply` added. Reports (`--report-only`, `--compare-collisions`, `--visual-compare`, `--opposite-type`, `--find-plists`) change nothing, so they run the same with or without it.

Each phase below can be run on its own, or several can be given on one command line. `python scripts/organize.py --root "<MediaRoot>" --all` fixes extensions (Phase 1), moves junk into `_junk` and incomplete files into `_incomplete`, and then runs Phases 3–6 (`--fix-extensions --move-junk --move-incomplete --fill-blanks --convert-png --apply-moves --sync-timestamps`); add `--quarantine-ads` or `--flatten` to include those. It deletes nothing. Phases always run in this order whatever order the flags are typed in: fix-extensions, move-junk, move-incomplete, quarantine-ads, convert-bmp, fill-blanks, convert-png, apply-moves, compare-collisions, visual-compare, sync-timestamps, flatten. A multi-phase run ends with a `Summary of this run` block listing every phase's counts and the problem lines (`FAILED`, `SKIPPED`, `COLLISION`, `NOTE`) it reported, up to 50 per phase. Without `--apply`, `--all` previews every phase it includes against the folder as it is now, so a later phase may do more once the earlier ones have run. Add `--apply` only after the user has confirmed every phase it includes. `--report-only` cannot be combined with other phases.

### Phase 1 — Fix extensions (part of `--all`)
`python scripts/organize.py --root "<MediaRoot>" --fix-extensions`. Reads each file's first bytes and lists each rename as `WOULD RENAME: 2020-01-01\IMG_1.PNG -> IMG_1.HEIC (really HEIC)` and keeps the extension's case. It looks only at files named as a photo or video (or with no extension), so an `.m4a` song or a document is never renamed. A name already taken, or claimed by another file in the same folder, is a `COLLISION` and the file keeps its name. A container whose brand it does not know (a HEIF burst, an AVIF photo; BUG-04) is `UNKNOWN FORMAT (left alone)` rather than renamed to `.mp4`. `_ads`, `_incomplete`, `_junk` and `_empty_folders` are skipped.

3GP/3G2 videos keep their own extension (they are not renamed to `.mp4`). AVCHD camcorder files (`.m2ts`/`.mts`), MPEG videos (`.mpg`/`.mpeg`, also `.vob` and `.mod`) Windows Media files (`.wmv`/`.asf`/`.wma`) and AVI videos (`.avi`) are recognised and left as they are; `organize.py` never dates or converts them, and only `--flatten` moves them. Sony sidecar files (`.modd`, `.moff`) are left alone. Empty (0-byte) files are listed as `EMPTY` and left for `--move-incomplete`; `UNKNOWN FORMAT` means a non-empty file with a photo or video name in a format it does not recognise. (The older PowerShell version, `Fix-Extensions.ps1`, has been moved to `_review` and is no longer used.)

### Phase 2 — Scan metadata
`python scripts/organize.py --root "<MediaRoot>" --report-only`. Reads Date Taken from the real format of each file:
- HEIC/HEIF → embedded TIFF/EXIF `DateTimeOriginal`
- MOV/MP4/M4V/3GP/3G2 → `mvhd` atom `creation_time` (Explorer's "Media created"), converted from UTC to local time
- PNG/JPEG/TIFF → standard EXIF via Pillow

Photos and videos are found in `<MediaRoot>` and every subfolder at any depth; `_ads`, `_incomplete`, `_junk` and `_empty_folders` are skipped at any depth too, so a year's own `2022/_ads` is skipped as well. Writes the audit workbook (`<root folder name>_<photos|videos>_media_audit_<date>.xlsx`) summarizing which files have Date Taken, which don't, and which are in a folder that doesn't match their date. Share the summary with the user before Phase 3.

### Phase 3 — Write Date Taken where it's missing
`python scripts/organize.py --root "<MediaRoot>" --fill-blanks`. For every file in `<MediaRoot>` and every subfolder at any depth whose Date Taken is blank:
- If the filename contains a date (e.g. Snapchat exports `2023-12-20_<id>-main.jpg`, or `IMG_20231220_142355.jpg`), write that as `DateTimeOriginal` (JPEG, PNG, TIFF), using the time from the name if present, else `12:00:00`.
- Otherwise, if the containing folder's name holds a date (`2019-08-30`, `20190830`, `2026-08-19 11-44-31`, `08-19-2026` read month first, `30-08-2019` read day first only when the first number cannot be a month, `Aug 19 2026`, `19 August 2026`), write `DateTimeOriginal = <folder-date> 12:00:00`.
- The file's modified time is never used as a source — it usually reflects the import, not the capture.
- JPEGs get the EXIF segment swapped in place; the image data is not re-encoded.
- HEIC/MOV files are written with `exiftool` when it is installed (on PATH, or in winget's default folder). Without it they are flagged as `SKIPPED (needs exiftool)` — offer to install it (`winget install --id OliverBetz.ExifTool -e --source winget`), or convert HEIC → JPEG in Phase 4.
- Videos (MOV/MP4/M4V/3GP/3G2) whose Media Created is blank get it written with `exiftool`, from the first of:
  1. a date in the filename (e.g. `WP_20131115_002.mp4`, `20190630_090136.mp4`), with its time if present, else `12:00:00`;
  2. the nearest containing folder whose name holds a full date (`2019-08-30`, `11-11-2019`), at `12:00:00`.

  A folder name holding only a year (`2014`, `2013 West`) is never used. Videos with neither source are listed as `SKIPPED (no date in filename or folder names)`; share that list with the user. The time is treated as local time and stored as UTC, so Explorer's Media Created column shows it unchanged. AVI and MPG files are not handled.
- Without `--apply` it lists every date that would be written (`WOULD WRITE`) without touching anything.
- Empty (0-byte) files are skipped and reported as one `NOTE:` count. GIF/BMP/WEBP have no Date Taken field and are counted as `unsupported-format`. If the count of empty files is large, suggest `--move-incomplete` (below).

### Phase 4 — Convert formats Windows can't read Date Taken from
`python scripts/organize.py --root "<MediaRoot>" --convert-png`. Converts PNG files to JPEG at quality 95, preserving EXIF, so Windows Explorer surfaces Date Taken. Without `--apply` it lists each PNG that would be converted (`WOULD CONVERT`). Add `--apply` only after confirming with the user — JPEG is lossy and the original PNG is left in place for the cleanup script to remove. PNGs with any transparent pixels are never converted (JPEG has no transparency) and are counted as `skipped-transparent`; they stay PNG. PNGs named `*-overlay.png` (Snapchat's transparent caption layers) are skipped too. A `.png` that cannot be read as a picture (a macOS `._` sidecar, a truncated download) is reported as `FAILED to convert`, counted as `read-failed` and left alone; the remaining PNGs still convert.

### Convert BMP to JPEG (optional; not part of `--all`)
`python scripts/organize.py --root "<MediaRoot>" --convert-bmp`. BMP has no field for a date, so neither Explorer nor ExifTool can give one a Date Taken. This converts each BMP in `<MediaRoot>` and every subfolder to a JPEG of the same name at quality 95. It writes into the JPEG the Date Taken `--fill-blanks` would use: the date in the filename, else the folder's date at 12:00:00 (`WOULD CONVERT: 2021-05-04\scan.bmp -> scan.jpg (Date Taken 2021-05-04 12:00:00 from folder)`, counted as `converted-dated` or `converted-undated`). It runs before `--fill-blanks` when both are given. A `.bmp` that is really another format is reported as `NOT A BMP` and left for Phase 1. A BMP with transparent pixels stays BMP. The original is left for `Cleanup-Pictures.ps1`, which deletes it once the JPEG is confirmed as the same picture. `--fill-blanks` ends with a `NOTE` when it skipped BMPs.

### Phase 5 — Move to date-matched folders
`python scripts/organize.py --root "<MediaRoot>" --apply-moves`. Any file whose Date Taken differs from its current folder's `YYYY-MM-DD` name is moved to a sibling folder named for its real date, creating that folder if needed. Without `--apply` it lists each move (`WOULD MOVE`) and rename (`WOULD RENAME`) and creates no folder. A file with no Date Taken or Media Created is not moved; if it sits in a `YYYY-MM-DD` folder and its name holds no date, it is renamed with a `_<folder-date>` suffix (`RENAMED (no date in file)`, counted as `suffixed-undated`) so the folder's date survives in the name. Run `--fill-blanks` first so only files whose date could not be written get the suffix. A suffix is never added to a file that has a date, and never stripped from any file. Extensions are left exactly as they are, case included; correcting them is Phase 1's job. Files at any depth are checked against the folder they sit in, and move to a sibling of it (`Trip/2019-08-30/x.jpg` taken on the 31st goes to `Trip/2019-08-31`). A file loose in `<MediaRoot>` is checked against `<MediaRoot>`'s own name and never moved out of it; if that name is a different date, the plan lists it as `in-root-date-differs`.

### Compare collisions (report only, any time after Phase 5; not part of `--all`)
`python scripts/organize.py --root "<MediaRoot>" --compare-collisions`. Phase 5 skips a file as `COLLISION` when its name is already taken in the folder for its real date. This compares each skipped file byte for byte with the file holding that name and lists the pair as `IDENTICAL` (a true duplicate) or `DIFFERENT` (with both sizes and both dates). It works after Phase 7 too: a file `--flatten` renamed with a `_<date-taken>` suffix is compared with the file that had its name in the root, and a file `--flatten` left in its subfolder as a `COLLISION` is compared with both. Nothing is moved, renamed or deleted; share the counts with the user and let them decide what to do with the duplicates.

### Visual duplicate check (report only; not part of `--all`)
`python scripts/organize.py --root "<MediaRoot>" --visual-compare`. Compares the pixels of each pair of possible duplicates and reports `DUPLICATE`, `DIFFERENT` or `UNSURE` with a confidence level (`high`, `medium`, `low`) and the measured difference. Nothing is moved, renamed or deleted: there is no mode that acts on the verdicts yet. It runs entirely on this computer; nothing is sent anywhere and it costs nothing.
- Pairs checked: every collision pair `--compare-collisions` covers, plus files in one folder that share a name and differ only in extension (`IMG_1.jpg` / `IMG_1.png`, the pairs `Cleanup-Pictures.ps1` would delete from).
- Byte-identical pairs are `IDENTICAL (confidence certain)` with no comparison needed. For the rest, a photo is compared as one picture; a video by its length and by four frames taken at the same points in each file, judged on the least alike frame.
- The pixel difference is a percentage (0 = same picture). Up to 1% is `DUPLICATE` high, up to 2% `DUPLICATE` medium, up to 10% `UNSURE` low, up to 15% `DIFFERENT` medium, above that `DIFFERENT` high. Different video lengths or picture shapes are `DIFFERENT` high outright. Two shots taken a fraction of a second apart can score under 2%, so a `DUPLICATE` verdict on files that never shared a name deserves a look.
- Videos need ffmpeg: on PATH, or `pip install "imageio-ffmpeg>=0.5"`.
- The audit workbook's Run log has a **Confidence** column filled in for these rows. HEIC photos cannot be compared (Pillow cannot open them) and are listed as `FAILED`.

### Phase 6 — Sync file-system timestamps (optional)
`python scripts/organize.py --root "<MediaRoot>" --sync-timestamps`. Looks at every file in `<MediaRoot>` and every subfolder at any depth. Sets each file's "Date Created" to its EXIF Date Taken, and its "Date Modified" too **but only for files that look unedited**. An "unedited" file is one whose EXIF `DateTime` tag (file-level modify time) equals `DateTimeOriginal` (or is missing) AND whose EXIF `Software` tag does not match a known editor (Photoshop, Lightroom, Camera Raw, GIMP, Affinity, Luminar, Pixelmator, Snapseed, VSCO, Instagram). Files that fail the check keep their "Date Modified" (it records when they were edited) and get only "Date Created" set, listed as `SYNCED created only (edited)` and counted as `created-only-edited`. Files with no Date Taken are not touched. Without `--apply` it lists each file that would be synced (`WOULD SYNC`). "Date Created" is set through the Win32 `SetFileTime` API, so on non-Windows systems only "Date Modified" is synced (reported as `created-unsupported`) and edited files are skipped.

### Phase 7 — Flatten into the root folder (optional)
`python scripts/organize.py --root "<MediaRoot>" --flatten`. Moves every file that has a Date Taken up one level, out of its `YYYY-MM-DD` subfolder and into `<MediaRoot>` itself, then moves the subfolders left empty into `<MediaRoot>/_empty_folders`, keeping their path, instead of deleting them (`MOVED EMPTY`, counted as `empty-folders-moved`; a path already there gets a ` (2)` ending). Every phase ignores `_empty_folders`. Without `--apply` it lists every move, including the folders that would go into `_empty_folders`, without touching anything.
- Files with no Date Taken are left where they are — the folder name may be the only record of their date — so their folders are kept.
- Exception: inside `<MediaRoot>/_ads`, every file in a subfolder at any depth (`_ads/Temp/2020-01-06`, since `--quarantine-ads` keeps the subfolder path) moves up into `_ads` itself whether or not it has a Date Taken (ads rarely do), counted as `ads-moved`. Game `.raw` ads move too. A name already taken in `_ads` gets a `_<subfolder-name>` suffix, which keeps the date the ad was filed under. The same happens when `<MediaRoot>` is itself an `_ads` folder (`E:\Pictures\2020\_ads`); its emptied subfolders then go into the `_empty_folders` beside it (`E:\Pictures\2020\_empty_folders\_ads`), as a run on the year folder would put them. It also happens when `<MediaRoot>` is anywhere inside an `_ads` folder (`E:\Pictures\_ads\2022`); its emptied subfolders then go into its own `_empty_folders`.
- Camcorder videos (`.m2ts`, `.mts`) and older MPEG, Windows Media and AVI videos (`.mpg`, `.mpeg`, `.wmv`, `.avi`) are flattened too, going by the date in the filename (`20180116122434.m2ts`, `WP_20130807_002.mpg`), since their internal date is not read. One with no date in its name goes by the date in its subfolder's name (`2018-01-16`, `7-17-2014`) and has that date appended as it moves (`7-17-2014/SDC13837.AVI` → `SDC13837_2014-07-17.AVI`), counted as `dated-from-folder`, so the date survives the folder being removed. One with neither is `LEFT (no date in filename or folder name)`; one that is empty or all null bytes is `LEFT (no video data)`.
- Sony sidecar files named `<file name>.modd` / `<file name>.moff` (usually hidden) move with their file and take its new name if it was renamed; counted as `sidecars-moved`. The user has Sony's software, so sidecars are kept wherever their file is.
- A `.modd`/`.moff` in `<MediaRoot>` or one of its subfolders whose file is not beside it is moved into `<MediaRoot>/_junk`, keeping its path (`MOVED (sidecar with no file)`, counted as `orphan-sidecars-moved`). Nothing is deleted. `_ads` and `_incomplete` are not touched.
- Folders that still hold anything else (undated files, non-media files) are kept.
- If a name is already taken in the root (e.g. two days each have an `IMG_0001.JPG`), the incoming file gets a `_<date-taken>` suffix; if that is taken too, it is skipped and reported.
- It reports how many files of the opposite kind `<MediaRoot>` itself holds once flattened: `OPPOSITE TYPE: 37 video(s) in this photo folder (9,120 photo(s))`, counted as `videos-in-photo-folder` (or `photos-in-video-folder` when videos are the majority). Whichever kind there is more of decides what the folder is; `_ads`, `_incomplete` and files left in subfolders are not counted. Share the number with the user; nothing is moved because of it.

Run this last: once files are in the root, the other phases no longer see them (they only look inside subfolders).

### Opposite type report (report only, any time; not part of `--all`)
`python scripts/organize.py --root "<FolderOfYearFolders>" --opposite-type`. Lists every photo filed among the videos, or video among the photos, with a count for each year folder. Here `--root` is the folder that holds the year folders (`D:\Videos`), not one year; to check photos and videos both, run it once for each. Also available as `/report-opposite-type`.
- Whichever kind the root holds more of decides what it is. Each file of the other kind is listed as `PHOTO IN VIDEO FOLDER: 2014/7-17-2014/IMG_0001.jpg` (or `VIDEO IN PHOTO FOLDER: ...`), then one line per year folder (`2014: 3 photo(s), 412 video(s)`) and an `OPPOSITE TYPE` total. Counted as `photos-in-video-folders` (or `videos-in-photo-folders`), `year-folders`, `year-folders-with-photos`, and one count per year folder.
- A year folder is any folder whose name starts with a year (`2014`, `2013 West`); each is searched at every depth. Other folders in the root, and files loose in it, are not looked at. `_ads` and `_incomplete` are not counted. A root with no year folders is reported as one folder.
- A file's kind goes by its extension, so run Phase 1 first if extensions may be wrong.
- Nothing is moved, renamed or deleted; share the counts and the list with the user and let them decide what to move.

### Find plist files named as photos (report only, any time; not part of `--all`)
`python scripts/organize.py --root "<MediaRoot>" --find-plists`. Lists every file in `<MediaRoot>` and every subfolder, holding folders included, that has a photo or video name but holds plist, XMP or other XML text: usually an iPhone `.AAE` edit file, or an XMP sidecar, saved under a picture's name (`IMG_E5239.JPG`). Each is listed as `NOT MEDIA (plist file named .JPG): 2023-08-07/IMG_E5239.JPG` and counted by kind (`plist-files`, `XMP-files`, `binary-plist-files`, `XML-files`) and in total (`not-media`).
- Every other phase recognises these files too. It leaves them where they are and reports them as `NOT MEDIA (... left alone)`, instead of failing to write a date into them (ExifTool's `Not a valid JPG (looks more like a XMP)`), converting them, or giving them a `_<folder-date>` suffix. `--fix-extensions` reports them as `NOT MEDIA` instead of `UNKNOWN FORMAT`.
- Nothing is moved, renamed or deleted. Share the list and let the user decide: they may want to keep them (an `.AAE` holds the edits made on the iPhone), rename them to `.AAE`, or delete them.

### Quarantine ad images and videos (optional, any time)
`python scripts/organize.py --root "<MediaRoot>" --quarantine-ads`. Moves ad images and videos out of `<MediaRoot>` and every subfolder into `<MediaRoot>/_ads`, keeping their subfolder path, so the user can look through them and delete the folder themselves. When `<MediaRoot>` holds year folders (`E:\Pictures`), an ad in a year folder goes into that year's own `_ads` instead (`2022/Temp/ad.png` → `2022/_ads/Temp/ad.png`); only ads loose in `<MediaRoot>` or in other folders go into `<MediaRoot>/_ads`. A root that is a year folder itself is not split by its day folders. `_ads` and the other holding folders are skipped at every depth, so ads already set aside are not moved again. Nothing is deleted. Without `--apply` it only lists them, as `WOULD QUARANTINE: <from> -> <to>`. A file is treated as an ad only when both hold:
1. The whole filename stem is one of:
   - a UUID, e.g. `0c4cda27-b4cc-4e92-a446-d6b780f24a64`
   - a 9-character hex id plus a number, e.g. `bed51b94a_1595`
   - `gmsnet` plus an optional number, e.g. `gmsnet2`
   - `news_images%2F` plus a number, e.g. `news_images%2F1714658759372`
   - `UnityAdsCache-` plus a 64-character hex hash, e.g. `UnityAdsCache-3d4c8e33a716c48d4cf7daad6049cb87960c0ef042c3c6014d7ba81eb18d2091`
   - a 24-character hex id plus one or more parts joined by `-` or `_`, e.g. `54ac2fda0a6755305200011c-b30-600`, `55d58970f6cd4574f635d6e3_568-1443241239`
   - a name that contains pixel dimensions and ends in `___` plus a 6-character id, e.g. `Update_Now_Video_V2_720x1280_15s___fudxlv`, `720x1280_ENDCARD___fo9w1l`
   - an id, a 13-digit millisecond time and a 5-character id, e.g. `492887-1648448524975-3d62u` (game ads)
   - a CDN address saved as the name, e.g. `__d2duuy9yo5pldo.cloudfront.net_codigames_6e945046-0a56-4291-814d-1cbf498cf2be`
   - 8, 7 and 16 letters and digits joined by `_`, e.g. `lbay6fy2_fftxeca_itehyhqsmpyyszx7`
   - `icon`
   - for `.raw` files only: `draw_` plus a word, e.g. `draw_title.raw`. These are a game's raw pixel dumps. A camera RAW (TIFF or Panasonic header) is kept as `KEPT (camera: camera RAW header)`.
   - for videos only: 20 lowercase letters and digits with at least one letter, e.g. `32129eda9b8e718c5277`, `vuyyzy0brvod5gcaocnv`, `agqnsutqkbwulksalejd`
   - for videos only: a 32-character lowercase hex hash, e.g. `d5a210d011c47b8300bb8034048719a9`
   - for videos only: a name ending `-<width>x<height>-Q2` or `-<width>x<height>-h264-Q2`, e.g. `313e81d7e1f03f326004da8f41daa11f.mp4-720x1280-h264-Q2`, `peacock_hand_4pics_fantasy_cute_45sec_1080x1920_rev-720x1280-Q2`

   Each may be followed by the `_YYYY-MM-DD` suffix `--flatten` or `--apply-moves` adds, or a ` (2)` copy marker.
2. It carries no camera Make/Model (EXIF for images, the device-make tag for video).

Name matches that do have camera info are real photos or videos; they are kept and listed as `KEPT`. Share those and the quarantined count with the user.

Best run before Phase 3 so ads are not dated and moved with the real photos and videos. The other phases ignore `_ads` at any depth, a year's own `2022/_ads` included, except Phase 7, which flattens the subfolders inside it. Emptied folders are left for Phase 7 or the cleanup script.

### Move incomplete files (any time; part of `--all`)
`python scripts/organize.py --root "<MediaRoot>" --move-incomplete`. Moves incomplete media files out of `<MediaRoot>` and every subfolder into `<MediaRoot>/_incomplete`, keeping their subfolder path, so each file stays in its dated folder (`_incomplete/2018-08-19/clip.mp4`). A file is incomplete when it is 0 bytes (`empty`), contains nothing but null bytes (`null-filled`), or is a video with no video header (`no-video-header`: a stub of a few bytes or a truncated copy that no player can open). These are the remains of a failed copy or phone transfer. Nothing is deleted. Without `--apply` it only lists them. The other phases ignore `_incomplete`, and `--flatten` never empties it. A `_no-image-data` folder left by an earlier version is folded into `_incomplete`; `--move-no-data` still works as the old name of the flag. These files cannot be repaired; the names tell the user what to re-copy from the phone or a backup.

### Move junk files aside (any time; part of `--all`)
`python scripts/organize.py --root "<MediaRoot>" --move-junk`. Moves every `.AAE` file (counted as `moved-aae`) and every Windows thumbnail cache (`Thumbs.db`, `ehthumbs.db`, `ehthumbs_vista.db`, hidden or not; counted as `moved-thumbs`) in `<MediaRoot>` and every subfolder into `<MediaRoot>/_junk`, keeping its subfolder path (`_junk/2023-08-07/IMG_1234.AAE`). Thumbnail caches are matched by whole file name only, so a photo such as `west sucking thumb.jpg` is never touched. `.AAE` files are the edit-instruction sidecars an iPhone exports next to a photo; they contain no image and nothing on Windows reads them. It also moves macOS `._` sidecars (`._IMG_1234.png` beside `IMG_1234.png`; counted as `moved-mac-sidecars`), the metadata stubs a Mac writes when copying to a non-Mac drive. A file counts as one only when its name starts with `._` and its contents open with the AppleDouble signature, so a real picture with such a name is never touched. Nothing is deleted: the user looks over `_junk` and deletes it. A path already taken in `_junk` is a `COLLISION` and the file stays where it is. Without `--apply` it only lists them. The other phases ignore `_junk`, and the final check reports what is still in it (`IN JUNK`). `--delete-junk` still works as the old name of the flag and moves too.

### Clean up converted files (optional; ask)
Ask the user whether they want this step. If they do, run `scripts/Cleanup-Pictures.ps1 -Path "<MediaRoot>"` at the end, which previews, then the same with `-Apply`. Run `--visual-compare` before it if the user wants to see the PNG/JPG pairs first, since this step removes one file of each pair. It deletes each PNG that `--convert-png` already turned into a JPG (same name, same picture size, pixels no more than 1% apart; any other files that share a name are kept, and a PNG whose JPG differs is listed as `KEPT` with the reason) and moves empty folders into `_empty_folders` (not deleted). It ends by counting the photos and videos whose Date Taken is in a different year from the year folder (`OTHER YEAR (2019): Trip/IMG_1.jpg`, one line each, then `Media from a different year : 12` in its summary); that count comes from `organize.py --other-year`, which can also be run alone and changes nothing.

## Output

Everything writes to one audit workbook per day, `<root folder name>_<photos|videos>_media_audit_<date>.xlsx` in the root folder (`2014_videos_media_audit_2026-10-07.xlsx`), where `<date>` is the day of the run and `photos` or `videos` is whichever kind the root holds more of. A workbook from earlier the same day under the old name, `media_audit_<date>.xlsx`, is renamed to the new one; older ones are renamed by the final-check-report skill. Runs on the same day share a workbook; the first run on a new day starts a new one, and earlier days' workbooks are left as they are.

- Every scan (`--report-only`, `--apply-moves`) rebuilds the Summary, Plan and Only-moves sheets.
- Every run of every phase of `organize.py`, and every run of `Cleanup-Pictures.ps1`, appends to two history sheets that are never cleared: **Run log** (one row per reported line: run time, phase, dry run yes/no, action such as `MOVED`, `WROTE`, `DELETED`, `FAILED`, and the detail) and **Run counts** (each phase's counts). Dry runs (any run without `--apply` or `-Apply`) are recorded too, marked `yes` in the Dry run column. A dry run never renames an older audit workbook.
- The PowerShell scripts record through `Write-AuditLog.ps1`, which needs Python with `openpyxl`: `python` on PATH, or the `py` launcher.
- If the workbook is open in Excel the run still happens but cannot be recorded; the output says `This run is NOT recorded in the audit workbook`. Tell the user to close it before the next phase.

End the response with:

1. A short summary of counts (extensions corrected, dates written, files converted, files moved, timestamps synced, files flattened and empty folders moved to `_empty_folders`, ad files quarantined, incomplete files moved, junk files moved to `_junk`).
2. If the user has not run it, ask whether they want to clean up converted files (`.\Cleanup-Pictures.ps1` from `<MediaRoot>`), which deletes PNGs and BMPs already converted to JPEG.
3. A link to the audit XLSX.

## Safety rails

- Ask before each phase that writes, moves, or deletes.
- On first contact with an unfamiliar folder, start with `--report-only`, and run every step without `--apply` before running it with `--apply`.
- Never rename or move files outside `<MediaRoot>`.
- When converting PNG or BMP → JPEG, never delete the original in the same step — leave removal to `Cleanup-Pictures.ps1` so the user sees it.
- Date-writing is destructive to EXIF; back up before Phase 3 on precious photo and video libraries.
- `organize.py` deletes nothing. `.AAE` sidecars, `Thumbs.db` thumbnail caches, macOS `._` sidecars and `.modd`/`.moff` sidecars whose file is gone are moved into `_junk`, never deleted. Deleting that folder is the user's call.
- The only step that deletes is "Clean up converted files" (`Cleanup-Pictures.ps1 -Apply`), and only PNGs and BMPs whose JPEG is confirmed to be the same picture.
- Incomplete files are moved to `_incomplete` in their dated folders, never deleted.
- Ad images and videos are quarantined in `_ads`, never deleted. Deleting that folder is the user's call after they have looked through it.
- Empty folders are moved into `_empty_folders`, never deleted. Deleting that folder is the user's call.
- Timestamp sync only touches files that pass the unedited-heuristic. Edited files are skipped and reported, never silently overwritten.
