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
| User stories | 44 (30 Done, 2 Partly done, 12 Not started) |
| Bugs | 32 (2 open, 30 resolved) |

| Bugs found by | Open | Resolved | Total |
|---|---|---|---|
| Michele Kummer | 0 | 13 | 13 |
| Claude | 2 | 17 | 19 |
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
<summary><strong>Epic 2 — Correct file types and dates</strong> (US-04 to US-08, US-29, US-44)</summary>

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

- `--report-only` reads photo dates from EXIF (JPEG, PNG and TIFF, and the EXIF embedded in HEIC) and video dates from the MOV/MP4 container. It needs no external tools.
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
- The original is left in place. `Cleanup-Pictures.ps1` deletes it only once the JPEG is confirmed to be the same picture (same size, pixels within 1%), as for PNGs (US-11).
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

</details>

<details>
<summary><strong>Epic 3 — Organize folders</strong> (US-09 to US-11)</summary>

Put each photo and video where its date says it belongs, then tidy the folder structure.

#### US-09 Move photos and videos to the folder for their date
As a media owner, I want each photo and video in a folder named for its real date, so that folder names can be trusted.

- `--apply-moves` moves a photo or video whose date differs from its folder's date into a sibling `YYYY-MM-DD` folder.
- Works at any depth. Each file is checked against the folder it sits in, and moves to a sibling of that folder: `Trip\2019-08-30\x.jpg` taken on the 31st moves to `Trip\2019-08-31`, not up to the root.
- A file loose in the root is never moved out of it. It is checked against the root's own name; if that is a different date, it is listed as `in-root-date-differs` and left where it is.
- A file with no date inside it, in a dated folder, gets that folder's date appended to its name (`IMG_1_2019-08-30.jpg`), so the date survives a later move.
- A name already taken at the target is skipped as a `COLLISION` and never overwritten.
- Without `--apply` it lists each move (`WOULD MOVE`) and rename, creates no folder, and reports the same collisions a real run would meet.

**Status:** Done

#### US-10 Flatten dated subfolders
As a media owner, I want every dated photo and video moved up into the media folder itself, so that I have one flat folder per year.

- `--flatten` (or `/flatten-media`) moves photos and videos that have a date up out of their subfolders. A name already taken in the root gets a `_<date-taken>` ending.
- Camcorder, MPEG, WMV and AVI videos move too, going by the date in the filename, else the subfolder name. The date is appended to the name when it came from the folder.
- Inside `_ads`, files in subfolders at any depth, game `.raw` ads included, move up into `_ads` itself, dated or not. The same holds when the root given is an `_ads` folder itself (`E:\Pictures\2020\_ads`), whose emptied subfolders go into the `_empty_folders` beside it (BUG-29). It also holds for a root anywhere inside an `_ads` folder (`E:\Pictures\_ads\2022`), whose emptied subfolders go into its own `_empty_folders` (BUG-30).
- Subfolders left empty are moved into `_empty_folders`, keeping their path. Nothing is deleted.
- Without `--apply` it only previews.

**Status:** Done

#### US-11 Remove leftover PNGs after conversion
As a photo owner, I want the PNG left behind by a conversion removed, and empty folders set aside, so that the folder is clean.

- `Cleanup-Pictures.ps1` deletes a PNG only when it has already been converted to JPEG. Nothing else is ever deleted.
- **Which files are paired:** each `.png` with a `.jpg`, else a `.jpeg`, of the same base name in the same folder. Letter case does not matter (`IMG_1.PNG` pairs with `img_1.jpg`). Files in different folders are never paired.
- **How the two pictures are compared**, in two checks, both through .NET's `System.Drawing`:
  1. **Size.** Only each file's header is read, to get its width and height in pixels. They must match, and the JPEG must not be empty. `--convert-png` keeps the size, so a real conversion always matches.
  2. **Pixels.** Both pictures are decoded and shrunk to 128x128, and the mean difference of their red, green and blue values is taken as a percentage (0 = same picture). This is the same measure as `--visual-compare`, and gives the same score to within 0.02%. The PNG counts as converted at **1% or less**, which `--visual-compare` calls `DUPLICATE` with high confidence. `-MaxPixelDifference` changes the limit.
  - Measured on test pictures: a converted screenshot scores 0.01% and a converted photo-like picture 0.03%. A different screenshot of the same size scores 12–35%. Random per-pixel noise, the hardest case for JPEG, scores 1.7% after conversion, so it is kept unless the limit is raised to 2.
  - File size, EXIF dates and modified times are not compared.
- **When they differ:** a different size, a difference over the limit, or a file that cannot be read means the files are treated as different pictures. Both are kept, and the PNG is listed with the reason: `KEPT (not the same picture, PNG 1170x2532, JPG 4032x3024)`, `KEPT (not the same picture, pixel difference 11.9%)`, or `cannot read picture size` / `cannot read pixels`.
- Every other file that shares a name is kept: a Live Photo video next to its photo, a sidecar (`.xmp`, `.aae`), or a HEIC next to a JPG.
- `_ads`, `_incomplete`, `_no-image-data` and `_empty_folders` are skipped.
- Empty folders are moved into `_empty_folders`, keeping their path.
- It previews unless `-Apply` is given. The console, the summary and the audit workbook all list each PNG deleted (or that would be) and each one kept.

**Status:** Done

</details>

<details>
<summary><strong>Epic 4 — Clear out files that aren't real photos or videos</strong> (US-12 to US-14, US-30)</summary>

Move ads and broken files out of the way, and delete files that hold no picture or recording.

#### US-12 Set ad images and videos aside
As a media owner, I want ad and app-cache images and videos moved out of my media folders, so that I can review and delete them in one place.

- `--quarantine-ads` moves photos and videos with an ad-style name and no camera information into `_ads`. Examples of ad-style names: a UUID, `UnityAdsCache-<hash>`, `news_images%2F…`.
- Camera information is EXIF Make/Model on a photo, or a device-make tag on a video. A file that has it is never treated as an ad.
- Run on the folder that holds the year folders (`E:\Pictures`), an ad in a year folder goes into that year's own `_ads` (`2022\_ads`), keeping the rest of its path. Only ads in other folders, or loose in the root, go into the root's `_ads`. Ads already in an `_ads` folder at any depth are not moved again (BUG-31), and the other steps leave a year's own `_ads` alone (BUG-32).
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

- `--move-incomplete` moves files that are 0 bytes or all null bytes, and videos with no video header, into `_incomplete`, keeping their subfolder path.
- Files in the older `_no-image-data` folder are folded into `_incomplete`.
- Nothing is deleted. Without `--apply` it only previews.

**Status:** Done

#### US-14 Set leftover sidecar files aside
As a media owner, I want files that hold no picture or recording moved out of my media folders, but not deleted, so that they don't clutter the folders and I can still get one back.

- `--move-junk` moves `.AAE` iPhone photo-edit files, `Thumbs.db`/`ehthumbs*.db` thumbnail caches, and macOS `._` sidecars into `_junk`, keeping their subfolder path. Nothing is deleted (BUG-27).
- A `._` file is treated as junk only when its contents carry the AppleDouble signature.
- Thumbnail caches are matched by whole file name only, so `west sucking thumb.jpg` is safe.
- A path already taken in `_junk` is a `COLLISION`, and the file stays where it is.
- `--flatten` moves Sony `.modd`/`.moff` sidecars whose file is gone into `_junk` too.
- The final check reports what is still in `_junk` (`IN JUNK`). `--delete-junk` still works as the old name of the flag, and moves too.
- Without `--apply` it only lists the files.

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
  - files in `_ads` and in `_incomplete`;
  - photos among videos, or videos among photos;
  - subfolders not flattened;
  - name collisions;
  - audit workbooks left behind.
- Its only change is renaming audit workbooks so their name includes the folder and media type, and only with `--apply`.

**Status:** Done

#### US-28 Find plist files saved with a photo name
As a media owner, I want to know which of my "photos" are really plist or XMP files, such as an iPhone `.AAE` edit file saved as `IMG_E5239.JPG`, so that I can decide whether to keep or delete them, instead of seeing date-writing fail on them.

- `--find-plists` searches the folder at every depth, holding folders included, and lists each file with a photo or video name that holds plist (XML or binary), XMP or other XML text, as `NOT MEDIA (plist file named .JPG): 2023-08-07/IMG_E5239.JPG`. It counts them by kind.
- Real photos and videos are never listed: they never start with `<` or `bplist`.
- Every other step reports these files as `NOT MEDIA (... left alone)` and skips them. `--fill-blanks` no longer reports `FAILED to write`, `--convert-png` does not try to convert them, and `--apply-moves` gives them no date suffix (BUG-25). `--fix-extensions` reports `NOT MEDIA` instead of `UNKNOWN FORMAT`.
- Nothing is moved, renamed or deleted. The user decides.
- `tests/test_plists.py` covers each of these.

**Status:** Done

</details>

<details>
<summary><strong>Epic 6 — Workflow, safety and record-keeping</strong> (US-19 to US-23, US-26, US-27, US-31)</summary>

Run the steps together, preview them, never lose a photo or video by surprise, and keep a history.

#### US-19 Run every step in one command
As a media owner, I want one command that runs the routine steps in the right order, so that I don't have to remember it.

- `--all` runs, in order: fix extensions, move junk, move incomplete files, fill blanks, convert PNG, apply moves, sync timestamps. It deletes nothing.
- `--quarantine-ads` and `--flatten` can be added to it.
- It ends with one summary of every step's counts and up to 50 problems per step.
- Without `--apply` it previews every step against the folder as it is now, and says that a later step may do more once the earlier ones have run.

**Status:** Done

#### US-20 Match Explorer's dates to the date taken
As a media owner, I want Date Created and Date Modified to match when the photo or video was taken, so that every Explorer column agrees.

- `--sync-timestamps` sets Date Created to the photo's Date Taken, or the video's Media Created, on every dated file at any depth.
- Date Modified is set too, but only on files that look unedited. A photo looks edited when EXIF `DateTime` differs from `DateTimeOriginal` by a minute or more, or when `Software` names a known editor (Photoshop, Lightroom, Snapseed and others). An edited file keeps its Date Modified.
- Date Created is set through the Win32 API. On other systems only Date Modified is synced.

- Without `--apply` it lists each file that would be synced (`WOULD SYNC`) and changes no timestamp.

**Status:** Partly done. One unreadable file stops the whole step (BUG-02).

#### US-21 Never delete without saying so
As a media owner, I want photos and videos moved aside rather than deleted, except in steps that say they delete, so that mistakes can be undone.

- `_ads`, `_junk`, `_incomplete` and `_empty_folders` hold what was set aside. Every step skips them.
- Only `Cleanup-Pictures.ps1` deletes files: PNGs and BMPs already converted to JPEG. `organize.py` deletes nothing (BUG-27).
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
- `/fix-media-dates <folder> --apply` and `/flatten-media <folder> --apply` make the changes. Optional steps (ads, BMP conversion, PNG conversion, timestamp sync, flatten, cleaning up converted files) run only when the user asked for them.
- `/fix-media-dates <folder> --all` previews `organize.py --all` (fix extensions, move junk, move incomplete, fill blanks, convert PNG, apply moves, sync timestamps) in one go, and ends by telling the user to type `/fix-media-dates <folder> --all --apply`, which makes those changes. Ad quarantine and flatten are left out unless `--quarantine-ads` or `--flatten` is added, and cleanup runs on its own.
- Both commands show `[--apply]` in their argument hint (`/fix-media-dates` also shows `[--all]`), and `/media-help` lists every form.
- `/report-opposite-type` only reports, so it has no `--apply`.
- `tests/test_commands.py` checks each of these, and that no command, skill or guide still says `--dry-run` or `-WhatIf`.

**Status:** Done

#### US-27 Every step that changes files has a dry run, and it is the default
As a media owner, I want every step that changes my photos and videos to preview by default, so that I never have to remember a preview flag to stay safe.

- Every `organize.py` step that writes, converts, moves, renames or deletes files lists what it would do (`WOULD WRITE`, `WOULD CONVERT`, `WOULD MOVE`, `WOULD SYNC`, `WOULD DELETE`, ...) and changes nothing unless `--apply` is given. This covers `--fix-extensions`, `--move-junk`, `--move-incomplete`, `--quarantine-ads`, `--fill-blanks`, `--convert-png`, `--apply-moves`, `--sync-timestamps`, `--flatten`, `--final-check` and `--all`.
- A dry run ends with `DRY RUN: nothing was changed. Run the same command again with --apply to make these changes.`
- `Cleanup-Pictures.ps1` previews unless `-Apply` is given. `-WhatIf` still works.
- Reports (`--report-only`, `--compare-collisions`, `--visual-compare`, `--opposite-type`, `--find-plists`, `find_duplicates.py`) change nothing, so they run the same either way. `--visual-compare` no longer needs a flag.
- `--dry-run` is still accepted and means the default. It cannot be combined with `--apply`.
- A dry run is recorded in the audit workbook, marked `yes` in the Dry run column, and never renames the workbook (BUG-05).
- `tests/test_dry_run.py` runs each step without `--apply` and checks that no file's content, name or timestamp changed, then runs it with `--apply` and checks that something did. A new step that changes files fails the test until it is added there.

**Status:** Done

#### US-31 Choose between step by step and all in one go
As a media owner, I want to know how the two ways of running `/fix-media-dates` differ and in what order to run the steps, so that I pick the right one and don't run the steps twice or in the wrong order.

- `/fix-media-dates <folder>` walks through every step and asks which optional steps the user wants: ads, BMP conversion, PNG conversion, timestamp sync, flatten, and cleaning up converted files. It always asks about cleanup, the one step that deletes (BUG-28).
- `/fix-media-dates <folder> --all` runs the routine steps in one go with no questions, fixing extensions first (BUG-26). It deletes nothing.
- The README has a table showing which steps each way runs, says to choose one of them for a folder, and gives the recommended order of every step, from fixing extensions to the final check.
- The README's **Guardrails** section lists the safety rules that hold for every step.
- In the recommended order, the visual compare comes before cleaning up converted files, because cleanup removes one file of each PNG/JPG pair it would compare.

**Status:** Done

</details>

<details>
<summary><strong>Epic 7 — Maintain the plugin</strong> (US-24 to US-25, US-32)</summary>

Change and test the plugin safely.

#### US-24 Test without real photos or videos
As a maintainer, I want tests that run on generated files, so that I can check a change without risking my own photos and videos.

- `py -m unittest discover tests -v` runs the suite. It currently has 64 tests.
- `sample-data/generate.py` makes synthetic test photos. The video tests generate their own small videos with ffmpeg.
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

</details>

<details>
<summary><strong>Epic 8 — Desktop app</strong> (US-33 to US-43)</summary>

Run every step from a window with buttons, checkboxes and settings instead of typing commands. The app runs the existing scripts on this computer, with the same preview-first rules, so it adds no new way to lose a file. Requested by Michele Kummer on 2026-10-26; nothing is built yet.

**Stack** (chosen by Michele Kummer on 2026-10-27): the interface is written in **Vue 3** with plain CSS and built with **Vite**. It is shown in a window by **pywebview**, which uses the Edge WebView2 already in Windows. A small Python layer builds each step's command line, runs `organize.py` or `Cleanup-Pictures.ps1`, and streams their output back to the window. The app starts with `py app.py` and needs nothing beyond the plugin's own Python packages and pywebview. Chosen because the plugin already needs Python, the author knows Vue and CSS, and no second runtime (Node, Rust or a bundled Chromium) has to ship. Electron would be the alternative if a standalone installer for people without Python is ever needed.

#### US-33 Set the project's parameters once
As a media owner, I want to set the folder and the options that every step uses in one place, so that I don't have to repeat them for each button.

- A **Project** panel at the top holds:
  - **Folder to organize** (required): a text box with a **Browse** button, for example `D:\Pictures\2026`. It is passed to every step as `--root`.
  - **Library folder**: the folder that holds the year folders, for example `D:\Pictures`. It is used by **Final check** and **Find the opposite type**. When the folder to organize is named for a year, it fills in with the folder above it.
  - **Audit workbook name**: blank uses the default name (`<folder>_<photos|videos>_media_audit_<date>.xlsx`). Anything typed is passed as `--xlsx`.
  - **PNG quality** and **BMP quality** (US-38).
  - **Cleanup pixel difference limit**: the most two pictures may differ, from 0.1% to 5%, for **Clean up converted files** to count a PNG or BMP as converted. Default 1%. Passed as `-MaxPixelDifference`.
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
| 2 | Scan | `--report-only` | No |
| 3 | Set junk aside | `--move-junk` | Yes |
| 4 | Set incomplete files aside | `--move-incomplete` | Yes |
| 5 | Set ads aside | `--quarantine-ads` | No |
| 6 | Find plist and XMP files | `--find-plists` | No |
| 7 | Convert BMP to JPEG | `--convert-bmp` | No |
| 8 | Fill in missing dates | `--fill-blanks` | Yes |
| 9 | Convert PNG to JPEG | `--convert-png` | Yes |
| 10 | Move to date folders | `--apply-moves` | Yes |
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
- The default is ticked for the seven steps `--all` runs (fix extensions, set junk aside, set incomplete files aside, fill in missing dates, convert PNG to JPEG, move to date folders, sync timestamps), and unticked for the rest, so a full run with the defaults does what `--all` does.
- **Reset to default selection** puts the ticks back to the default. **Select all** and **Clear all** do what they say.
- Ticking **Flatten** while **Move to date folders** is ticked (or the other way round) shows a note that they are alternatives, with a button to untick the other one. It does not block the choice.
- Ticking **Clean up converted files**, the only step that deletes, shows a note saying so.
- The selection is saved with the project's parameters (US-33).

**Status:** Not started

#### US-36 Preview or run every selected step
As a media owner, I want one button that previews every ticked step and one that runs them, so that I can check the whole plan and then carry it out.

- **Preview all selected** runs each ticked step without `--apply`, in the recommended order, and changes nothing. It says, as `--all` does, that a later step may do more once the earlier ones have really run.
- **Run all selected** first asks for confirmation, listing the steps that will change files. When **Clean up converted files** is ticked, the confirmation says it deletes the PNGs and BMPs it has checked. When no preview has run since the selection or settings changed, it says so and offers **Preview first**.
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
| Clean up converted files | Deletes each PNG and BMP already converted, after checking they are the same picture. This cannot be undone. |
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

</details>

---

## Part 2 — Bugs

Severity: **High** means files are lost or the plugin can't be used. **Medium** means a wrong result, or a step that fails or stops. **Low** means a cosmetic problem, or one with a workaround.

<details>
<summary><strong>Open bugs</strong> (2, both found by Claude on 2026-10-21)</summary>

Each was reproduced on synthetic files, except where noted.

#### BUG-02 One unreadable photo or video stops a step, and nothing is recorded
**Severity:** Medium · **Found by:** Claude · **Affects:** photos and videos · **Where:** [organize.py](../skills/media-date-organizer/scripts/organize.py) `sync_timestamps`, `scan`

`fill_blanks` catches read errors per file, but `sync_timestamps` and `scan` do not. `scan` is used by `--report-only`, `--apply-moves`, `--compare-collisions` and `--visual-compare`.

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

</details>

<details>
<summary><strong>Resolved bugs</strong> (30: 13 found by Michele Kummer, 17 by Claude)</summary>

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

</details>
