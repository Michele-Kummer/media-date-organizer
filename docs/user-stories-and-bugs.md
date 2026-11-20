# User stories and bugs

This document records the requirements for **media-date-organizer** as user stories grouped into epics, followed by every known bug, open and resolved, and who found each one. It is meant as a worked example of how requirements were generated for this project.

**How it was made (2026-10-21)**

- **User stories:** written with Claude Code (Claude Opus 5.5) by reading the plugin's code, docs and git history. Each story's acceptance criteria describe how the plugin behaves today.
- **Open bugs:** found by Claude while writing the stories. Each one was reproduced on synthetic files.
- **Resolved bugs:** taken from the git history. Michele Kummer, the project's author, said which ones they found.
- **Updated 2026-10-22:** Michele Kummer asked for `--all` to fix extensions, for junk to be moved aside instead of deleted, and for the step-by-step run to ask about cleanup. Those gaps are recorded as BUG-26 to BUG-28, and US-31 records the new requirements. US-32 was added at Michele Kummer's request.
- **Updated 2026-10-23:** Michele Kummer found that `--flatten` left the ads in `E:\Pictures\2020\_ads` in their subfolders (BUG-29).
- **Updated 2026-10-23:** Michele Kummer found that `--quarantine-ads` run on `E:\Pictures` put every year's ads in one `E:\Pictures\_ads` (BUG-31), and that `--flatten` then left the ads in `E:\Pictures\_ads\2022` in their subfolders (BUG-30).
- **Updated 2026-10-26:** Claude found, while checking those fixes, that the other steps still went into a year's own `_ads` when run on `E:\Pictures` (BUG-32).
- **Updated 2026-10-26:** Michele Kummer asked for a desktop app: a button for each step, project settings, checkboxes choosing the steps of a full run with a default, PNG and BMP quality settings, **Run all selected** and **Preview all selected**, tooltips, Montserrat, light and dark themes in the SK SkyOrbit logo's colors, and WCAG Level A. Epic 8 (US-33 to US-43) records these requirements. Claude measured the contrast of the logo's colors to choose the theme colors.
- **Updated 2026-10-27:** Michele Kummer asked for the quality options to be a story of their own. US-44 adds them to `organize.py`, and US-38 depends on it. Michele Kummer chose Vue 3 with pywebview for the desktop app, recorded at the top of Epic 8.
- **Updated 2026-11-02:** Michele Kummer asked for moving files to date folders to be optional and left out of `--all`. US-09, US-19, US-26, US-31 and the desktop app's default selection now say so.
- **Updated 2026-11-03:** Michele Kummer asked for ads, incomplete files and junk to go straight into `_ads`, `_incomplete` and `_junk`, with no subfolders. US-12, US-13 and US-14 now say so. Michele Kummer then asked for the folder's date to be added to the name of any that have no Date Taken (US-46, built the same day), and for a desktop app setting, built with the app, that chooses whether they are flattened (US-45).
- **Updated 2026-11-03:** Michele Kummer found thousands of photos named only by a number (`46.jpg`, `47.jpg`) in `Pictures\2026` after an import and asked whether they were duplicates. Claude found they were a phone's gallery thumbnails, given their folder's date and then flattened in among the photos (BUG-33). US-14 now sets them aside in `_thumbnails`.
- **Updated 2026-11-08:** Michele Kummer listed more names that are ads: kids' app button images ending `_over@2x`, a plant-ID app's files starting `glority_cach` and colour swatches such as `2#xff0000ff#0#1` (US-47).
- **Updated 2026-11-08:** Michele Kummer asked for sample data to show a before and after. US-48 records the generator, which replaces the old three-file sample set. Michele Kummer then asked for the good photos in `After` to be flattened into year folders.
- **Updated 2026-11-09:** Michele Kummer asked for no spaces in file and folder names. US-49 records the names the sample generator writes with spaces, built the same day.
- **Updated 2026-11-09:** Claude checked the new screenshots against the sample data. Michele Kummer fixed the captions and asked for the panels to show the same columns and for the README to explain what a reader may wonder about (US-50).
- **Updated 2026-11-13:** Michele Kummer asked for plist and XMP files to be moved into `_junk` instead of only being reported. US-14 and US-28 now say so. Michele Kummer then asked, as part of the desktop app's design, for a setting for each kind of junk (US-51), incomplete file (US-52) and ad (US-53).
- **Updated 2026-11-14:** Michele Kummer found that `--move-junk` sets phone thumbnails aside before any date is written, so they leave their dated folder with no date, and that it does so on every run with no way to opt out (BUG-34). Michele Kummer asked for the move to be undone and for setting thumbnails aside to become an optional slash command of its own, run after dates are applied (US-54, built the same day).
- **Updated 2026-11-14:** Michele Kummer found that `--flatten` on `E:\Pictures\2022` left the photos in `Temp\<number>` folders where they were, because it only looked one subfolder deep (BUG-35). Michele Kummer asked for flatten to go all the way down, but only through dated folders and folders named Temp, Junk, Delete, Weird or Review, leaving folders named for a child, a trip or a wedding as they are (US-55, built the same day). Michele Kummer then asked for the desktop app to let the user list the folder names to flatten, with an option for all folders (US-56).
- **Updated 2026-11-14:** Claude suggested more names that usually hold photos waiting to be sorted, and Michele Kummer asked for all of them to be flattened too: New folder, DCIM and the camera folders inside it (`100APPLE`), Camera, Unsorted, To Sort, Misc, Downloads and Import. US-55 and US-56 now list them.
- **Updated 2026-11-14:** Michele Kummer asked why three WebP pictures in `E:\Pictures\2022\Temp\2022-05-08` were not given the date in their names. Claude found that `--fill-blanks` writes no date into WebP, and Michele Kummer asked for WebP to be converted to dated JPEGs (US-57, built the same day).
- **Updated 2026-11-14:** Michele Kummer asked for the cleanup step to include WebP, and for it to move every converted PNG, BMP and WebP into `_converted` instead of deleting it (US-58, built the same day). No step deletes files any more; US-11, US-21, US-29, US-31, US-34, US-36 and US-57 now say so.
- **Updated 2026-11-15:** Michele Kummer found that `--move-incomplete` ran much more slowly than the other steps. Claude traced it to the null-byte check reading 1 MB of every photo (BUG-36).
- **Updated 2026-11-15:** Michele Kummer found that `--sync-timestamps` on `E:\Pictures\2020` stopped with `OSError: [Errno 22]`, and that the photo it stopped on, `VideoCapture_20200614-211024.jpg`, had not been given the date in its name. Claude found its Date Taken was the placeholder 1904-01-01 00:00:00, and that Python on Windows cannot convert any date before 1970 (BUG-37). Michele Kummer asked for the placeholder to count as blank, for a date that cannot be synced to be logged as failed, and for scanned photos older than 1970 to be supported.
- **Updated 2026-11-15:** Michele Kummer asked why a second `--sync-timestamps` run synced almost every file again. Claude found that the step never compared a file's times with its Date Taken before writing them (BUG-38).
- **Updated 2026-11-15:** Michele Kummer asked why `--fix-extensions` took so long. Claude timed a preview on `E:\Pictures\2026`, a USB hard drive: 258 seconds the first time and 0.6 seconds the second, and found that it can open each file up to four times. Michele Kummer asked for it to open each file only once (US-59).
- **Updated 2026-11-15:** Michele Kummer found that many 1 KB files in `E:\Pictures\2018\Temp` were not moved to `_incomplete`. Claude found that all 451 of them are MTP property lists left by a failed phone transfer, with no picture in them, and that `--move-incomplete` did not recognise them (BUG-39, fixed the same day).
- **Updated 2026-11-20:** Michele Kummer asked for screenshots and backup thumbnails to be sorted out of the photos into groups of their own, in an optional step that deletes nothing, recognised by the formats Claude knows of (US-60, built the same day). While building it, Claude found that writing a date into a PNG, or converting a PNG to JPEG, dropped its XMP, and with it the tag that marks an iPhone screenshot (BUG-40, fixed the same day).
- **Updated 2026-11-20:** Michele Kummer found that `1000000714.jpg` in `E:\Pictures\2024`, a phone gallery thumbnail, was not set aside by `--move-thumbnails`. Claude found that Android 11 and later number media from 1000000000, so the name has 10 digits, while the step only accepted 1 to 7 (BUG-41, fixed the same day).

**Status** on each story is *Done* when every criterion holds, *Partly done* when some do not, with the gap named, or *Not started* when it is a requirement not yet built.

Each epic below can be expanded and collapsed.

**Who the stories are for**

- **Media owner:** someone on Windows with folders of photos and videos from phones, cameras and apps, who wants Explorer to show the right date on every one. Used for stories that cover both photos and videos.
- **Photo owner:** the same person, in stories that only cover photos.
- **Maintainer:** whoever changes or tests the plugin.

Each bug says what it **Affects**: photos, videos, both, or something other than media files (setup, the audit workbook).

## At a glance

| | Count |
|---|---|
| Epics | 8 |
| User stories | 60 (39 Done, 2 Partly done, 19 Not started) |
| Bugs | 41 (3 open, 38 resolved) |

| Bugs found by | Open | Resolved | Total |
|---|---|---|---|
| Michele Kummer | 1 | 20 | 21 |
| Claude | 2 | 18 | 20 |
| Automated tests | 0 | 0 | 0 |

---

## Part 1 — User stories

<details>
<summary><strong>Epic 1 — Setup and getting started</strong> (US-01 to US-03)</summary>

Install the plugin, learn what it needs, and find out what it can do.

#### US-01 Install the plugin
As a media owner, I want to install the plugin with one command, so that I can start organizing my photos and videos without copying files around.

- `/plugin install media-date-organizer --marketplace Michele-Kummer/media-date-organizer` installs 3 skills and 4 slash commands.
- Requires Claude Code 2.1.275+, Python 3.9+, `pillow>=10.0`, `openpyxl>=3.1`, and Windows PowerShell 5.1+ or PowerShell 7.
- `/plugin marketplace update michele-kummer` picks up a newer version.

**Status:** Done

#### US-02 Be told what is missing
As a media owner, I want a clear message when something the plugin needs is missing, so that I know what to install instead of seeing a crash.

- Python older than 3.9: the script stops with "Python 3.9 or later is needed".
- No Pillow: a warning with the `pip install "pillow>=10.0"` command. Writing photo EXIF, converting PNG and checking for ads are refused.
- No openpyxl: scanning still works. The audit workbook is skipped, with a message saying so.
- No ExifTool: HEIC photos and videos that need a date are listed as `SKIPPED (needs exiftool)`. ExifTool is found on PATH or in winget's default folder.
- No ffmpeg: comparing videos is refused, with the `pip install "imageio-ffmpeg>=0.5"` command. Photos are still compared.
- The PowerShell scripts find Python as `python`, or through the `py` launcher. They ignore the Microsoft Store stub. With neither available, they say the run was not recorded.

**Status:** Done

#### US-03 See what I can ask for
As a media owner, I want to see everything the plugin can do, with what to type for each, so that I don't have to read the README.

- `/media-help` lists every command and plain-language request with an example. It changes nothing.

**Status:** Done

</details>

<details>
<summary><strong>Epic 2 — Correct file types and dates</strong> (US-04 to US-08, US-29, US-44, US-57, US-59)</summary>

Make every photo and video report its real format and its real date, and make Windows Explorer show it.

#### US-04 Correct wrong extensions on photos and videos
As a media owner, I want photos and videos whose extension does not match their content renamed, so that every tool reads them correctly.

- `organize.py --fix-extensions` reads the start of every file named as a photo or video, or with no extension, in the folder and every subfolder, and recognises:
  - photos: PNG, JPEG, HEIC/HEIF, GIF, WEBP, TIFF and BMP;
  - videos: MP4/MOV, 3GP/3G2, M2TS/MTS, MPG, WMV and AVI.
- A mismatched extension is corrected, for example a `.PNG` that is really HEIC, or a `.HEIC` that is really a QuickTime video. 3GP/3G2 keep their own extension, and the extension keeps its case.
- `--all` runs it first (BUG-26).
- A name that is already taken is a `COLLISION`, and both files are left alone. Other files, such as an `.m4a` song, are never renamed.
- Empty files are listed as `EMPTY`. Unrecognised photo and video files are listed as `UNKNOWN FORMAT`, including a container brand it does not know (a HEIF burst, an AVIF photo), which is left alone rather than renamed to `.mp4` (see BUG-04). Sony `.modd`/`.moff` video sidecars are left alone.
- It lists the renames and changes nothing unless `--apply` is given (US-27).
- It is the only extension fixer. The PowerShell version, `Fix-Extensions.ps1`, was moved to `_review` so there is one set of rules to maintain.

**Status:** Done

#### US-05 See which photos and videos have no date
As a media owner, I want a report of every photo's and video's real date and what would happen to it, so that I can decide before anything changes.

- The step is called **Audit dates**. `--audit` reads photo dates from EXIF (JPEG, PNG and TIFF, and the EXIF embedded in HEIC) and video dates from the MOV/MP4 container. It needs no external tools.
- `--report-only`, the flag's old name, still works, so older command lines keep running.
- Photos and videos are found in the root and every subfolder at any depth, skipping `_ads`, `_incomplete` and `_empty_folders`.
- Each file is given an action: keep, move, fill-blank or skip. A file loose in a root named for a different date is listed as `in-root-date-differs`. The results are written to the audit workbook.
- The fill-blank date is the one `--fill-blanks` would write: for a photo, its filename or its own folder's name; for a video, its filename or the nearest folder whose name holds a full date.
- Nothing is changed.

**Status:** Done

#### US-06 Fill in missing Date Taken on photos
As a photo owner, I want photos with a blank Date Taken to get one from the best evidence available, so that they sort correctly.

- Looks at the root and every subfolder at any depth, skipping `_ads`, `_incomplete` and `_empty_folders`.
- The date comes from the filename (`IMG_20190830_101500`), else from the containing folder's name (`2019-08-30`, `2026-08-19 11-44-31`, `08-19-2026`, `Aug 19 2026`) at 12:00:00.
- The file's modified time is never used, because copying and importing resets it.
- A Date Taken of exactly 1904-01-01 00:00:00 counts as blank. It is the QuickTime time zero that some apps write when they have no date, such as Windows frame grabs named `VideoCapture_20200614-211024.jpg` (BUG-37).
- JPEGs get their EXIF block replaced without re-encoding the picture. HEIC is written with ExifTool.
- Empty files are skipped and counted.
- Without `--apply` it lists what would be written (US-27).

**Status:** Done

#### US-07 Fill in missing Media Created on videos
As a media owner, I want videos with a blank Media Created to get a date, so that they sort with the photos from the same day.

- MOV, MP4, M4V, 3GP and 3G2 are covered.
- The date comes from the filename, else from the nearest containing folder whose name holds a full date. A year-only folder (`2014`, `2013 West`) is never used.
- Videos with no date source are listed as `SKIPPED (no date in filename or folder names)`.
- Written with ExifTool, converting local time to the UTC the container stores.

**Status:** Done

#### US-08 Make PNG dates visible in Explorer
As a photo owner, I want PNG screenshots converted to JPEG, so that Windows Explorer shows their Date Taken.

- Converts at quality 95 and keeps the EXIF.
- PNGs with any transparent pixel stay PNG. So do Snapchat `*-overlay.png` caption layers.
- A `.png` that cannot be read is reported as `FAILED to convert` and the rest still convert. A half-written JPEG is removed.
- The original PNG is left for the cleanup script (US-11).
- Without `--apply` it lists each PNG that would be converted (`WOULD CONVERT`) and writes nothing. Claude adds `--apply` only after the user confirms.

**Status:** Done

#### US-29 Give BMP pictures a date
As a photo owner, I want my BMP pictures turned into JPEGs with the right Date Taken, so that they sort with my other photos. A BMP has no field for a date, so it can never show one as it is.

- `--convert-bmp` converts each BMP in the folder and every subfolder to a JPEG of the same name at quality 95. The picture is unchanged.
- The JPEG gets the date `--fill-blanks` would use: the date in the filename (`IMG_20210503_101500.bmp`), else the folder's date at 12:00:00. Moving and flattening then treat it like any other photo.
- A `.bmp` that is really another format is reported as `NOT A BMP` and left alone. BMPs with transparent pixels stay BMP.
- The original is left in place. `Cleanup-Pictures.ps1` moves it into `_converted` only once the JPEG is confirmed to be the same picture (same size, pixels within 1%), as for PNGs (US-11, US-58).
- Not part of `--all`; add `--convert-bmp` to include it. It previews unless `--apply` is given. `--fill-blanks` ends with a `NOTE` pointing to it when it skipped BMPs.
- `tests/test_bmp_and_ads.py` covers conversion, the date, a misnamed BMP and the cleanup.

**Status:** Done

#### US-44 Choose the JPEG quality for PNG and BMP conversions
As a photo owner, I want to set the JPEG quality that PNG and BMP conversions use, so that I can choose between smaller files and pictures closer to the original.

- `--png-quality N` sets the quality `--convert-png` uses, and `--bmp-quality N` the quality `--convert-bmp` uses. N is a whole number from 1 to 100. Without them, both stay at 95, as today.
- A value that is not a whole number from 1 to 100 stops the run before anything changes, with a message giving the allowed range.
- `--all` passes `--png-quality` on to its PNG conversion.
- The preview (`WOULD CONVERT`) and the audit workbook give the quality each file was, or would be, converted at.
- `--help`, the README, the cheat sheet, the `media-date-organizer` skill and `/fix-media-dates` describe both options, and say that JPEG drops some detail at any quality below 100.
- Converting the test pictures at falling qualities finds the highest quality at which `Cleanup-Pictures.ps1` no longer counts the JPEG as the same picture (more than 1% apart, US-11). The README states it, and the app's quality note uses it (US-38).
- Tests cover the default, each option, a value out of range, and that the picture is saved at the quality given.
- The desktop app's quality settings (US-38) depend on this story.

**Status:** Not started

#### US-57 Give WebP pictures a date
As a photo owner, I want my WebP pictures turned into JPEGs with the right Date Taken, so that they sort with my other photos. WebP pictures come from saving an image from a web page or a messaging app, usually carry no date, and `--fill-blanks` cannot write one into them. Three WebPs in `E:\Pictures\2022\Temp\2022-05-08` named `IMG_20220508_185526_425.webp` were left with no Date Taken, although the date was in their names.

- `--convert-webp` converts each WebP in the folder and every subfolder to a JPEG of the same name at quality 95. The picture keeps its size.
- A Date Taken already in the WebP is kept. Otherwise the JPEG gets the date `--fill-blanks` would use: the date in the filename (`IMG_20220508_185526_425.webp` gives 2022-05-08 18:55:26), else the folder's date at 12:00:00. A WebP with neither is still converted, with no date.
- Animated WebPs and WebPs with transparent pixels stay WebP and are listed as `SKIPPED`, since a JPEG would keep one frame and lose the transparency. A `.webp` that is really another format is reported as `NOT A WEBP` and left alone.
- A JPEG already holding the name is never overwritten. The WebP is listed as `SKIPPED (<name>.jpg already exists)` and stays.
- The original is moved, not deleted: once the JPEG is confirmed to be the same picture (same size, pixels within 1%), the WebP moves straight into `_converted` inside the folder, with no subfolders. A name already there gets its folder's name added. If the JPEG does not match, the WebP stays where it is and is listed as `KEPT`. `Cleanup-Pictures.ps1` moves any WebP still beside a matching JPEG the same way (US-58).
- Every step skips `_converted`, and the final check reports what is in it (`IN CONVERTED`).
- Not part of `--all`; add `--convert-webp` to include it. It runs before `--fill-blanks`, and previews (`WOULD CONVERT`, `WOULD MOVE`) unless `--apply` is given. `--fill-blanks` ends with a `NOTE` pointing to it when it skipped WebPs.
- `tests/test_webp.py` covers the preview, the conversion, each source of the date, animated and transparent WebPs, a misnamed WebP, a JPEG already holding the name, a name already in `_converted`, a second run, the same-picture check, and the final check.

**Status:** Done

#### US-59 Fix extensions opens each file only once
As a media owner, I want `--fix-extensions` to open each photo and video only once, so that it finishes sooner on a slow drive. A preview on `E:\Pictures\2026` (3,622 files on a USB hard drive) took 258 seconds the first time and 0.6 seconds when run again, so almost all the time goes on reaching each file on the disk. Today `fix_extensions` can open the same file up to four times: `detect_type` reads 16 bytes, `_detect_format` opens it again for 200 bytes when the format is not a common one, `_unknown_ftyp_brand` opens it again for 12 bytes when the result is MP4, and `not_media_kind` calls `detect_type` again and then reads 1 KB.

- `fix_extensions` opens each file once, reads its first 1 KB, and makes every check on those bytes: the AppleDouble signature, the format (`detect_type` and the camcorder and older video formats in `_detect_format`), the container brand, and plist or XMP text.
- `detect_type`, `_detect_format`, `_unknown_ftyp_brand` and `not_media_kind` can each be given bytes already read, so other steps can share them. Called with a path, as today, they behave as before.
- The size check uses the bytes read where it can, and a file that cannot be opened is still reported as `FAILED` and does not stop the run.
- The results are the same as today: the same renames, `COLLISION`, `EMPTY`, `UNKNOWN FORMAT` and `NOT MEDIA` lines, and the same counts.
- Tests check that each file is opened only once, and that the existing tests in `tests/test_fix_extensions_and_junk.py` and `tests/test_dry_run.py` still pass.
- The step is timed again on `E:\Pictures\2026` from a cold start (the drive just connected, or the PC just restarted), with digiKam closed, and the time is recorded here. The gain may be small, because the slow part is reaching each file the first time, and later opens of the same file are served from memory.

**Status:** Not started

</details>

<details>
<summary><strong>Epic 3 — Organize folders</strong> (US-09 to US-11, US-55, US-58)</summary>

Put each photo and video where its date says it belongs, then tidy the folder structure.

#### US-09 Move photos and videos to the folder for their date
As a media owner, I want each photo and video in a folder named for its real date, so that folder names can be trusted.

- `--apply-moves` moves a photo or video whose date differs from its folder's date into a sibling `YYYY-MM-DD` folder.
- The step is optional. It is not part of `--all`; add `--apply-moves` to include it.
- Works at any depth. Each file is checked against the folder it sits in, and moves to a sibling of that folder: `Trip\2019-08-30\x.jpg` taken on the 31st moves to `Trip\2019-08-31`, not up to the root.
- A file loose in the root is never moved out of it. It is checked against the root's own name; if that is a different date, it is listed as `in-root-date-differs` and left where it is.
- A file with no date inside it, in a dated folder, gets that folder's date appended to its name (`IMG_1_2019-08-30.jpg`), so the date survives a later move.
- A name already taken at the target is skipped as a `COLLISION` and never overwritten.
- Without `--apply` it lists each move (`WOULD MOVE`) and rename, creates no folder, and reports the same collisions a real run would meet.

**Status:** Done

#### US-10 Flatten dated subfolders
As a media owner, I want every dated photo and video moved up into the media folder itself, so that I have one flat folder per year.

- `--flatten` (or `/flatten-media`) moves photos and videos that have a date up out of their subfolders, at any depth (BUG-35). A name already taken in the root gets a `_<date-taken>` ending.
- Only dated and scratch folders are flattened; named folders are left as they are (US-55).
- Camcorder, MPEG, WMV and AVI videos move too, going by the date in the filename, else the nearest dated folder above them. The date is appended to the name when it came from a folder.
- Inside `_ads`, files in subfolders at any depth, game `.raw` ads included, move up into `_ads` itself, dated or not. The same holds when the root given is an `_ads` folder itself (`E:\Pictures\2020\_ads`), whose emptied subfolders go into the `_empty_folders` beside it (BUG-29). It also holds for a root anywhere inside an `_ads` folder (`E:\Pictures\_ads\2022`), whose emptied subfolders go into its own `_empty_folders` (BUG-30).
- Subfolders left empty are moved into `_empty_folders`, keeping their path. Nothing is deleted.
- Without `--apply` it only previews.

**Status:** Done

#### US-11 Remove leftover PNGs after conversion
As a photo owner, I want the PNG left behind by a conversion removed, and empty folders set aside, so that the folder is clean.

- `Cleanup-Pictures.ps1` moves a PNG into `_converted` only when it has already been converted to JPEG. BMPs and WebPs are handled the same way (US-58). Nothing is deleted.
- **Which files are paired:** each `.png` with a `.jpg`, else a `.jpeg`, of the same base name in the same folder. Letter case does not matter (`IMG_1.PNG` pairs with `img_1.jpg`). Files in different folders are never paired.
- **How the two pictures are compared**, in two checks, both through .NET's `System.Drawing` (a WebP is decoded by the Windows Imaging Component first, US-58):
  1. **Size.** Only each file's header is read, to get its width and height in pixels. They must match, and the JPEG must not be empty. `--convert-png` keeps the size, so a real conversion always matches.
  2. **Pixels.** Both pictures are decoded and shrunk to 128x128, and the mean difference of their red, green and blue values is taken as a percentage (0 = same picture). This is the same measure as `--visual-compare`, and gives the same score to within 0.02%. The PNG counts as converted at **1% or less**, which `--visual-compare` calls `DUPLICATE` with high confidence. `-MaxPixelDifference` changes the limit.
  - Measured on test pictures: a converted screenshot scores 0.01% and a converted photo-like picture 0.03%. A different screenshot of the same size scores 12–35%. Random per-pixel noise, the hardest case for JPEG, scores 1.7% after conversion, so it is kept unless the limit is raised to 2.
  - File size, EXIF dates and modified times are not compared.
- **When they differ:** a different size, a difference over the limit, or a file that cannot be read means the files are treated as different pictures. Both are kept, and the PNG is listed with the reason: `KEPT (not the same picture, PNG 1170x2532, JPG 4032x3024)`, `KEPT (not the same picture, pixel difference 11.9%)`, or `cannot read picture size` / `cannot read pixels`.
- Every other file that shares a name is kept: a Live Photo video next to its photo, a sidecar (`.xmp`, `.aae`), or a HEIC next to a JPG.
- `_ads`, `_incomplete`, `_no-image-data`, `_junk`, `_thumbnails`, `_converted` and `_empty_folders` are skipped.
- Empty folders are moved into `_empty_folders`, keeping their path.
- It previews unless `-Apply` is given. The console, the summary and the audit workbook all list each PNG moved (or that would be) and each one kept.

**Status:** Done

#### US-55 Keep named folders when flattening
As a media owner, I want flatten to empty my dated folders and my scratch folders such as `Temp`, at any depth, but leave folders I named for a child, a trip or a wedding as they are, so that one run flattens the year without breaking up the folders I made on purpose.

- `--flatten` goes into three kinds of subfolder, at any depth:
  - a dated folder: any name holding a full date (`2022-02-14`, `Aug 19 2023`, `Trip 11-11-2019`);
  - a scratch folder: a name holding one of these words or phrases as a whole word, in any case: Temp, Junk, Delete, Weird, Review, New folder, DCIM, Camera, Unsorted, To Sort, Misc, Download, Downloads, Import, Imports or Imported (`Temp`, `temp2`, `To Delete`, `Weird ones`, `To Review`, `New folder (2)`, `Camera Roll`, `Imported 2022`). A space, underscore or dash may join a phrase (`to_sort`, `NewFolder`). Not `Template`, `Junkyard`, `Sorted`, `Important` or a name starting with an underscore (`_review`, `_duplicates`), which is a folder things were set aside in on purpose;
  - a camera's or phone's own folder inside `DCIM`, named by the camera file standard: 3 digits from 100, then 5 letters, digits or underscores (`100APPLE`, `101ANDRO`, `100_PANA`);
  - every folder below a scratch folder, whatever its name (`Temp\5`, `Temp\2022-02-14\7`).
- Every other folder is a named folder (`Emma`, `Hawaii`, `Wedding`, or `2022-03-01\Emma` inside a dated folder). It is left exactly as it is, with everything inside it, its dated subfolders and empty subfolders included, and listed as `KEPT (named folder): Wedding (40 file(s))`, counted as `named-folders-kept`.
- A named folder holding no file at any depth is set aside in `_empty_folders`, like any other empty folder.
- The final check lists a named folder as `NAMED FOLDER (left as is)`, counted as `named-folders`, not as `NOT FLATTENED`, so it does not make a year look unfinished.
- The name clash checks (`--compare-collisions` and the final check) look at the same folders as `--flatten`.
- A test in `tests/test_smoke.py` flattens a year folder with files two and three levels down in `Temp`, each scratch name, named folders at the top and inside a dated folder, `Template`, `_review` and an empty named folder, then runs the final check.

**Status:** Done

#### US-58 Set converted originals aside instead of deleting them
As a photo owner, I want the PNG, BMP or WebP left behind by a conversion moved into `_converted` rather than deleted, so that I can look at the originals before I throw them away, and so that cleanup covers WebP too.

- `Cleanup-Pictures.ps1` pairs each `.png`, `.bmp` and `.webp` with a `.jpg`, else a `.jpeg`, of the same name in the same folder, and checks them as in US-11: same size, pixels within 1%.
- A matching original moves straight into `_converted` in the folder cleaned, with no subfolders, as `--convert-webp` does: `MOVED (converted to scan.jpg): 2021-05-04\scan.bmp -> _converted\scan.bmp`. A name already there gets its folder's name added (`scan_2021-05-04.bmp`). When that is taken too, the original stays and is listed as `COLLISION, skipping`. Nothing is deleted.
- `System.Drawing` cannot read WebP, so a WebP is decoded through the Windows Imaging Component, which reads it with the WebP Image Extension that comes with Windows 11. A WebP it cannot read is listed as `KEPT (not the same picture, cannot read picture size)` and stays.
- `--convert-webp` still moves each WebP it converts into `_converted` itself. Cleanup catches any WebP still beside a matching JPEG.
- The summary gives `Converted PNGs, BMPs and WebPs moved : N (into _converted)`, the pairs kept, and any names taken in `_converted`. It previews (`WOULD MOVE`) unless `-Apply` is given.
- `CleanupConvertedTests` in `tests/test_bmp_and_ads.py` covers the preview, a PNG, BMP and WebP moving, a WebP whose JPEG differs, a name taken once and twice in `_converted`, and pairs inside `_converted` being left alone.

**Status:** Done

</details>

<details>
<summary><strong>Epic 4 — Clear out files that aren't real photos or videos</strong> (US-12 to US-14, US-30, US-46, US-47, US-54, US-60)</summary>

Move ads and broken files out of the way, and delete files that hold no picture or recording.

#### US-12 Set ad images and videos aside
As a media owner, I want ad and app-cache images and videos moved out of my media folders, so that I can review and delete them in one place.

- `--quarantine-ads` moves photos and videos with an ad-style name and no camera information into `_ads`. Examples of ad-style names: a UUID, `UnityAdsCache-<hash>`, `news_images%2F…`.
- Camera information is EXIF Make/Model on a photo, or a device-make tag on a video. A file that has it is never treated as an ad.
- Run on the folder that holds the year folders (`E:\Pictures`), an ad in a year folder goes into that year's own `_ads` (`2022\_ads`). Only ads in other folders, or loose in the root, go into the root's `_ads`. Ads already in an `_ads` folder at any depth are not moved again (BUG-31), and the other steps leave a year's own `_ads` alone (BUG-32).
- Ads go straight into `_ads`, with no subfolders. An ad with no Date Taken gets its folder's date in its name (`2022\Temp\2022-02-14\ad.png` → `2022\_ads\ad_2022-02-14.png`, US-46). Any other name already in `_ads` gets a `_<subfolder-name>` suffix. If the new name is taken too, the file stays where it is and is listed as a `COLLISION`.
- Nothing is deleted. Without `--apply` it only previews.

**Status:** Done

#### US-30 Recognise game ads by name
As a media owner, I want the game ads that phones save among my pictures recognised as ads, so that `--quarantine-ads` clears them out of my dated folders too.

- Found in `E:\Pictures\2023`, where they were the only files left in the dated folders after flattening. These name forms are now ads (each may carry a `_YYYY-MM-DD` ending or a ` (2)` copy marker):
  - an id, a 13-digit millisecond time and a 5-character id: `492887-1648448524975-3d62u.webp`;
  - a CDN address saved as the name: `__d2duuy9yo5pldo.cloudfront.net_codigames_<uuid>.gif`;
  - 8, 7 and 16 letters and digits joined by `_`: `lbay6fy2_fftxeca_itehyhqsmpyyszx7.gif`;
  - `icon.webp`;
  - for `.raw` only, `draw_` plus a word: `draw_title.raw`. A camera RAW, recognised by its header, is kept.
- The camera check still applies: a name match with camera information is kept.
- There is no rule for numbered BMPs (`8824_1269.bmp`, `imagebmp (5).bmp`, `37038.bmp`). In this library they are as often the user's own pictures as game ads, and the name cannot tell them apart. Numbered BMPs that are ads are moved to `_ads` by hand.
- On `E:\Pictures\2023` it moved all 13 leftovers that are not BMPs into `_ads`, plus 9 loose JPGs with the same names. The run also included the 3 numbered BMPs, under a BMP rule that has since been removed.
- `tests/test_bmp_and_ads.py` checks every name above, and that camera, phone and screenshot names are not matched.

**Status:** Done

#### US-13 Set incomplete files aside
As a media owner, I want failed copies moved out of the way, so that they stop showing up as photos or videos with no date.

- `--move-incomplete` moves files that are 0 bytes or all null bytes, phone transfer stubs (a small MTP property list saved under the photo's name, with no picture in it, BUG-39), and videos with no video header, straight into `_incomplete`, with no subfolders. Each one under a dated folder gets that date in its name, unless its name holds a date already (`2020-01-02\clip.mp4` → `_incomplete\clip_2020-01-02.mp4`, US-46). If that name is taken, the file stays where it is and is listed as a `COLLISION`.
- Files in the older `_no-image-data` folder are folded into `_incomplete`, flat.
- Nothing is deleted. Without `--apply` it only previews.

**Status:** Done

#### US-14 Set leftover sidecar files aside
As a media owner, I want files that hold no picture or recording moved out of my media folders, but not deleted, so that they don't clutter the folders and I can still get one back.

- `--move-junk` moves `.AAE` iPhone photo-edit files, `Thumbs.db`/`ehthumbs*.db` thumbnail caches, macOS `._` sidecars, and `.plist` and `.xmp` files straight into `_junk`, with no subfolders. Nothing is deleted (BUG-27).
- It also moves files with a photo or video name that hold plist, XMP or other XML text (`IMG_E5239.JPG`, US-28) into `_junk`, listed as `MOVED (plist file named .JPG)`. They are found by their content, so a real photo is never moved this way.
- A `._` file is treated as junk only when its contents carry the AppleDouble signature.
- Thumbnail caches are matched by whole file name only, so `west sucking thumb.jpg` is safe.
- A name already taken in `_junk` (every folder's `Thumbs.db`, say) gets a `_<subfolder-name>` suffix (`Thumbs_2020-01-02.db`), in the preview too. If that is taken as well, it is a `COLLISION`, and the file stays where it is.
- `--flatten` moves Sony `.modd`/`.moff` sidecars whose file is gone into `_junk` too.
- Phone gallery thumbnails are left where they are, so `--fill-blanks` can give them their folder's date. `--move-thumbnails` sets them aside afterwards (US-54, BUG-34).
- The final check reports what is still in `_junk` (`IN JUNK`). `--delete-junk` still works as the old name of the flag, and moves too.
- Without `--apply` it only lists the files.

**Status:** Done

#### US-46 Keep the folder's date on undated files that are set aside
As a media owner, I want an ad or incomplete file with no Date Taken to carry its folder's date in its name when it is moved into `_ads` or `_incomplete`, so that flattening does not lose the only date it had.

- When `--quarantine-ads` or `--move-incomplete` moves a photo or video with no Date Taken (Media Created for a video), the date from the nearest folder above it whose name holds a full date (`2018-08-19`, `7-17-2014`) is appended to its name: `2018-08-19\clip.mp4` becomes `_incomplete\clip_2018-08-19.mp4`.
- A file with a Date Taken keeps its name.
- A name that already holds a date keeps its name.
- A file with no Date Taken and no dated folder above it keeps its name.
- A name still taken in the holding folder is a `COLLISION`, and the file stays where it is.
- Junk (`.AAE`, `Thumbs.db`, `._` sidecars) is not a photo or video and has no Date Taken, so it keeps its name, with the `_<subfolder-name>` suffix only on a clash (US-14).
- The preview lists every new name before anything moves.
- Tests cover an undated file in a dated folder (and one deeper inside it), a dated file, a name that already holds a date, an undated file with no dated folder, and a name clash.

**Status:** Done

#### US-47 Recognise app button, cache and colour images as ads
As a media owner, I want the button images, cache files and colour swatches that kids' and plant-ID apps save among my pictures recognised as ads, so that `--quarantine-ads` clears them out too.

- Michele Kummer listed these names as ads. These name forms are now ads (each may carry a `_YYYY-MM-DD` ending or a ` (2)` copy marker):
  - any name ending `_over@2x`: `TwfUQw2t_over@2x`, `scribble2mammoth_over@2x`, `playdatemlponypartyofone_over@2x`, `myfirst10monkeysmathapp_over@2x`, `jFnHbUHN_over@2x`;
  - anything starting `glority_cach`: `glority_cache_1656951098314`;
  - a number, `#x` and an 8-digit colour, then optional `#<number>` parts: `2#xff0000ff#0#1`, `32#xffa2defe`.
- The camera check still applies: a name match with camera information is kept.
- `tests/test_bmp_and_ads.py` checks every name above, and that near misses (`over@2x.png`, `button_over.png`, `IMG_1234@2x.png`, `glority_cac.jpg`, `my_glority_cache_1656951098314.jpg`, `32#xffa2de.png`, `photo#1.jpg`) are not matched.

**Status:** Done

#### US-54 Set phone thumbnails aside once they are dated
As a photo owner, I want phone gallery thumbnails set aside only when I ask, and only after they have a date, so that each one keeps its folder's date and I can still compare it with my photos.

- `/move-thumbnails <folder>` (flag `--move-thumbnails`) moves phone gallery thumbnails straight into `_thumbnails`, with no subfolders. A thumbnail is a JPEG named only by a number of up to 10 digits (`1234.jpg`, `1234 (2).jpg`, or `1000000714.jpg` from Android 11 and later, BUG-41), optionally followed by a `_YYYY-MM-DD` suffix, at most 1024 pixels on its long side, with no camera Make or Model.
- Only a thumbnail that already has a Date Taken is moved. One with none stays where it is and is listed as `LEFT (no Date Taken yet; run --fill-blanks first)`, counted as `left-undated`, because every step skips `_thumbnails` and its folder's date would be lost (BUG-34).
- It is optional and not part of `--all`. `--all --move-thumbnails` runs it after `--fill-blanks` and `--convert-png`, and before `--apply-moves` and `--flatten`, whatever order the flags are typed in.
- A name already taken in `_thumbnails` gets a `_<subfolder-name>` suffix (`46_2026-11-03.jpg`). If that is taken as well, it is a `COLLISION`, and the file stays where it is.
- Nothing is deleted, since a thumbnail can be the only copy left of a photo. Without `--apply` it only lists the files. The final check reports what is still in `_thumbnails` (`IN THUMBNAILS`).
- `PhoneThumbnailTests` in `tests/test_fix_extensions_and_junk.py` covers the dry run, the move, an undated thumbnail left in place, a name clash, `--all` leaving thumbnails alone and dating them, `--all --move-thumbnails` moving them with their date, and the final check.

**Status:** Done

#### US-60 Sort screenshots and backup thumbnails into their own folders
As a photo owner, I want screenshots and backup thumbnails separated from my photos in an optional step, so that my pictures are easier to manage and nothing is deleted.

- `/sort-pictures <folder>` (flag `--sort-pictures`) runs `--move-thumbnails` and then `--move-screenshots`. Each can still be run on its own.
- `--move-screenshots` moves screenshots straight into `_screenshots`, with no subfolders. A screenshot is a PNG, JPEG or HEIC with no camera Make or Model that either:
  - is named as phones and computers name screenshots: `Screenshot_20231220-142355.png` (Android, Samsung, Pixel, Xiaomi), `Screenshot (12).png` and `Screenshot 2023-12-20 142355.png` (Windows), `Screen Shot 2023-12-20 at 2.23.55 PM.png` and `Screenshot 2023-12-20 at 14.23.55.png` (Mac), `Screenshot from 2023-12-20 14-23-55.png` (Linux), names starting `screencap`, `Screen Capture` or `ScreenClip`, and a Mac's screenshot names in German, French, Spanish, Italian, Dutch, Swedish, Russian, Japanese and Chinese; or
  - carries the "Screenshot" tag that iOS and macOS write in EXIF UserComment or XMP, which is how an iPhone screenshot named `IMG_1234.PNG` is found.
- A longer word (`Screenshotting the sunset.jpg`), a name that does not start with the word (`My screenshot.png`) and a picture with camera information are not screenshots.
- `--move-thumbnails` now also moves, into `_thumbnails`:
  - backup thumbnails: a JPEG or PNG at most 1024 pixels with no camera Make or Model that is named as a thumbnail (`IMG_1234_thumb.jpg`, `thumb_IMG_1234.jpg`, `IMG_1234.thumb.jpg`, `IMG_1234-thumbnail.png`, `tn_IMG_1234.jpg`) or sits in a thumbnail folder (`.thumbnails`, `Thumbnails`, `.thumbs`, `Thumbs`) at any depth. The marker must be joined to the name by `_`, `-` or `.`, so `west sucking thumb.jpg` and `thumbtack.jpg` are safe. Counted as `moved-backup-thumbnails`;
  - thumbnail cache files, which hold many thumbnails in a format Windows cannot open: `.ithmb` files from an iPhone or iPod backup's `Photo Cache` folder, and Android's `.thumbdata` files. Counted as `moved-thumbnail-caches`.
- Only a screenshot or thumbnail picture that already has a Date Taken is moved. One with none stays where it is and is listed as `LEFT (no Date Taken yet; run --fill-blanks first)`, as in US-54. Thumbnail cache files cannot be dated, so they move as they are.
- It is optional and not part of `--all`. `--all --sort-pictures` runs it after `--fill-blanks` and `--convert-png`, and before `--apply-moves` and `--flatten`.
- A name already taken gets a `_<subfolder-name>` suffix. If that is taken as well, it is a `COLLISION`, and the file stays where it is.
- Nothing is deleted. Without `--apply` it only lists the files. Every step and `Cleanup-Pictures.ps1` skip `_screenshots`, and the final check reports what is in it (`IN SCREENSHOTS`, counted as `screenshot-files`).
- A screenshot PNG already converted to JPEG moves with its JPEG. Run the cleanup step first to have the PNG moved into `_converted` instead.
- `tests/test_sort_pictures.py` covers every screenshot name above, the iPhone tag in PNG and JPEG, near misses, each kind of backup thumbnail and cache file, the dry run, the move, an undated picture left in place, a name clash, `--all` leaving screenshots alone, `--all --move-screenshots` moving them with their date, `--sort-pictures` running both, and the final check.

**Status:** Done

</details>

<details>
<summary><strong>Epic 5 — Check and report, without changing anything</strong> (US-15 to US-18, US-28)</summary>

Reports that show duplicates, misfiled files and anything left over.

#### US-15 Find duplicate photos and videos
As a media owner, I want to know which photos and videos are copies of each other, so that I can free up space.

- `find_duplicates.py --root <folder>` searches at every depth.
- Byte-for-byte copies are reported as `IDENTICAL`.
- Likely copies (re-saved, resized or re-tagged) are reported as `DUPLICATE` or `POSSIBLE`. These are found among files of the same kind (two photos, or two videos) that share a date, a name or a size.
- Photos are compared by their pixels. Videos are compared by four frames and their length, which needs ffmpeg.
- Nothing is moved, renamed or deleted.

**Status:** Done

#### US-16 Check whether a skipped collision is a real copy
As a media owner, I want to know whether a photo or video skipped as a `COLLISION` is the same as the file in its way, so that I know which one to delete.

- `--compare-collisions` lists each pair as `IDENTICAL` or `DIFFERENT`. It also covers files `--flatten` renamed or left behind.
- `--visual-compare` compares the pixels of two photos, or four frames of two videos. It reports `DUPLICATE`, `DIFFERENT` or `UNSURE` with a confidence level, which goes into its own column in the audit workbook.
- Both run entirely on the computer and change nothing.

**Status:** Done

#### US-17 Find photos filed with videos, and videos filed with photos
As a media owner, I want to see photos sitting in my video folders, and videos sitting in my photo folders, so that I can refile them.

- The requirement works both ways:
  - pointed at a video library (`/report-opposite-type D:\Videos`), it lists every photo;
  - pointed at a photo library (`/report-opposite-type D:\Pictures`), it lists every video.
- Whichever kind the folder holds more of decides which kind it is, so no option is needed to choose the direction.
- It gives a count for each year folder, searched at every depth, and lists each misfiled file as `PHOTO IN VIDEO FOLDER` or `VIDEO IN PHOTO FOLDER`. With no year folders, the folder itself is reported as one.
- Nothing is changed.

**Status:** Done

#### US-18 See what is left after organizing
As a media owner, I want one report of everything still needing attention, so that I know when a year is finished.

- `--final-check` on the folder holding the year folders reports, per year folder:
  - files in `_ads`, `_incomplete`, `_junk`, `_thumbnails` and `_converted`;
  - photos among videos, or videos among photos;
  - subfolders not flattened;
  - name collisions;
  - audit workbooks left behind.
- Its only change is renaming audit workbooks so their name includes the folder and media type, and only with `--apply`.

**Status:** Done

#### US-28 Find plist files saved with a photo name
As a media owner, I want to know which of my "photos" are really plist or XMP files, such as an iPhone `.AAE` edit file saved as `IMG_E5239.JPG`, and to have them set aside, so that I can decide whether to keep or delete them, instead of seeing date-writing fail on them.

- `--find-plists` searches the folder at every depth, holding folders included, and lists each file with a photo or video name that holds plist (XML or binary), XMP or other XML text, as `NOT MEDIA (plist file named .JPG): 2023-08-07/IMG_E5239.JPG`. It counts them by kind, and changes nothing.
- Real photos and videos are never listed: they never start with `<` or `bplist`.
- `--move-junk`, and so `--all`, moves them into `_junk` (US-14). Nothing is deleted, so the user still decides.
- Every other step reports these files as `NOT MEDIA (... left for --move-junk)` and skips them. `--fill-blanks` no longer reports `FAILED to write`, `--convert-png` does not try to convert them, and `--apply-moves` gives them no date suffix (BUG-25). `--fix-extensions` reports `NOT MEDIA` instead of `UNKNOWN FORMAT`.
- `tests/test_plists.py` covers each of these.

**Status:** Done

</details>

<details>
<summary><strong>Epic 6 — Workflow, safety and record-keeping</strong> (US-19 to US-23, US-26, US-27, US-31)</summary>

Run the steps together, preview them, never lose a photo or video by surprise, and keep a history.

#### US-19 Run every step in one command
As a media owner, I want one command that runs the routine steps in the right order, so that I don't have to remember it.

- `--all` runs, in order: fix extensions, move junk, move incomplete files, fill blanks, convert PNG, sync timestamps. It deletes nothing.
- `--quarantine-ads`, `--apply-moves` and `--flatten` can be added to it.
- It does not update the audit workbook's Summary, Plan and Only-moves sheets unless `--apply-moves` is added. After `--all --apply` it says to run `--audit` for sheets that show the folder as it is now.
- It ends with one summary of every step's counts and up to 50 problems per step.
- Without `--apply` it previews every step against the folder as it is now, and says that a later step may do more once the earlier ones have run.

**Status:** Done

#### US-20 Match Explorer's dates to the date taken
As a media owner, I want Date Created and Date Modified to match when the photo or video was taken, so that every Explorer column agrees.

- `--sync-timestamps` sets Date Created to the photo's Date Taken, or the video's Media Created, on every dated file at any depth.
- Date Modified is set too, but only on files that look unedited. A photo looks edited when EXIF `DateTime` differs from `DateTimeOriginal` by a minute or more, or when `Software` names a known editor (Photoshop, Lightroom, Snapseed and others). An edited file keeps its Date Modified.
- Date Created is set through the Win32 API. On other systems only Date Modified is synced.
- Dates before 1970, such as scanned old photos, are synced too (BUG-37).
- A file whose date cannot be turned into a file time is listed as `FAILED`, and the rest are still synced.
- A file whose times already match, within 2 seconds, is left alone and counted as `already-synced` instead of being listed, so a second run lists only what changed (BUG-38). The 2 seconds allow for FAT32 and exFAT drives, which store Date Modified in 2-second steps.
- Without `--apply` it lists each file that would be synced (`WOULD SYNC`) and changes no timestamp.

**Status:** Partly done. One unreadable file stops the whole step (BUG-02).

#### US-21 Never delete without saying so
As a media owner, I want photos and videos moved aside rather than deleted, except in steps that say they delete, so that mistakes can be undone.

- `_ads`, `_junk`, `_thumbnails`, `_incomplete`, `_converted` and `_empty_folders` hold what was set aside. Every step skips them.
- No step deletes files. `Cleanup-Pictures.ps1` moves PNGs, BMPs and WebPs already converted to JPEG into `_converted` (US-58), and `organize.py` deletes nothing (BUG-27).
- The README's **Guardrails** section lists every safety rule in one place.

**Status:** Done

#### US-22 Preview before anything changes
As a media owner, I want to see what a step will do before it does it, so that I never lose a photo or video by surprise.

- Every step that changes files previews by default, and changes files only with `--apply` (US-27). That includes `--convert-png`, `--apply-moves`, `--sync-timestamps` and `--all`, which had no preview before.
- Claude previews each changing step and asks before going ahead. The slash commands do the same (US-26).
- A preview changes nothing, not even the audit workbook's name (BUG-05).

**Status:** Done

#### US-23 Keep a history of everything done to a folder
As a media owner, I want a record of every step run on a photo or video folder, so that I can see later what changed and when.

- The workbook is named `<folder>_<photos|videos>_media_audit_<date>.xlsx`, in the media folder. Whichever kind the folder holds more of picks `photos` or `videos`. Runs on the same day share it.
- Every step appends to the Run log and Run counts sheets. That includes dry runs (marked `yes` in the Dry run column) and both PowerShell scripts.
- If the workbook is open in Excel, the step runs but is not recorded.

**Status:** Partly done. A step that stops on an error records nothing, and in `--all` neither do the steps that finished before it (BUG-02).

#### US-26 Slash commands show what they would do, and change files only with `--apply`
As a media owner, I want `/fix-media-dates` and `/flatten-media` to show me what they would change before they change anything, and to make the changes only when I type `--apply`, so that I can check the plan first and nothing changes by accident. (Plex-Filename-Organizer's scripts work the same way.)

- `/fix-media-dates <folder>` and `/flatten-media <folder>` are dry runs. Every step runs as a preview, and nothing is renamed, written, converted, moved or deleted.
- A dry run ends by telling the user what to type to go ahead: `/fix-media-dates <folder> --apply` or `/flatten-media <folder> --apply`.
- `/fix-media-dates <folder> --apply` and `/flatten-media <folder> --apply` make the changes. Optional steps (ads, BMP conversion, PNG conversion, moving to date folders, timestamp sync, flatten, cleaning up converted files) run only when the user asked for them.
- `/fix-media-dates <folder> --all` previews `organize.py --all` (fix extensions, move junk, move incomplete, fill blanks, convert PNG, sync timestamps) in one go, and ends by telling the user to type `/fix-media-dates <folder> --all --apply`, which makes those changes. Ad quarantine, moving to date folders and flatten are left out unless `--quarantine-ads`, `--apply-moves` or `--flatten` is added, and cleanup runs on its own.
- Both commands show `[--apply]` in their argument hint (`/fix-media-dates` also shows `[--all]`), and `/media-help` lists every form.
- `/report-opposite-type` only reports, so it has no `--apply`.
- `tests/test_commands.py` checks each of these, and that no command, skill or guide still says `--dry-run` or `-WhatIf`.

**Status:** Done

#### US-27 Every step that changes files has a dry run, and it is the default
As a media owner, I want every step that changes my photos and videos to preview by default, so that I never have to remember a preview flag to stay safe.

- Every `organize.py` step that writes, converts, moves, renames or deletes files lists what it would do (`WOULD WRITE`, `WOULD CONVERT`, `WOULD MOVE`, `WOULD SYNC`, `WOULD DELETE`, ...) and changes nothing unless `--apply` is given. This covers `--fix-extensions`, `--move-junk`, `--move-incomplete`, `--quarantine-ads`, `--fill-blanks`, `--convert-png`, `--apply-moves`, `--sync-timestamps`, `--flatten`, `--final-check` and `--all`.
- A dry run ends with `DRY RUN: nothing was changed. Run the same command again with --apply to make these changes.`
- `Cleanup-Pictures.ps1` previews unless `-Apply` is given. `-WhatIf` still works.
- Reports (`--audit`, `--compare-collisions`, `--visual-compare`, `--opposite-type`, `--find-plists`, `find_duplicates.py`) change nothing, so they run the same either way. `--visual-compare` no longer needs a flag.
- `--dry-run` is still accepted and means the default. It cannot be combined with `--apply`.
- A dry run is recorded in the audit workbook, marked `yes` in the Dry run column, and never renames the workbook (BUG-05).
- `tests/test_dry_run.py` runs each step without `--apply` and checks that no file's content, name or timestamp changed, then runs it with `--apply` and checks that something did. A new step that changes files fails the test until it is added there.

**Status:** Done

#### US-31 Choose between step by step and all in one go
As a media owner, I want to know how the two ways of running `/fix-media-dates` differ and in what order to run the steps, so that I pick the right one and don't run the steps twice or in the wrong order.

- `/fix-media-dates <folder>` walks through every step and asks which optional steps the user wants: ads, BMP conversion, PNG conversion, moving to date folders, timestamp sync, flatten, and cleaning up converted files. It always asks about cleanup, which sets the converted originals aside (BUG-28).
- `/fix-media-dates <folder> --all` runs the routine steps in one go with no questions, fixing extensions first (BUG-26). It deletes nothing.
- The README has a table showing which steps each way runs, says to choose one of them for a folder, and gives the recommended order of every step, from fixing extensions to the final check.
- The README's **Guardrails** section lists the safety rules that hold for every step.
- In the recommended order, the visual compare comes before cleaning up converted files, because cleanup moves one file of each PNG/JPG pair it would compare into `_converted`.

**Status:** Done

</details>

<details>
<summary><strong>Epic 7 — Maintain the plugin</strong> (US-24 to US-25, US-32, US-48 to US-50)</summary>

Change and test the plugin safely.

#### US-24 Test without real photos or videos
As a maintainer, I want tests that run on generated files, so that I can check a change without risking my own photos and videos.

- `py -m unittest discover tests -v` runs the suite. It currently has 99 tests.
- The tests generate their own photos, and the video tests their own small videos with ffmpeg.
- Video tests are skipped when ffmpeg is missing. The video date-writing test is skipped when ExifTool is missing. The Date Created test runs only on Windows.
- The PowerShell scripts are tested only for their dry run (`-Apply`), and only on Windows.

**Status:** Done

#### US-25 Try a change without installing it
As a maintainer, I want to load my local copy into Claude Code, so that I can try a change before publishing it.

- `claude --plugin-dir .` from the clone loads the plugin for that session.

**Status:** Done

#### US-32 Keep the docs current
As a maintainer, I want the README, cheat sheet, skills and this file updated with each change, so that the docs match the scripts.

- Each feature commit since this file was added (`8c6d76f`) updated the README, cheat sheet, skills and this file wherever the change affected them.

**Status:** Done

#### US-48 See a before and after on sample files
As a maintainer, I want a sample folder that shows each problem the tool fixes, and a copy with the tool run on it, so that I can show what it does and try it without using my own photos.

- `py sample-data/generate.py` writes `sample-data/Sample_Pictures/Before`: year folders (`2023`, `2024`) with day folders inside, holding 19 generated files, each with its problem written on the picture. They cover a date only in the name or the folder's name, a PNG, extensions that lie, photos and a video filed under the wrong date, phone thumbnails, three kinds of app ads, junk sidecars, a copy with no data, and two videos.
- It copies `Before` to `After` and runs `organize.py --all --quarantine-ads --apply-moves --flatten --apply` on each year folder. The good photos and videos end up loose in their year folder, and the rest in that year's `_ads`, `_junk`, `_thumbnails` and `_incomplete`. `After_log.txt` holds what the tool printed.
- `Comparison.md` lists every file in `Before` and `After` with its real format and Date Taken.
- `--before-only` writes only `Before`, and `--out <folder>` writes somewhere else.
- Running it again moves the old `Before` and `After` into `_previous` as `Before_<date>_<time>` and `After_<date>_<time>`; nothing is deleted.
- Without ffmpeg the videos are left out and it says so. The `Sample_Pictures` folder is ignored by git.
- `tests/test_sample_data.py` checks that `Before` starts with each problem, and that in `After` each one is fixed, no day folders are left and the clutter is in each year's holding folders.

**Status:** Done

#### US-49 No spaces in the names the sample generator writes
As a maintainer, I want the files and folders the sample generator writes to use underscores between words instead of spaces, so that their paths can be typed, linked and scripted without quotes.

- The output folder is `sample-data/Sample_Pictures`, not `Sample Pictures`.
- The tool's output is saved as `After_log.txt`, not `After log.txt`.
- An earlier run is moved into `_previous` as `Before_<date>_<time>` and `After_<date>_<time>`, with no spaces.
- `.gitignore`, `sample-data/README.md` and US-48 use the new names, and the test for `_previous` looks for the new form. `.gitignore` still lists `Sample Pictures`, so an older folder not yet moved is never committed.
- Output from an older version is brought up to date by moving, never deleting: a `Sample Pictures` folder is moved to `Sample_Pictures` (or left as it is, with a message, if `Sample_Pictures` already exists), an `After log.txt` goes into `_previous` as `After_log_<date>_<time>.txt`, and spaces in the names in `_previous` become underscores unless the new name is taken.
- Sample content keeps the spaces it needs to show a problem: `Aug 19 2023` is a folder named the way people name them, which the tool reads a date from.
- `tests/test_sample_data.py` checks the default name, the move from `Sample Pictures`, the renames in `_previous`, and that nothing is moved over an existing name.

**Status:** Done

#### US-50 Screenshots a reader can follow
As a media owner reading the README, I want the before and after screenshots laid out the same way and explained where they could puzzle me, so that I can see what the tool changed without guessing.

- Every panel in every screenshot (`docs/screenshots/2024` and `docs/screenshots/All`, combined and separate) shows the same columns in the same order: Name, Date, Type, Size, Tags, Date taken, Media created. Today the After year panels (`2023`, `2024`) have no Date or Tags column.
- The README explains, below the screenshots, what a reader may wonder about:
  - `IMG_0413.HEIC` shows a blank Date taken in Before although the file has one. It is really a JPEG with the wrong extension, so Explorer cannot read its date. After it is renamed `IMG_0413.JPG`, the date shows.
  - `2024-01-01` and `2024-03-10` are in `_empty_folders` in After but not in Before. The tool created them to file the misdated photos and video under their own dates, and they were emptied when it flattened 2024.
  - The `.xlsx` file in each After year folder is the audit workbook, the record of what the run changed.
- The screenshots are retaken from a fresh `py sample-data/generate.py` run, so Before and After come from the same run.

**Status:** Not started

</details>

<details>
<summary><strong>Epic 8 — Desktop app</strong> (US-33 to US-43, US-45, US-51 to US-53, US-56)</summary>

Run every step from a window with buttons, checkboxes and settings instead of typing commands. The app runs the existing scripts on this computer, with the same preview-first rules, so it adds no new way to lose a file. Requested by Michele Kummer on 2026-10-26; nothing is built yet.

**Stack** (chosen by Michele Kummer on 2026-10-27): the interface is written in **Vue 3** with plain CSS and built with **Vite**. It is shown in a window by **pywebview**, which uses the Edge WebView2 already in Windows. A small Python layer builds each step's command line, runs `organize.py` or `Cleanup-Pictures.ps1`, and streams their output back to the window. The app starts with `py app.py` and needs nothing beyond the plugin's own Python packages and pywebview. Chosen because the plugin already needs Python, the author is familiar with Vue and CSS, and no second runtime (Node, Rust or a bundled Chromium) has to ship. Electron would be the alternative if a standalone installer for people without Python is ever needed.

#### US-33 Set the project's parameters once
As a media owner, I want to set the folder and the options that every step uses in one place, so that I don't have to repeat them for each button.

- A **Project** panel at the top holds:
  - **Folder to organize** (required): a text box with a **Browse** button, for example `D:\Pictures\2026`. It is passed to every step as `--root`.
  - **Library folder**: the folder that holds the year folders, for example `D:\Pictures`. It is used by **Final check** and **Find the opposite type**. When the folder to organize is named for a year, it fills in with the folder above it.
  - **Audit workbook name**: blank uses the default name (`<folder>_<photos|videos>_media_audit_<date>.xlsx`). Anything typed is passed as `--xlsx`.
  - **PNG quality** and **BMP quality** (US-38).
  - **Cleanup pixel difference limit**: the most two pictures may differ, from 0.1% to 5%, for **Clean up converted files** to count a PNG, BMP or WebP as converted. Default 1%. Passed as `-MaxPixelDifference`.
- Every step button and both **Run all selected** and **Preview all selected** are unavailable until the folder exists. A folder that does not exist is named in a message next to the box.
- The settings are saved for each folder on this computer (not in the media folder) and come back when that folder is chosen again.
- **Reset to defaults** puts every setting except the folders back to its default.

**Status:** Not started

#### US-34 A button for each step
As a media owner, I want a button for every step the plugin can do, so that I can run any one of them on its own.

- One row per step, in the README's recommended order, grouped under **Fix the dates** and **Check and tidy**. Each row has a checkbox (US-35) and a button named for the step:

| # | Button | Runs | In a full run by default |
|---|---|---|---|
| 1 | Fix extensions | `--fix-extensions` | Yes |
| 2 | Audit dates | `--audit` | No |
| 3 | Set junk aside | `--move-junk` | Yes |
| 4 | Set incomplete files aside | `--move-incomplete` | Yes |
| 5 | Set ads aside | `--quarantine-ads` | No |
| 6 | Find plist and XMP files | `--find-plists` | No |
| 7 | Convert BMP to JPEG | `--convert-bmp` | No |
| 8 | Fill in missing dates | `--fill-blanks` | Yes |
| 9 | Convert PNG to JPEG | `--convert-png` | Yes |
| 10 | Move to date folders | `--apply-moves` | No |
| 11 | Sync timestamps | `--sync-timestamps` | Yes |
| 12 | Flatten | `--flatten` | No |
| 13 | Find duplicates | `find_duplicates.py` | No |
| 14 | Find the opposite type | `--opposite-type` on the library folder | No |
| 15 | Find files from another year | `--other-year` | No |
| 16 | Compare collisions | `--compare-collisions` | No |
| 17 | Visual compare | `--visual-compare` | No |
| 18 | Clean up converted files | `Cleanup-Pictures.ps1` | No |
| 19 | Final check | `--final-check` on the library folder | No |

- A button for a step that changes files runs its preview. When the preview ends, an **Apply** button appears with the results, and runs the same step with `--apply` (`-Apply` for cleanup) after the user confirms.
- A button for a report runs it straight away, since a report changes nothing.
- Steps that only report are marked **Report** next to their name, in text, not by color alone.
- Each row shows when the step last ran on this folder and whether that was a preview.

**Status:** Not started

#### US-35 Choose which steps a full run includes
As a media owner, I want to tick the steps I want in a full run, starting from a sensible default, so that I can run my usual set without ticking it every time.

- Each step's checkbox is labelled "Include <step> in a full run".
- The default is ticked for the six steps `--all` runs (fix extensions, set junk aside, set incomplete files aside, fill in missing dates, convert PNG to JPEG, sync timestamps), and unticked for the rest, so a full run with the defaults does what `--all` does.
- **Reset to default selection** puts the ticks back to the default. **Select all** and **Clear all** do what they say.
- Ticking **Flatten** while **Move to date folders** is ticked (or the other way round) shows a note that they are alternatives, with a button to untick the other one. It does not block the choice.
- Ticking **Clean up converted files** shows a note saying it moves the converted originals into `_converted`.
- The selection is saved with the project's parameters (US-33).

**Status:** Not started

#### US-36 Preview or run every selected step
As a media owner, I want one button that previews every ticked step and one that runs them, so that I can check the whole plan and then carry it out.

- **Preview all selected** runs each ticked step without `--apply`, in the recommended order, and changes nothing. It says, as `--all` does, that a later step may do more once the earlier ones have really run.
- **Run all selected** first asks for confirmation, listing the steps that will change files. When **Clean up converted files** is ticked, the confirmation says it moves the PNGs, BMPs and WebPs it has checked into `_converted`. When no preview has run since the selection or settings changed, it says so and offers **Preview first**.
- **Run all selected** runs each ticked step with `--apply`, in the recommended order, so **Visual compare** always comes before **Clean up converted files**.
- Each step is recorded in the audit workbook as it would be from the command line.
- Both buttons are unavailable while nothing is ticked, and say why.

**Status:** Not started

#### US-37 Follow a run and see what it did
As a media owner, I want to see each step's progress and results in the app, so that I know what happened without reading a terminal.

- A results panel shows which step is running and what it prints, as it prints it.
- When a run ends, it shows one summary: each step's counts and its problems (`COLLISION`, `FAILED`, `NOT MEDIA` and so on), as `--all` does.
- **Stop** stops the run after the current step finishes, so no step is cut off halfway through a file. The steps not run are listed.
- A step that fails stops the run, names the step and shows its error. The steps after it are listed as not run.
- **Open audit workbook** opens the workbook in Excel, and **Open folder** opens the folder in Explorer.
- **Show command** shows the exact command each step ran, so the user can run it again from a terminal.

**Status:** Not started

#### US-38 Set the quality of PNG and BMP conversions
As a photo owner, I want to choose the JPEG quality used when PNGs and BMPs are converted, so that I can trade file size against picture quality.

- **PNG quality** and **BMP quality** each have a slider and a number box from 1 to 100, kept in step. The default for both is 95, as today.
- A note next to each says that JPEG drops some detail at any setting below 100, more as the number goes down, and that 90 to 95 is hard to tell from the original.
- A number outside 1 to 100, or not a number, is named in a message next to the box, and the conversion buttons are unavailable until it is fixed.
- The app passes the values to **Convert PNG to JPEG** and **Convert BMP to JPEG** as `--png-quality` and `--bmp-quality`.
- At a low quality the converted JPEG may differ from the original by more than the cleanup limit, and **Clean up converted files** then keeps the original. The quality note says this, giving the quality US-44 measured.

**Depends on:** US-44, which adds the two options to `organize.py`.

**Status:** Not started

#### US-39 Explain each button with a tooltip
As a media owner, I want every button to explain briefly what it does and what it might cost me, so that I can choose without opening the README.

- Every button, checkbox and setting has a tooltip. It appears on mouse hover and on keyboard focus, stays while the pointer is over it, and closes with **Esc**.
- A button that is unavailable still shows its tooltip, ending with why it is unavailable.
- Each step's tooltip says what it does, and leads with any side effect. These are the main ones:

| Button | Side effect named in the tooltip |
|---|---|
| Fix extensions | Renames files whose extension is wrong. |
| Set junk aside, Set incomplete files aside, Set ads aside | Moves files into `_junk`, `_incomplete` or `_ads`. Nothing is deleted. |
| Convert BMP to JPEG, Convert PNG to JPEG | Re-encodes the picture as JPEG, which loses some quality (US-38). Pictures with transparency are left as they are. The original is kept until cleanup. |
| Fill in missing dates | Writes a Date Taken or Media Created into files that have none. Videos and HEIC need ExifTool. |
| Move to date folders, Flatten | Moves files between folders. Use one or the other. |
| Sync timestamps | Changes Date Created, and Date Modified on files that look unedited. The old times are not kept. |
| Clean up converted files | Moves each PNG, BMP and WebP already converted into `_converted`, after checking they are the same picture. Nothing is deleted. |
| Any report | Changes nothing. |

- **Run all selected**, **Preview all selected**, **Apply** and **Stop** have tooltips too.
- The tooltip text is written once and used for the tooltip and the button's accessible description (US-42).

**Status:** Not started

#### US-40 A modern look in Montserrat
As a media owner, I want the app to look clean and modern, so that it is pleasant and easy to read.

- All text is in Montserrat: regular (400) for body text, semibold (600) for buttons and labels, bold (700) for headings. Body text is at least 14 px.
- The font files ship with the app, under the SIL Open Font License, so it works offline and looks the same on every computer. If they cannot be loaded, it falls back to Segoe UI, then any sans serif.
- Rounded corners, consistent spacing and clear grouping of the Project, Steps and Results panels.
- The window works from 1024 x 700 upwards, and at 200% text zoom without text being cut off.

**Status:** Not started

#### US-41 Light and dark themes in the logo's colors
As a media owner, I want to choose a light or a dark theme, in colors taken from the SK SkyOrbit logo, so that the app is comfortable to use and matches the brand.

- A **Theme** dropdown offers **Light** and **Dark**. The choice is remembered. The first time, it follows the Windows setting.
- The colors come from `SK SkyOrbit Color SVG 3.svg`: navy `#18415E`, mid blue `#66A1C8`, light blue `#9CC4E2` and gold `#F8D274`. White `#FFFFFF`, a pale tint `#F4F8FB` and a deep navy `#0F2A3D`, made by darkening the logo's navy, are added for backgrounds.
- Every pair of text and background colors below has been measured, and each reaches 4.5:1, the AA contrast level:

| Use | Light theme | Dark theme |
|---|---|---|
| Page background | `#FFFFFF` | `#0F2A3D` |
| Panel background | `#F4F8FB` | `#18415E` |
| Text | `#18415E` (10.7:1 on white) | `#FFFFFF` (14.8:1 on deep navy, 10.7:1 on navy) |
| Secondary text | `#18415E` | `#9CC4E2` (8.0:1 on deep navy, 5.8:1 on navy) |
| Step buttons | `#FFFFFF` on `#18415E` (10.7:1) | `#0F2A3D` on `#9CC4E2` (8.0:1) |
| Run all selected | `#18415E` on `#F8D274` (7.4:1) | `#0F2A3D` on `#F8D274` (10.2:1) |
| Selected row | `#18415E` on `#9CC4E2` (5.8:1) | `#FFFFFF` on `#18415E` (10.7:1) |
| Borders and checkboxes | `#18415E` | `#66A1C8` (5.3:1 on deep navy) |
| Keyboard focus outline | `#18415E`, 2 px | `#F8D274`, 2 px (10.2:1 on deep navy) |

- Mid blue on white (2.8:1) and gold on white (1.5:1) are too faint for text, so in the light theme they are only used for decoration, never for text, borders or focus.

**Status:** Not started

#### US-42 Usable with a keyboard and a screen reader (WCAG 2.2 Level A)
As a media owner who uses the keyboard or a screen reader, I want the app to meet the basic accessibility rules, so that I can use every part of it.

The app meets every WCAG 2.2 Level A success criterion. The ones that matter most here:

- **1.1.1 Non-text content:** every icon has a text name; decorative images are hidden from screen readers.
- **1.3.1 Info and relationships:** each setting has a visible label tied to it; the step checkboxes are a named group (**Steps for a full run**); panels have headings.
- **1.3.2 Meaningful sequence** and **2.4.3 Focus order:** **Tab** moves through Project, Steps (in step order) and Results, in reading order.
- **1.4.1 Use of color:** reports, deleting steps, errors and unavailable buttons are marked with text or an icon as well as color.
- **2.1.1 Keyboard** and **2.1.2 No keyboard trap:** every button, checkbox, slider, dropdown and tooltip works from the keyboard, and focus never gets stuck, including in the confirmation dialogs.
- **2.2.2 Pause, stop, hide:** the live run output can be paused.
- **2.4.2 Page titled:** the window title names the app and the folder.
- **2.5.3 Label in name:** each control's accessible name starts with its visible label.
- **3.3.1 Error identification** and **3.3.2 Labels or instructions:** an invalid folder or quality is named in text next to its box, with what is allowed.
- **4.1.2 Name, role, value:** every control reports its name, role and state (ticked, unavailable, running) to screen readers.

Beyond Level A, the app also aims for these AA criteria, which the palette already allows: **1.4.3** text contrast 4.5:1, **1.4.11** control and focus contrast 3:1, **1.4.13** tooltips that can be dismissed and hovered, and **2.4.7** a visible focus outline.

**Status:** Not started

#### US-43 Test the app
As a maintainer, I want tests for the app, so that a change cannot quietly break a button, a default or the accessibility.

- The Python layer's tests run in the existing `unittest` suite. Each button is checked to build the same command line the README gives for its step, with the project's parameters and quality settings.
- The default selection is checked to equal the steps `--all` runs.
- **Run all selected** is checked to run the ticked steps in the recommended order, and to run nothing with `--apply` until the user confirms.
- Each theme's colors are checked to reach the contrast ratios in US-41.
- An automated accessibility check (axe-core) reports no Level A failures in either theme.
- `docs/` has a keyboard and screen reader checklist, run by hand before each release.

**Status:** Not started

#### US-45 Choose whether set-aside files are flattened
As a media owner, I want a setting that chooses whether ads, incomplete files and junk are flattened once they are set aside, so that I can keep their subfolders when I want to see where each one came from.

- The **Project** panel (US-33) has a **Flatten set-aside files** checkbox, ticked by default. It applies to **Set ads aside**, **Set incomplete files aside** and **Set junk aside**, alone or in a full run, and to the sidecars **Flatten** moves into `_junk`.
- Ticked: each file goes straight into `_ads`, `_incomplete` or `_junk`, with no subfolders, as the script does today (US-12 to US-14), with the folder's date added to undated names (US-46).
- Unticked: each file keeps its subfolder path inside the holding folder (`_incomplete\2018-08-19\clip.mp4`), and no name is changed.
- `organize.py` gets a flag that keeps subfolder paths, added when the app is built. The **Command** line under each button (US-37) shows it.
- The tooltip (US-39) explains both choices with an example.
- The setting is saved with the project's other settings, and **Reset to defaults** ticks it again.
- Tests cover a ticked and an unticked run of each of the three steps.

**Status:** Not started

#### US-51 Choose which kinds of junk are set aside
As a media owner, I want to choose which kinds of junk are moved aside, so that I can keep a kind I still use, such as `.AAE` files that hold my iPhone edits, in place beside its photos.

- The **Project** panel (US-33) has a **Junk to move** group with one checkbox for each kind. All are ticked by default:

| Checkbox | What it moves | Into | Moved by |
|---|---|---|---|
| macOS "._" files | Sidecars a Mac writes beside each file it copies to a non-Mac drive (`._IMG_0001.JPG`) | `_junk` | Set junk aside |
| AAE files | iPhone photo-edit files (`IMG_0001.AAE`) | `_junk` | Set junk aside |
| Windows thumbnail caches | `Thumbs.db`, `ehthumbs.db` and `ehthumbs_vista.db` | `_junk` | Set junk aside |
| Plist and XMP files | `.plist` and `.xmp` files, and plist or XMP text saved under a photo name (`IMG_E5239.JPG`) | `_junk` | Set junk aside |
| Leftover camcorder files | Sony `.modd` and `.moff` sidecars whose video is gone | `_junk` | Flatten |
| Photo thumbnails | Phone gallery thumbnails (`1234.jpg`, small, no camera make or model) | `_thumbnails` | Set thumbnails aside (US-54) |

- An unticked kind stays where it is, and the step's output says how many were left in place by this setting, so a reader can tell them apart from files that were never found.
- The settings apply to the step's button, its preview and a full run (US-35, US-36).
- `organize.py` gets an option naming the kinds to move, added when the app is built. Given no option, `--move-junk` and `--flatten` move every kind, as they do today (US-14). The **Command** line under each button (US-37) shows the option.
- When every box is unticked, **Set junk aside** says that there is nothing to move and does not run.
- The tooltip (US-39) names each kind with an example file name, and says that a phone thumbnail can be the only copy left of a photo.
- The settings are saved with the project's other settings, and **Reset to defaults** ticks every box again.
- Tests cover each kind ticked and unticked, the default with no option, and every box unticked.

**Status:** Not started

#### US-52 Choose which kinds of incomplete files are set aside
As a media owner, I want to choose which kinds of incomplete files are moved aside, so that I can leave a kind in place while I try to recover it, such as a video copy that stopped partway.

- The **Project** panel (US-33) has an **Incomplete files to move** group with one checkbox for each kind. All are ticked by default:

| Checkbox | What it moves | Example |
|---|---|---|
| Empty files | Photos and videos that are 0 bytes | `IMG_0412.JPG`, 0 bytes |
| Files with only zeros | Photos and videos that hold nothing but null bytes, so there is no picture or recording in them | A 3 MB `clip.mp4` that is all zeros |
| Videos with no header | Videos with no `moov` header, a stub or a copy that stopped partway, which no player can open | A truncated `VID_0001.MOV` |

- Every kind goes into `_incomplete`, as **Set incomplete files aside** does today (US-13).
- An unticked kind stays where it is, and the step's output says how many were left in place by this setting.
- The settings apply to the step's button, its preview and a full run (US-35, US-36).
- `organize.py` gets an option naming the kinds to move, added when the app is built. Given no option, `--move-incomplete` moves every kind, as it does today. The **Command** line under the button (US-37) shows the option.
- When every box is unticked, **Set incomplete files aside** says that there is nothing to move and does not run.
- The tooltip (US-39) explains each kind with an example.
- The settings are saved with the project's other settings, and **Reset to defaults** ticks every box again.
- Tests cover each kind ticked and unticked, the default with no option, and every box unticked.

**Status:** Not started

#### US-53 Choose which kinds of ads are set aside
As a media owner, I want to choose which kinds of ad names are moved aside, so that I can keep a kind that, in my folders, turns out to be my own pictures.

- The **Project** panel (US-33) has an **Ads to move** group with one checkbox for each kind of name **Set ads aside** looks for (US-12, US-30, US-47). All are ticked by default:

| Checkbox | Names it matches | Example |
|---|---|---|
| Long random IDs | A random ID used as the whole name: a UUID, a 9-character hex ID and a number, a 24-character hex ID with more parts, or three random parts joined by `_` | `0c4cda27-b4cc-4e92-a446-d6b780f24a64.jpg`, `bed51b94a_1595.png` |
| Ad network names | Names from ad networks and the web addresses they save from | `gmsnet2.png`, `UnityAdsCache-<hash>.jpg`, `news_images%2F1714658759372.jpg`, `__d2duuy9yo5pldo.cloudfront.net_codigames_<id>.png` |
| Game ads | Game ad creatives and the raw pixel data games save | `Update_Now_Video_V2_720x1280_15s___fudxlv.mp4`, `492887-1648448524975-3d62u.png`, `draw_title.raw` |
| App files | App icons, button images, cache files and colour swatches | `icon.png`, `scribble2mammoth_over@2x.png`, `glority_cache_1656951098314.jpg`, `2#xff0000ff#0#1.png` |
| Ad videos | Video names only: 20 random lowercase letters and digits, a 32-character hash, or a transcode tag at the end | `vuyyzy0brvod5gcaocnv.mp4`, `d5a210d011c47b8300bb8034048719a9.mp4`, `<id>-720x1280-h264-Q2.mp4` |

- A file is still moved only when its name matches a ticked kind **and** it has no camera make or model, as today. Every kind goes into `_ads`, or the year's own `_ads` (US-12).
- A file whose name matches only unticked kinds stays where it is, and the step's output says how many were left in place by this setting.
- The settings apply to the step's button, its preview and a full run that includes it (US-35, US-36).
- `organize.py` gets an option naming the kinds to move, added when the app is built. Given no option, `--quarantine-ads` moves every kind, as it does today. The **Command** line under the button (US-37) shows the option.
- When every box is unticked, **Set ads aside** says that there is nothing to move and does not run.
- The tooltip (US-39) shows an example name for each kind.
- The settings are saved with the project's other settings, and **Reset to defaults** ticks every box again.
- Tests cover each kind ticked and unticked, a name with camera information under a ticked kind, the default with no option, and every box unticked.

**Status:** Not started

#### US-56 Choose which folders are flattened
As a media owner, I want to type the folder names that **Flatten** should empty, besides dated folders, or tell it to flatten every folder, so that I can flatten my own scratch folders (such as `Unsorted` or `From Phone`) without editing the script, and still keep the folders I named for a child, a trip or a wedding.

- The **Project** panel (US-33) has a **Folders to flatten** setting with two choices:
  - **Dated folders and these names** (the default), with a list the user can add names to and remove names from. It starts with the words and phrases `--flatten` uses today (US-55): `Temp`, `Junk`, `Delete`, `Weird`, `Review`, `New folder`, `DCIM`, `Camera`, `Unsorted`, `To Sort`, `Misc`, `Download`, `Downloads`, `Import`, `Imports` and `Imported`. Camera folders such as `100APPLE` are always flattened, like dated folders.
  - **All folders**: every subfolder at any depth is flattened, named ones included. Choosing it shows a note that folders named for a child, a trip or a wedding will be emptied too.
- Dated folders are always flattened, whichever choice is made.
- Each name is matched as `--flatten` matches the built-in words: as a whole word, in any case, anywhere in the folder's name (`Unsorted` matches `Unsorted 2022`), and never in a name starting with an underscore. Every folder below a matching folder is flattened too.
- An empty name, or one already in the list, is not added, and the list says why.
- `organize.py` gets the back end, added when the app is built: an option giving the words to flatten (replacing the built-in list), and an option to flatten all folders. Given neither, `--flatten` works as it does today. The **Command** line under the button (US-37) shows the options.
- The preview of **Flatten** (US-35) lists which folders would be emptied and which named folders would be kept (`KEPT (named folder)`), so the user can check the list before running it.
- The final check uses the same setting, so a folder the user chose to flatten is reported as `NOT FLATTENED` when it still holds files, and is not listed as a named folder.
- The tooltip (US-39) gives an example of each choice.
- The setting is saved with the project's other settings, and **Reset to defaults** puts back the built-in words.
- Tests cover a name the user added, a name removed from the list, **All folders**, a name starting with an underscore, and a run with neither option.

**Status:** Not started

</details>

---

## Part 2 — Bugs

Severity: **High** means files are lost or the plugin can't be used. **Medium** means a wrong result, or a step that fails or stops. **Low** means a cosmetic problem, or one with a workaround.

<details>
<summary><strong>Open bugs</strong> (3: 2 found by Claude on 2026-10-21, 1 by Michele Kummer on 2026-11-15)</summary>

Each was reproduced on synthetic files, except where noted.

#### BUG-02 One unreadable photo or video stops a step, and nothing is recorded
**Severity:** Medium · **Found by:** Claude · **Affects:** photos and videos · **Where:** [organize.py](../skills/media-date-organizer/scripts/organize.py) `sync_timestamps`, `scan`

`fill_blanks` catches read errors per file, but `sync_timestamps` and `scan` do not. `scan` is used by `--audit`, `--apply-moves`, `--compare-collisions` and `--visual-compare`.

**Steps to reproduce**
1. Make a photo or video that cannot be read during the step. The repro simulated this with a `PermissionError`; in real use it could be a file locked by another program, or a HEIC photo or a video large enough to cause a `MemoryError`, since both are read whole when no header is found.
2. Run `--sync-timestamps`.

**Expected:** That file is reported as failed and the rest are synced.
**Actual:** The step stops with a traceback, and no audit workbook is written. Under `--all`, the record of the steps that had already finished is lost too, because the workbook is written once at the end.

#### BUG-04 HEIF and AVIF photos are read as MP4 video
**Severity:** Low · **Found by:** Claude · **Affects:** photos (HEIF image sequences and AVIF) · **Where:** `detect_type` in [organize.py](../skills/media-date-organizer/scripts/organize.py)

Any file with an `ftyp` header whose brand is not in the known list is reported as `.mp4`. Two examples:
- a `.heic` with the `hevc` brand (a HEIF image sequence, such as an iPhone burst);
- an AVIF photo.

A HEIF photo read as video has no video date. `--fill-blanks` would then try to write video date tags into it with ExifTool.

**Steps to reproduce:** `detect_type` on a file starting `....ftyphevc` or `....ftypavif` returns `.mp4`.
**Expected:** HEIF brands (`hevc`, `heim`, `heis`, `hevx`) return `.heic`. Unknown brands return `None`.

#### BUG-36 `--move-incomplete` reads 1 MB of every photo, so it runs slowly
**Severity:** Low · **Found by:** Michele Kummer · **Affects:** photos and videos · **Where:** [organize.py](../skills/media-date-organizer/scripts/organize.py) `_has_no_data`, called by `_incomplete_kind`

To find files that hold nothing but null bytes, `_has_no_data` reads in 1 MB chunks and checks each chunk only after reading it. A normal photo has non-null header bytes in its first few bytes, but the whole first 1 MB is still read before the check. `_incomplete_kind` runs this on every photo, and on every video without an MP4 or MOV header (AVI, MPG, WMV). On 10,000 photos that is about 10 GB read, where the other steps read a few hundred bytes to a few KB of each file. The step is slowest on a hard drive or network share, or when another program is using the disk. Michele Kummer noticed the slowdown and Claude found the cause by reading the code; it was not timed on synthetic files.

**Steps to reproduce**
1. Point `--root` at a folder of several thousand photos on a hard drive.
2. Run `--move-incomplete`, then `--fix-extensions`, and compare how long each takes.

**Expected:** `--move-incomplete` takes about as long as `--fix-extensions`. It reads a small first piece of each file (4 KB, say) and only reads further, in 1 MB chunks, when that piece is all null bytes. The result is the same.
**Actual:** `--move-incomplete` takes far longer, because it reads 1 MB of every file.

</details>

<details>
<summary><strong>Resolved bugs</strong> (38: 20 found by Michele Kummer, 18 by Claude)</summary>

The list is oldest first. **Fixed in** gives the commit. Bugs fixed before the history begins point to [case-study.md](case-study.md) instead.

| ID | Bug | Affects | Severity | Found by | Fixed in |
|---|---|---|---|---|---|
| BUG-06 | Wrong extensions hid real dates | Photos and videos | High | Claude | case study |
| BUG-07 | PNG Date Taken hidden in Explorer | Photos (PNG) | Medium | Claude | case study |
| BUG-08 | Command line and docs disagreed | Setup and docs | Medium | Michele Kummer | `c742389`, `3b99ebb`, `89f2044` |
| BUG-09 | Filling a date re-encoded JPEGs | Photos (JPEG) | Medium | Claude | `b58aef6` |
| BUG-10 | Filename dates ignored | Photos | Medium | Michele Kummer | `b58aef6` |
| BUG-11 | Case-only renames reported as collisions | Photos and videos | Low | Claude | `48dde7a` |
| BUG-12 | Video dates in the wrong time zone, whole video read | Videos | Medium | Claude | `0c3f7e3` |
| BUG-13 | One unreadable file stopped fill and convert | Photos and videos | Medium | Claude | `0c3f7e3`, `8d47bde` |
| BUG-14 | Cleanup `-WhatIf` looped forever | Folders | Medium | Claude | `df37cf1` |
| BUG-15 | Older video formats reported as UNKNOWN | Videos | Low | Michele Kummer | `df37cf1`, `8d47bde` |
| BUG-16 | Photo files left open | Photos | Low | Claude | `e82fc06` |
| BUG-17 | `--apply-moves` renamed files | Photos and videos | Medium | Claude | `8d47bde` |
| BUG-18 | Edited photos skipped by timestamp sync | Photos | Low | Claude | `8d47bde` |
| BUG-19 | Fill and sync only looked one level deep | Photos and videos | Medium | Michele Kummer | `9f23c22` |
| BUG-20 | Plugin could not be installed | Setup | High | Michele Kummer | `9f23c22` |
| BUG-21 | Folder dates read only from exact `YYYY-MM-DD` names | Photos and videos | Medium | Michele Kummer | `89f2044` |
| BUG-22 | Install commands disagreed about package versions | Setup | Low | Claude | `8c6d76f`, `1111480` |
| BUG-23 | Minimum Python version stated but never checked | Setup | Low | Claude | `8c6d76f` |
| BUG-24 | PowerShell scripts skipped the audit log without `python` on PATH | Audit workbook | Low | Claude | `8c6d76f` |
| BUG-01 | Cleanup deleted Live Photo videos and sidecar files | Photos and videos | High | Claude | `1111480` |
| BUG-03 | Report and `--apply-moves` only looked one folder deep | Photos and videos | Medium | Claude | `2b6ea1d` |
| BUG-05 | A dry run renamed an audit workbook | Audit workbook | Low | Claude | `15b699c` |
| BUG-25 | Plist files named as photos failed to get a date and were renamed | Photos (non-media files with a photo name) | Low | Michele Kummer | `a8631ce` |
| BUG-26 | `--all` did not fix extensions | Photos and videos | Medium | Michele Kummer | `b6166b8` |
| BUG-27 | Junk and orphan sidecar files were permanently deleted | Non-media files (sidecars and thumbnail caches) | Medium | Michele Kummer | `b6166b8` |
| BUG-28 | The step-by-step run never asked about cleanup | Workflow | Low | Michele Kummer | `b6166b8` |
| BUG-29 | `--flatten` left ads in their subfolders | Photos and videos (ads) | Medium | Michele Kummer | `98dfd1f` |
| BUG-30 | `--flatten` left ads in a year folder inside `_ads` | Photos and videos (ads) | Medium | Michele Kummer | `8b96016` |
| BUG-31 | `--quarantine-ads` put every year's ads in one `_ads` | Photos and videos (ads) | Medium | Michele Kummer | `8b96016` |
| BUG-32 | Other steps went into a year's own `_ads` | Photos and videos (ads) | Medium | Claude | `8b96016` |
| BUG-33 | Phone thumbnails were dated and flattened in among the photos | Photos (phone thumbnails) | Medium | Michele Kummer | `a8db9d2` |
| BUG-34 | Phone thumbnails were set aside before they got a date, with no way to opt out | Photos (phone thumbnails) | Medium | Michele Kummer | `4b5f2ed` |
| BUG-35 | `--flatten` only looked one subfolder deep | Photos and videos | Medium | Michele Kummer | `a155436` |
| BUG-37 | A 1904 placeholder date was kept, and dates before 1970 stopped timestamp sync | Photos | Medium | Michele Kummer | `575d9bb` |
| BUG-38 | Timestamp sync rewrote and listed files that were already synced | Photos and videos | Low | Michele Kummer | `407497b` |
| BUG-39 | Phone transfer stubs were not set aside as incomplete | Photos | Medium | Michele Kummer | `5be9fb5` |
| BUG-40 | Writing a date into a PNG, or converting it to JPEG, dropped its XMP | Photos (PNG) | Medium | Claude | `76022e8` |
| BUG-41 | Thumbnails from newer Android phones were not set aside | Photos | Medium | Michele Kummer | `78fb788` |

#### BUG-06 Wrong extensions hid real dates
**Found by:** Claude · **Affects:** photos and videos · **Fixed:** before the first commit ([case-study.md](case-study.md))

On the first real run, 14 of 35 files seemed to have no Date Taken. Writing EXIF to the first one failed, which showed the file was not what its extension said. Of 13 `.PNG` files, 8 were HEIC photos and 3 were QuickTime videos, and 2 `.HEIC` files were PNG photos.
**Fix:** Correcting extensions from the file's first bytes became the first phase (`Fix-Extensions.ps1`). With each file read by the right reader, all 35 had a date.

#### BUG-07 PNG Date Taken hidden in Explorer
**Found by:** Claude · **Affects:** photos (PNG) · **Fixed:** before the first commit ([case-study.md](case-study.md))

Four PNG photos showed a blank Date Taken in Windows Explorer although the EXIF date was in the file. Explorer never shows Date Taken for PNG.
**Fix:** `--convert-png` converts PNG to JPEG at quality 95, keeping the EXIF.

#### BUG-08 Command line and docs disagreed
**Found by:** Michele Kummer · **Affects:** setup and docs · **Fixed in:** `c742389`, `3b99ebb`, `89f2044`

The docs described `--apply-moves`, `--fill-blanks` and `--sync-timestamps`, but the script had `--apply` and neither of the other two. Later, help text still said "ad images" for a step that also moves videos, and the `--sync-timestamps` help contained a stray `$root`.
**Fix:** The script was rewritten to match the docs, and the help text was corrected.

#### BUG-09 Filling a date re-encoded JPEGs
**Found by:** Claude · **Affects:** photos (JPEG) · **Fixed in:** `b58aef6`

Every JPEG photo given a date was re-saved at Pillow's default quality, losing picture quality.
**Fix:** The EXIF block is now swapped in place, and the image data is left untouched.

#### BUG-10 Filename dates ignored
**Found by:** Michele Kummer · **Affects:** photos · **Fixed in:** `b58aef6`

Photos without an EXIF date, such as Snapchat exports, were given their folder's date even when the filename held the real one (`IMG_20231220_142355.jpg`). Photos in folders without a date in their name got no date at all.
**Fix:** The filename date is used first, then the folder date. The file's modified time is never used.

#### BUG-11 Case-only renames reported as collisions
**Found by:** Claude · **Affects:** photos and videos · **Fixed in:** `48dde7a`

A move that only changed letter case (`img.JPG` → `img.jpg`) was reported as a collision on Windows, where names are not case-sensitive.
**Fix:** Case-only renames are no longer treated as collisions.

#### BUG-12 Video dates in the wrong time zone, whole video read
**Found by:** Claude · **Affects:** videos · **Fixed in:** `0c3f7e3`

Video dates are stored in UTC but were treated as local time, so they were off by the time-zone difference. Finding the date also read the whole video into memory.
**Fix:** Dates are converted between UTC and local time when read and written. Only the header atoms are read.

#### BUG-13 One unreadable file stopped fill and convert
**Found by:** Claude · **Affects:** photos and videos (`--fill-blanks`), PNG photos (`--convert-png`) · **Fixed in:** `0c3f7e3`, `8d47bde`

A single unreadable photo or video stopped `--fill-blanks`. A `.png` that wasn't a picture stopped `--convert-png` and could leave a half-written JPEG behind.
**Fix:** The file is reported and counted as `read-failed`, the rest are processed, and a half-written JPEG is removed. (BUG-02 is the same problem in other steps.)

#### BUG-14 Cleanup `-WhatIf` looped forever
**Found by:** Claude · **Affects:** folders (no photo or video is touched) · **Fixed in:** `df37cf1`

`Cleanup-Pictures.ps1 -WhatIf` never finished on a folder with an empty subfolder, because the preview never removed the folder it kept finding.
**Fix:** The empty-folder pass was rewritten. Since `89f2044` it moves empty folders into `_empty_folders` instead of removing them.

#### BUG-15 Older video formats reported as UNKNOWN
**Found by:** Michele Kummer · **Affects:** videos · **Fixed in:** `df37cf1`, `8d47bde`

`Fix-Extensions.ps1` reported camcorder (`.m2ts`, `.mts`), MPEG, Windows Media and AVI videos as `UNKNOWN`, and Sony `.modd`/`.moff` sidecars as unknown files.
**Fix:** All are recognised and left with their own extension. `--flatten` moves them by the date in the filename.

#### BUG-16 Photo files left open
**Found by:** Claude · **Affects:** photos · **Fixed in:** `e82fc06`

Photos stayed open after reading their metadata, converting PNGs and comparing pictures, which can stop Windows from moving or deleting them.
**Fix:** Every photo is closed after use.

#### BUG-17 `--apply-moves` renamed files
**Found by:** Claude · **Affects:** photos and videos · **Fixed in:** `8d47bde`

Besides moving photos and videos, `--apply-moves` changed their extension to the detected type in capitals and stripped `_YYYY-MM-DD` endings that carried a file's only date. `--convert-png` also named the JPEGs it made `.JPG` instead of `.jpg`.
**Fix:** `--apply-moves` no longer changes extensions or strips date endings. Only `Fix-Extensions.ps1` changes extensions.

#### BUG-18 Edited photos skipped by timestamp sync
**Found by:** Claude · **Affects:** photos · **Fixed in:** `8d47bde`

`--sync-timestamps` skipped edited photos entirely, so their Date Created still showed the import date.
**Fix:** Edited photos get Date Created set, and keep their Date Modified.

#### BUG-19 Fill and sync only looked one level deep
**Found by:** Michele Kummer · **Affects:** photos and videos · **Fixed in:** `9f23c22`

`--fill-blanks` and `--sync-timestamps` only checked files exactly one folder below the root, so photos and videos in nested folders were missed. (BUG-03 was the same limit in `--report-only` and `--apply-moves`, fixed later.)
**Fix:** Both now look at every depth.

#### BUG-20 Plugin could not be installed
**Found by:** Michele Kummer · **Affects:** setup · **Fixed in:** `9f23c22`

The plugin manifest failed validation because its skill and command paths lacked a leading `./`, and the README's `/plugin install .` instructions did not work.
**Fix:** The paths were corrected, a marketplace file was added, and the README gives the marketplace install command.

#### BUG-21 Folder dates read only from exact `YYYY-MM-DD` names
**Found by:** Michele Kummer · **Affects:** photos and videos · **Fixed in:** `89f2044`

Folders named `2026-08-19 11-44-31`, `2019_08_30`, `30-08-2019` or `Aug 19 2026` were not recognised as dated, so photos and videos in them got no fallback date and were not moved.
**Fix:** All of these forms are read. A year-only name is still not a date.

#### BUG-22 Install commands disagreed about package versions
**Found by:** Claude · **Affects:** setup · **Fixed in:** `8c6d76f`, `1111480` (two missed hints)

The two `SKILL.md` files, `commands/fix-media-dates.md` and the scripts' error messages said `pip install pillow openpyxl` with no versions. The README and `requirements.txt` require `pillow>=10.0` and `openpyxl>=3.1`.
**Fix:** Every install hint now gives the minimum version, including `imageio-ffmpeg>=0.5`. The `--convert-png` and `--quarantine-ads` hints were missed at first and fixed later.

#### BUG-23 Minimum Python version stated but never checked
**Found by:** Claude · **Affects:** setup · **Fixed in:** `8c6d76f`

The README said Python 3.9+, but nothing enforced it, and the skill docs did not mention it.
**Fix:** `organize.py` (and through it `find_duplicates.py`) stops with a clear message on Python older than 3.9. The skill docs and `/fix-media-dates` state the requirement.

#### BUG-24 PowerShell scripts skipped the audit log without `python` on PATH
**Found by:** Claude · **Affects:** the audit workbook (no photo or video is touched) · **Fixed in:** `8c6d76f`

`Write-AuditLog.ps1` looked only for `python`. A python.org install often provides only the `py` launcher, which is also what the cheatsheet uses. Where Python was missing, the Microsoft Store `python` stub could be picked instead.
**Fix:** It tries a real `python` first, then `py -3`, and ignores the WindowsApps stub.

#### BUG-01 Cleanup deleted Live Photo videos and sidecar files
**Severity:** High (permanent data loss) · **Found by:** Claude · **Affects:** photos and videos · **Fixed in:** `1111480`

`Cleanup-Pictures.ps1` treated any two files with the same base name in a folder as duplicates, whatever their type and content, and deleted all but one. `IMG_1234.HEIC` and `IMG_1234.MOV` (a Live Photo) lost the video, and `IMG_5555.JPG` and `IMG_5555.xmp` lost the edits. A file with an extension not on the preference list always lost, and the pass also ran inside `_ads`, `_incomplete` and `_empty_folders`.
**Fix:** The only file it deletes now is a PNG photo with a JPG or JPEG of the same name beside it, and only when both are the same size and differ by no more than 1% in their pixels, as a `--convert-png` conversion does. Videos and sidecars are never deleted. Any other pair is kept, and a PNG whose JPG differs is listed as `KEPT (not the same picture)` with the reason. The holding folders are skipped. The `-PreferredExtOrder` parameter is gone, and `-MaxPixelDifference` is new. US-11 describes how the pictures are compared.

#### BUG-03 Report and `--apply-moves` only looked one folder deep
**Severity:** Medium · **Found by:** Claude · **Affects:** photos and videos · **Fixed in:** `2b6ea1d`

`scan` looked only at photos and videos exactly one folder below the root, while `--fill-blanks`, `--sync-timestamps`, `--flatten` and `--convert-png` work at any depth. With `root\loose.jpg`, `root\2019-08-30\wrong.jpg` and `root\Trip\2019-08-30\deep.jpg`, `--report-only` reported only `wrong.jpg`. After `--flatten`, every file is loose in the root, so a later report listed none of them. `--apply-moves`, `--compare-collisions` and `--visual-compare` use the same scan, so they missed the same files.
**Fix:** `scan` walks the root and every subfolder at any depth, skipping the holding folders, like `--fill-blanks`. Each file is checked against the folder it sits in and moves to a sibling of that folder (`Trip\2019-08-31`). A file loose in the root is never moved out of it; one whose date differs from a dated root is listed as `in-root-date-differs`. The fill-blank date now comes from the same source `--fill-blanks` uses, so a video gets the nearest dated folder. Two tests cover it, and both fail on the old code.

#### BUG-05 A dry run renamed an audit workbook
**Severity:** Low · **Found by:** Claude · **Affects:** the audit workbook (no photo or video is touched) · **Fixed in:** `15b699c`

Working out today's workbook name renamed an old-style `media_audit_<date>.xlsx` to `<folder>_<type>_media_audit_<date>.xlsx` on every run, previews included. With `media_audit_<date>.xlsx` in a folder named `2014`, `--flatten --dry-run` renamed it to `2014_photos_media_audit_<date>.xlsx`.
**Fix:** A dry run leaves the workbook's name alone and records itself in the old-style workbook. The next run with `--apply` renames it. Fixed with US-27, which made every step a dry run unless `--apply` is given. `tests/test_dry_run.py` covers it.

#### BUG-25 Plist files named as photos failed to get a date and were renamed
**Severity:** Low · **Found by:** Michele Kummer · **Affects:** files with a photo name that are really plist or XMP text · **Fixed in:** `a8631ce`

On `E:\Pictures\2023`, `--fill-blanks` reported `FAILED to write 2023-08-07/IMG_E5239_2023-08-07.JPG: Error: Not a valid JPG (looks more like a XMP)`, and the same for `IMG_E6230_2023-12-10.JPG`. The files are plist text (iPhone `.AAE` edit data) saved under a `.JPG` name. Every step treated them as undated photos: `--fill-blanks` handed them to ExifTool, which refused them; `--convert-png` failed on a `.png` one; and `--apply-moves` gave them a `_<folder-date>` suffix, which is how they got `_2023-08-07` in their names.
**Fix:** Files whose content is plist, XMP or other XML text are recognised by their first bytes. Every step reports them as `NOT MEDIA` and leaves them alone, and the new `--find-plists` lists them all (US-28). They are never deleted, so the user decides. The `_2023-08-07` suffixes already added are not removed.

#### BUG-26 `--all` did not fix extensions
**Found by:** Michele Kummer · **Affects:** photos and videos · **Fixed in:** `b6166b8`

Fixing extensions was only in `Fix-Extensions.ps1`, which `--all` does not run. A JPEG saved as `.PNG` or a HEIC saved as `.JPG` went through `--all` under its wrong name, so the date steps read it as the wrong format, even though the README listed fixing extensions as step 1 of `/fix-media-dates`.
**Fix:** New `organize.py --fix-extensions`, with the same rules as the PowerShell script, runs first in `--all`. `tests/test_fix_extensions_and_junk.py` covers it.

#### BUG-27 Junk and orphan sidecar files were permanently deleted
**Found by:** Michele Kummer · **Affects:** non-media files (`.AAE`, `Thumbs.db`, macOS `._` and Sony `.modd`/`.moff` sidecars) · **Fixed in:** `b6166b8`

`--delete-junk`, and so `--all`, deleted `.AAE` edit files, thumbnail caches and macOS sidecars, and `--flatten` deleted Sony sidecars whose video was gone. An `.AAE` holds the edits made on the iPhone, so deleting it cannot be undone, and it went against the project's rule of moving things aside instead of deleting them.
**Fix:** `--move-junk` (with `--delete-junk` kept as its old name) and `--flatten` move these files into `_junk`, keeping their path, and never overwrite. Every step skips `_junk`, and the final check reports what is in it.

#### BUG-28 The step-by-step run never asked about cleanup
**Found by:** Michele Kummer · **Affects:** workflow · **Fixed in:** `b6166b8`

`/fix-media-dates` asked about the optional steps but treated cleanup as a reminder at the end, so the one step that deletes was never offered as a choice.
**Fix:** Cleanup is now step 13, "Clean up converted files", an optional step the command always asks about, before the dry run ends and again after `--apply` if it was not run.

#### BUG-29 `--flatten` left ads in their subfolders
**Found by:** Michele Kummer · **Affects:** photos and videos (ads) · **Fixed in:** `98dfd1f`

`--flatten --root E:\Pictures\2020\_ads` moved none of the 340 ads, and the dry run reported every folder as kept. There were three causes:
- `flatten` only looked one subfolder deep inside `_ads`, but `--quarantine-ads` keeps each ad's subfolder path, so these ads were two levels down (`_ads\Temp\2020-01-06\`).
- It only recognised the ads folder as `<root>/_ads`. With the `_ads` folder itself as the root, it looked for `_ads\_ads` and treated the ads like ordinary files, leaving any without a Date Taken (most ads) as `LEFT (no Date Taken)`.
- It skipped game `.raw` ads, which `--quarantine-ads` moves into `_ads`.

A root typed with a trailing backslash would also have made every emptied folder look kept. Separately, the `--help` text added for this fix had a backslash path that Python warned about (`SyntaxWarning: "\P" is an invalid escape sequence`).
**Fix:** Inside `_ads`, flatten now finds ads in subfolders at any depth, `.raw` included, and moves them up into `_ads`. A root named `_ads` is flattened as the ads folder, and its emptied subfolders go into the `_empty_folders` beside it (`E:\Pictures\2020\_empty_folders\_ads`), as a run on the year folder would put them. The root path is normalised before folders are compared, and the help text escapes its backslashes. Two tests in `tests/test_smoke.py` cover flattening `_ads` from the year folder, and from `_ads` itself with ads two levels down, a `.raw` ad and a trailing backslash.

#### BUG-30 `--flatten` left ads in a year folder inside `_ads`
**Found by:** Michele Kummer · **Affects:** photos and videos (ads) · **Fixed in:** `8b96016`

`--flatten --root E:\Pictures\_ads\2022` moved none of the 2,446 ads and listed nothing as `LEFT`. The fix for BUG-29 only treated the root as an ads folder when the root itself was named `_ads`. This root was named `2022`, so it was flattened as an ordinary photo folder, which looks only one subfolder deep, and the ads sat two levels down (`Temp\2022-02-14\`). The folder was laid out this way because of BUG-31.
**Fix:** A root anywhere inside an `_ads` folder is flattened as an ads folder: every file at any depth moves up into the root, dated or not. Its emptied subfolders go into its own `_empty_folders`, not into the folder above `_ads`, and each move is listed under the root's own name (`2022/Temp/2022-02-14/ad.png -> 2022/ad.png`). A test in `tests/test_smoke.py` flattens `_ads\2022` with ads two levels down and a `.raw` ad.

#### BUG-31 `--quarantine-ads` put every year's ads in one `_ads`
**Found by:** Michele Kummer · **Affects:** photos and videos (ads) · **Fixed in:** `8b96016`

Run on `E:\Pictures`, the folder that holds the year folders, `--quarantine-ads` moved each ad to `<root>\_ads\<its path>`, so `2022\Temp\ad.png` went to `_ads\2022\Temp\ad.png`. That put every year's ads in a single `E:\Pictures\_ads` instead of keeping them with their year. It also skipped holding folders only at the top level, so once ads were inside a year folder, a later run would have moved them again.
**Fix:** When the root holds year folders, an ad in a year folder goes into that year's own `_ads` (`2022\_ads\Temp\ad.png`). Day folders such as `2022-02-14` are not taken for years, so a run on one year folder is not split by day. Holding folders are skipped at every depth, and each moved file is listed with where it went. Ads already gathered in `E:\Pictures\_ads\2022` are not moved back into `E:\Pictures\2022\_ads`; flattening that folder works where it is (BUG-30). Two tests in `tests/test_smoke.py` cover a run on the folder holding the years and a run on one year folder.

#### BUG-32 Other steps went into a year's own `_ads`
**Found by:** Claude · **Affects:** photos and videos (ads) · **Fixed in:** `8b96016`

After the fix for BUG-31, a run of `--quarantine-ads` on `E:\Pictures` puts ads in each year's own `_ads` (`2022\_ads`). Every other step skipped holding folders such as `_ads`, `_junk` and `_incomplete` only at the top of the root, so a run on `E:\Pictures` went into `2022\_ads`. `--fill-blanks` would have given each ad a Date Taken from its day folder, and `--apply-moves` would then have filed it with the real photos, which is what setting ads aside is meant to prevent. `Cleanup-Pictures.ps1` had the same top-level check. Found by a dry run on synthetic files, before any real run.
**Fix:** `organize.py` and `Cleanup-Pictures.ps1` now skip holding folders at any depth, and the `--quarantine-ads` help text describes the per-year `_ads`. A test in `tests/test_smoke.py` runs `--all --apply` on a root with an ad in `2022\_ads` and junk in `2022\_junk` and checks both are left alone and the ad stays undated. A test in `tests/test_bmp_and_ads.py` checks that `Cleanup-Pictures.ps1` leaves a converted BMP in `2022\_ads` alone.

#### BUG-33 Phone thumbnails were dated and flattened in among the photos
**Found by:** Michele Kummer · **Affects:** photos (phone thumbnails) · **Fixed in:** `a8db9d2`

An import from a phone brought along its gallery's thumbnail cache: 2,520 small JPEGs named only by a number (`46.jpg`, `1020.jpg`), put loose in the import's `2026-11-02` folder. They have no camera info and no Date Taken, so `--fill-blanks` gave each one the folder's date at 12:00:00, and `--flatten` then moved them up into `Pictures\2026` beside the real photos. With an earlier import there were 4,048 in all. They are not byte-for-byte copies, so the duplicate finder could not catch them, and comparing them with both photo libraries showed that some are the only copy left of a photo, so they could not simply go to `_junk`.
**Fix:** `--move-junk` recognises a phone thumbnail (`is_phone_thumbnail`: a JPEG named only by a number, at most 1024 pixels on its long side, with no camera Make or Model) and moves it into a new `_thumbnails` holding folder, which every step skips and the final check reports (`IN THUMBNAILS`). `Cleanup-Pictures.ps1` skips it too. On the real files it caught 4,005 of the 4,014 thumbnails and none of the photos. `PhoneThumbnailTests` in `tests/test_fix_extensions_and_junk.py` covers the check, the move, name clashes, `--all` setting them aside before they get a date, and the final check.

#### BUG-34 Phone thumbnails were set aside before they got a date, with no way to opt out
**Found by:** Michele Kummer · **Affects:** photos (phone thumbnails) · **Fixed in:** `4b5f2ed`

The fix for BUG-33 made `--move-junk` move phone thumbnails into `_thumbnails`. `--move-junk` is step 3 and part of `--all`, so it runs before `--fill-blanks` (step 8). On `E:\Pictures\2022` it moved 4,017 thumbnails, from the year folder itself and from 196 day folders under `Temp`, into `_thumbnails` with no Date Taken. Every step skips `_thumbnails`, so the folders' dates were lost, and the move could not be left out of a run. The 4,017 moves were undone from the audit workbook's Run log, putting each file back where it came from.
**Fix:** `--move-junk` no longer touches phone thumbnails. A new optional phase, `--move-thumbnails` (slash command `/move-thumbnails`), moves them into `_thumbnails` only once they have a Date Taken, and lists any without one as `LEFT`. It is not part of `--all`; added to it, it runs after the dates are written. Tests in `tests/test_fix_extensions_and_junk.py` and `tests/test_dry_run.py` cover it, and the sample generator adds `--move-thumbnails` to its run (US-54).

#### BUG-35 `--flatten` only looked one subfolder deep
**Found by:** Michele Kummer · **Affects:** photos and videos · **Fixed in:** `a155436`

`--flatten --root E:\Pictures\2022` left every photo in `Temp\<number>` folders where it was, and did not list them as `LEFT` either, so nothing said they had been passed over. `flatten` found its files with `iter_media`, which lists the folders directly inside the root and the files directly inside each of those, and goes no deeper. `Temp\5\photo.jpg` is two levels down, so it was never seen, and `Temp` was never emptied, so the final check reported it as `NOT FLATTENED`. The other steps that set files aside (`--quarantine-ads`, `--move-junk`) already searched every depth. Going one level deep also meant the opposite problem one level up: every first-level folder was emptied, whatever its name, including folders named for a child, a trip or a wedding.
**Fix:** `--flatten` now goes all the way down through dated folders, scratch folders (Temp, Junk, Delete, Weird, Review) and every folder below a scratch folder, and leaves every other folder as it is, listed as `KEPT (named folder)` (US-55). A camcorder file with no date in its name takes the date of the nearest dated folder above it. Orphan Sony sidecars are looked for in the same folders. The name clash checks and the final check use the same rule, and the final check lists named folders as `NAMED FOLDER (left as is)` instead of `NOT FLATTENED`. `iter_media`, which nothing else used, was replaced by `_flatten_walk`. Two tests in `tests/test_smoke.py` cover the scratch folder names and a flatten of a year folder with files two and three levels down in `Temp`, named folders, `_review` and the final check.

#### BUG-37 A 1904 placeholder date was kept, and dates before 1970 stopped timestamp sync
**Found by:** Michele Kummer · **Affects:** photos · **Fixed in:** `575d9bb`

An edge case. `--sync-timestamps --apply` on `E:\Pictures\2020` stopped partway with `OSError: [Errno 22] Invalid argument`. The photo it stopped on, `Temp\2020-06-14\VideoCapture_20200614-211024.jpg`, is a Windows frame grab whose EXIF Date Taken is `1904:01:01 00:00:00`: QuickTime's time zero, which the capturing app wrote instead of leaving the field empty. Two things went wrong. First, `_parse_exif_dt` accepted any date it could read, so `--fill-blanks` treated the photo as already dated and never used the date in its name. Video dates already threw away anything before 1971, but photo dates had no such check. Second, `sync_timestamps` called `datetime.timestamp()` to turn the date into a file time. That asks the C library for the local time zone, and on Windows the library rejects every date before 1970, so any photo older than 1970, such as a scanned print, would stop the step in the same way. Windows itself stores file times back to 1601, so the limit was Python's, not the file system's. The call was also outside the `try`, so one bad date stopped the whole step instead of being reported.

**Steps to reproduce**
1. Write a JPEG named `VideoCapture_20200614-211024.jpg` with EXIF `DateTimeOriginal` set to `1904:01:01 00:00:00`.
2. Run `--fill-blanks --apply`, then `--sync-timestamps --apply`.

**Expected:** `--fill-blanks` writes 2020-06-14 21:10:24 from the filename, and the sync sets the file times to it. A photo dated 1955 is synced to 1955.
**Actual:** `--fill-blanks` counts the photo as already dated, and the sync stops with `OSError: [Errno 22]`.

**Fix:** A Date Taken of exactly 1904-01-01 00:00:00 (`PLACEHOLDER_DATES`) is read as blank, so `--fill-blanks` replaces it with the date in the filename or folder name. 1904 dates at any other time are kept. A HEIC photo whose `DateTimeOriginal` is the placeholder now falls back to `DateTimeDigitized`. A new `_local_timestamp` turns a date before 1970 into a file time by finding the time zone offset 28 years on (or a multiple of 28, which keeps weekdays and leap years lined up) and shifting back, so scanned photos are synced to their real dates. The conversion is inside the `try`, so a date that still cannot be converted is listed as `FAILED` and the rest are synced. Ten tests in `tests/test_old_and_placeholder_dates.py` cover it.

#### BUG-38 Timestamp sync rewrote and listed files that were already synced
**Found by:** Michele Kummer · **Affects:** photos and videos · **Fixed in:** `407497b`

A second `--sync-timestamps --apply` run listed almost every file as `SYNCED` again, as if the first run had not worked. It had: `sync_timestamps` simply never looked at a file's current Date Created and Date Modified before writing them, so it wrote the same times again and counted every dated file as synced. Only files with no Date Taken were left out, which is why it was almost every file rather than all of them. The preview did the same, listing every file as `WOULD SYNC`. Nothing was harmed, but the output could not show what a run had actually changed.

**Steps to reproduce:** run `--sync-timestamps --apply` on a folder of dated photos twice.

**Expected:** The second run changes nothing and lists no file.
**Actual:** The second run lists every dated file as `SYNCED`.

**Fix:** A new `_already_synced` compares the file's Date Created (on Windows) and, for unedited files, its Date Modified with the Date Taken before anything is written. A file within 2 seconds (`SYNC_TOLERANCE_SECONDS`) on every time that would be set is counted as `already-synced`, not listed, and not written. The 2 seconds allow for FAT32 and exFAT drives, which store Date Modified in 2-second steps. An edited file's Date Modified is not compared, since sync leaves it alone. Twelve tests in `tests/test_sync_timestamps.py` cover it.

#### BUG-39 Phone transfer stubs were not set aside as incomplete
**Found by:** Michele Kummer · **Affects:** photos · **Fixed in:** `5be9fb5`

`E:\Pictures\2018\Temp` held 451 photos of 16 to 345 bytes (shown as 1 KB in Explorer) that `--move-incomplete` left where they were. None of them holds any picture. Each is an MTP object property list, which Windows can leave under a photo's name when a copy from a phone over MTP fails: a 4-byte count, then that many entries of object handle, property code (`0xDC08` date created, `0xDC44` file name, `0xDC89` size and so on), data type and value. `_incomplete_kind` only looked for files that were 0 bytes or all null bytes, and these are neither, so they stayed in their dated folders, and `--fix-extensions` listed each one as `UNKNOWN FORMAT (left alone)`.

**Steps to reproduce:** run `--move-incomplete` on `E:\Pictures\2018\Temp`, or on a folder holding a `.jpg` whose bytes are `01 00 00 00 17 1A 00 00 89 DC 06 00 DE 2E 00 00`.

**Expected:** The file is moved to `_incomplete` as the remains of a failed transfer.
**Actual:** The file is left where it is, and `--fix-extensions` lists it as `UNKNOWN FORMAT`.

**Fix:** A new `_is_mtp_prop_list` recognises the property list. A file counts only if it is between 16 bytes and 64 KB, every entry's property code is in the MTP range `0xD000` to `0xDFFF`, every data type is a known one, and the entries end exactly at the end of the file, so no real photo can match. `_incomplete_kind` returns `transfer-stub` for it, and `--move-incomplete` moves it to `_incomplete` with the folder's date added, as it does other incomplete files. `--fix-extensions` now lists it as `TRANSFER STUB (no picture, left for --move-incomplete)` instead of `UNKNOWN FORMAT`. A preview on `E:\Pictures\2018\Temp` would move all 451. Four tests in `tests/test_transfer_stubs.py` cover it.

#### BUG-40 Writing a date into a PNG, or converting it to JPEG, dropped its XMP
**Found by:** Claude · **Affects:** photos (PNG) · **Fixed in:** `76022e8`

Found while building US-60. `_write_exif_date_image` re-saves a PNG through Pillow with only its EXIF and colour profile, so `--fill-blanks` dropped every text chunk in the PNG, the XMP packet included. `_convert_to_jpeg` saved the JPEG with EXIF only, so `--convert-png` lost the XMP the same way. An iPhone screenshot named `IMG_1234.PNG` carries its "Screenshot" tag in that XMP, so once it had been dated or converted, `--move-screenshots` no longer recognised it and left it among the photos. Any other XMP, such as a caption or a rating, was lost too.
**Fix:** `_write_exif_date_image` now copies the PNG's text chunks, XMP included, into the re-saved file. `_convert_to_jpeg` passes the XMP on to the JPEG; Pillow 11 and later write it, and older versions leave it out as before. `KeepScreenshotTagTests` in `tests/test_sort_pictures.py` checks that `--fill-blanks`, `--convert-png` and writing a date into the JPEG all keep the tag.

#### BUG-41 Thumbnails from newer Android phones were not set aside
**Found by:** Michele Kummer · **Affects:** photos · **Fixed in:** `78fb788`

`is_phone_thumbnail` only accepted a name of 1 to 7 digits, the way older phones number their gallery thumbnails (`46.jpg`). Android 11 and later number media from 1000000000, so their thumbnails are named like `1000000714.jpg`, and `--move-thumbnails` left them among the photos. `E:\Pictures\2024` held 3,159 of them: JPEGs of 512 pixels or less with no camera Make or Model. Eight more had a `_2024-10-15` suffix, which `--flatten` adds when a name is already taken.
**Fix:** `_PHONE_THUMB_NAME_RE` now accepts 1 to 10 digits, followed by an optional `_YYYY-MM-DD` suffix. Longer numbers are still not thumbnails, so the 19 digit names some apps give full size photos (`1038549574306920334.JPG`) stay where they are, as do names like `1000000714_edited.jpg`. A preview on `E:\Pictures\2024` would now move 3,171 phone thumbnails. Two tests in `PhoneThumbnailTests` in `tests/test_fix_extensions_and_junk.py` cover the new names and the ones it must still leave alone.

</details>
