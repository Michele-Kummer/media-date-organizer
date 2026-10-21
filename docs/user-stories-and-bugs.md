# User stories and bugs

This document records the requirements for **media-date-organizer** as user stories grouped into epics, followed by every known bug, open and resolved, and who found each one. It is meant as a worked example of how requirements were generated for this project.

**How it was made (2026-10-21)**

- **User stories:** written with Claude Code (Claude Opus 5.5) by reading the plugin's code, docs and git history. Each story's acceptance criteria describe how the plugin behaves today.
- **Open bugs:** found by Claude while writing the stories. Each one was reproduced on synthetic files.
- **Resolved bugs:** taken from the git history. Michele Kummer, the project's author, said which ones they found.

**Status** on each story is *Done* when every criterion holds, or *Partly done* when some do not, with the gap named.

Each epic below can be expanded and collapsed.

**Who the stories are for**

- **Media owner:** someone on Windows with folders of photos and videos from phones, cameras and apps, who wants Explorer to show the right date on every one. Used for stories that cover both photos and videos.
- **Photo owner:** the same person, in stories that only cover photos.
- **Maintainer:** whoever changes or tests the plugin.

Each bug says what it **Affects**: photos, videos, both, or something other than media files (setup, the audit workbook).

## At a glance

| | Count |
|---|---|
| Epics | 7 |
| User stories | 25 (18 Done, 7 Partly done) |
| Bugs | 24 (4 open, 20 resolved) |

| Bugs found by | Open | Resolved | Total |
|---|---|---|---|
| Michele Kummer | 0 | 6 | 6 |
| Claude | 4 | 14 | 18 |
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
<summary><strong>Epic 2 — Correct file types and dates</strong> (US-04 to US-08)</summary>

Make every photo and video report its real format and its real date, and make Windows Explorer show it.

#### US-04 Correct wrong extensions on photos and videos
As a media owner, I want photos and videos whose extension does not match their content renamed, so that every tool reads them correctly.

- `Fix-Extensions.ps1` reads the start of every file (recursively) and recognises:
  - photos: PNG, JPEG, HEIC/HEIF, GIF, WEBP, TIFF and BMP;
  - videos: MP4/MOV, 3GP/3G2, M2TS/MTS, MPG, WMV and AVI.
- A mismatched extension is corrected, for example a `.PNG` that is really HEIC, or a `.HEIC` that is really a QuickTime video. 3GP/3G2 keep their own extension.
- Empty files are listed as `EMPTY`. Unrecognised non-empty files are listed as `UNKNOWN`. Sony `.modd`/`.moff` video sidecars are counted, not reported as unknown.
- `-WhatIf` previews without renaming.

**Status:** Done

#### US-05 See which photos and videos have no date
As a media owner, I want a report of every photo's and video's real date and what would happen to it, so that I can decide before anything changes.

- `--report-only` reads photo dates from EXIF (JPEG, PNG and TIFF, and the EXIF embedded in HEIC) and video dates from the MOV/MP4 container. It needs no external tools.
- Each file is given an action: keep, move, fill-blank or skip. The results are written to the audit workbook.
- Nothing is changed.

**Status:** Partly done. Files loose in the root, or more than one folder deep, are not reported (BUG-03).

#### US-06 Fill in missing Date Taken on photos
As a photo owner, I want photos with a blank Date Taken to get one from the best evidence available, so that they sort correctly.

- Looks at the root and every subfolder at any depth, skipping `_ads`, `_incomplete` and `_empty_folders`.
- The date comes from the filename (`IMG_20190830_101500`), else from the containing folder's name (`2019-08-30`, `2026-08-19 11-44-31`, `08-19-2026`, `Aug 19 2026`) at 12:00:00.
- The file's modified time is never used, because copying and importing resets it.
- JPEGs get their EXIF block replaced without re-encoding the picture. HEIC is written with ExifTool.
- Empty files are skipped and counted.
- `--dry-run` lists what would be written.

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
- The conversion runs only after the user confirms.

**Status:** Partly done. There is no `--dry-run` preview (US-22).

</details>

<details>
<summary><strong>Epic 3 — Organize folders</strong> (US-09 to US-11)</summary>

Put each photo and video where its date says it belongs, then tidy the folder structure.

#### US-09 Move photos and videos to the folder for their date
As a media owner, I want each photo and video in a folder named for its real date, so that folder names can be trusted.

- `--apply-moves` moves a photo or video whose date differs from its folder's date into a sibling `YYYY-MM-DD` folder.
- A file with no date inside it, in a dated folder, gets that folder's date appended to its name (`IMG_1_2019-08-30.jpg`), so the date survives a later move.
- A name already taken at the target is skipped as a `COLLISION` and never overwritten.

**Status:** Partly done. Files loose in the root, or more than one folder deep, are not moved (BUG-03). There is no `--dry-run` preview, though `--report-only` shows the plan.

#### US-10 Flatten dated subfolders
As a media owner, I want every dated photo and video moved up into the media folder itself, so that I have one flat folder per year.

- `--flatten` (or `/flatten-media`) moves photos and videos that have a date up out of their subfolders. A name already taken in the root gets a `_<date-taken>` ending.
- Camcorder, MPEG, WMV and AVI videos move too, going by the date in the filename, else the subfolder name. The date is appended to the name when it came from the folder.
- Inside `_ads`, files move up into `_ads` itself, dated or not.
- Subfolders left empty are moved into `_empty_folders`, keeping their path. Nothing is deleted.
- `--dry-run` previews.

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
- `-WhatIf` previews. The console, the summary and the audit workbook all list each PNG deleted and each one kept.

**Status:** Done

</details>

<details>
<summary><strong>Epic 4 — Clear out files that aren't real photos or videos</strong> (US-12 to US-14)</summary>

Move ads and broken files out of the way, and delete files that hold no picture or recording.

#### US-12 Set ad images and videos aside
As a media owner, I want ad and app-cache images and videos moved out of my media folders, so that I can review and delete them in one place.

- `--quarantine-ads` moves photos and videos with an ad-style name and no camera information into `_ads`. Examples of ad-style names: a UUID, `UnityAdsCache-<hash>`, `news_images%2F…`.
- Camera information is EXIF Make/Model on a photo, or a device-make tag on a video. A file that has it is never treated as an ad.
- Nothing is deleted. `--dry-run` previews.

**Status:** Done

#### US-13 Set incomplete files aside
As a media owner, I want failed copies moved out of the way, so that they stop showing up as photos or videos with no date.

- `--move-incomplete` moves files that are 0 bytes or all null bytes, and videos with no video header, into `_incomplete`, keeping their subfolder path.
- Files in the older `_no-image-data` folder are folded into `_incomplete`.
- Nothing is deleted. `--dry-run` previews.

**Status:** Done

#### US-14 Delete leftover sidecar files
As a media owner, I want files that hold no picture or recording deleted, so that they don't clutter my media folders.

- `--delete-junk` deletes `.AAE` iPhone photo-edit files, `Thumbs.db`/`ehthumbs*.db` thumbnail caches, and macOS `._` sidecars.
- A `._` file is deleted only when its contents carry the AppleDouble signature.
- Thumbnail caches are matched by whole file name only, so `west sucking thumb.jpg` is safe.
- This is a real delete. `--dry-run` previews, and Claude asks before running it.

**Status:** Done

</details>

<details>
<summary><strong>Epic 5 — Check and report, without changing anything</strong> (US-15 to US-18)</summary>

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
- `--visual-compare --dry-run` compares the pixels of two photos, or four frames of two videos. It reports `DUPLICATE`, `DIFFERENT` or `UNSURE` with a confidence level, which goes into its own column in the audit workbook.
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
- Its only change is renaming audit workbooks so their name includes the folder and media type. `--dry-run` previews that.

**Status:** Done

</details>

<details>
<summary><strong>Epic 6 — Workflow, safety and record-keeping</strong> (US-19 to US-23)</summary>

Run the steps together, preview them, never lose a photo or video by surprise, and keep a history.

#### US-19 Run every step in one command
As a media owner, I want one command that runs the routine steps in the right order, so that I don't have to remember it.

- `--all` runs, in order: delete junk, move incomplete files, fill blanks, convert PNG, apply moves, sync timestamps.
- `--quarantine-ads` and `--flatten` can be added to it.
- It ends with one summary of every step's counts and up to 50 problems per step.

**Status:** Partly done. `--all --dry-run` is refused, so the combined run cannot be previewed.

#### US-20 Match Explorer's dates to the date taken
As a media owner, I want Date Created and Date Modified to match when the photo or video was taken, so that every Explorer column agrees.

- `--sync-timestamps` sets Date Created to the photo's Date Taken, or the video's Media Created, on every dated file at any depth.
- Date Modified is set too, but only on files that look unedited. A photo looks edited when EXIF `DateTime` differs from `DateTimeOriginal` by a minute or more, or when `Software` names a known editor (Photoshop, Lightroom, Snapseed and others). An edited file keeps its Date Modified.
- Date Created is set through the Win32 API. On other systems only Date Modified is synced.

**Status:** Partly done. One unreadable file stops the whole step (BUG-02). There is no `--dry-run` preview.

#### US-21 Never delete without saying so
As a media owner, I want photos and videos moved aside rather than deleted, except in steps that say they delete, so that mistakes can be undone.

- `_ads`, `_incomplete` and `_empty_folders` hold what was set aside. Every step skips them.
- Only `--delete-junk` (non-media sidecars) and `Cleanup-Pictures.ps1` (PNGs already converted to JPEG) delete files.

**Status:** Done

#### US-22 Preview before anything changes
As a media owner, I want to see what a step will do before it does it, so that I never lose a photo or video by surprise.

- `--dry-run` works with fill blanks, flatten, quarantine ads, move incomplete, delete junk, visual compare and final check. `-WhatIf` works with both PowerShell scripts.
- Claude previews each changing step and asks before going ahead.

**Status:** Partly done. These have no dry run:
- `--convert-png`
- `--apply-moves`
- `--sync-timestamps`
- `--all`

`--dry-run` also renames an old-style audit workbook (BUG-05).

#### US-23 Keep a history of everything done to a folder
As a media owner, I want a record of every step run on a photo or video folder, so that I can see later what changed and when.

- The workbook is named `<folder>_<photos|videos>_media_audit_<date>.xlsx`, in the media folder. Whichever kind the folder holds more of picks `photos` or `videos`. Runs on the same day share it.
- Every step appends to the Run log and Run counts sheets. That includes dry runs and both PowerShell scripts.
- If the workbook is open in Excel, the step runs but is not recorded.

**Status:** Partly done. A step that stops on an error records nothing, and in `--all` neither do the steps that finished before it (BUG-02).

</details>

<details>
<summary><strong>Epic 7 — Maintain the plugin</strong> (US-24 to US-25)</summary>

Change and test the plugin safely.

#### US-24 Test without real photos or videos
As a maintainer, I want tests that run on generated files, so that I can check a change without risking my own photos and videos.

- `py -m unittest discover tests -v` runs the suite. It currently has 21 tests.
- `sample-data/generate.py` makes synthetic test photos. The video tests generate their own small videos with ffmpeg.
- Video tests are skipped when ffmpeg is missing. The video date-writing test is skipped when ExifTool is missing. The Date Created test runs only on Windows.
- The PowerShell scripts have no automated tests.

**Status:** Done

#### US-25 Try a change without installing it
As a maintainer, I want to load my local copy into Claude Code, so that I can try a change before publishing it.

- `claude --plugin-dir .` from the clone loads the plugin for that session.

**Status:** Done

</details>

---

## Part 2 — Bugs

Severity: **High** means files are lost or the plugin can't be used. **Medium** means a wrong result, or a step that fails or stops. **Low** means a cosmetic problem, or one with a workaround.

<details>
<summary><strong>Open bugs</strong> (4, all found by Claude on 2026-10-21)</summary>

Each was reproduced on synthetic files, except where noted.

#### BUG-02 One unreadable photo or video stops a step, and nothing is recorded
**Severity:** Medium · **Found by:** Claude · **Affects:** photos and videos · **Where:** [organize.py](../skills/media-date-organizer/scripts/organize.py) `sync_timestamps`, `scan`

`fill_blanks` catches read errors per file, but `sync_timestamps` and `scan` do not. `scan` is used by `--report-only`, `--apply-moves`, `--compare-collisions` and `--visual-compare`.

**Steps to reproduce**
1. Make a photo or video that cannot be read during the step. The repro simulated this with a `PermissionError`; in real use it could be a file locked by another program, or a HEIC photo or a video large enough to cause a `MemoryError`, since both are read whole when no header is found.
2. Run `--sync-timestamps`.

**Expected:** That file is reported as failed and the rest are synced.
**Actual:** The step stops with a traceback, and no audit workbook is written. Under `--all`, the record of the steps that had already finished is lost too, because the workbook is written once at the end.

#### BUG-03 Report and `--apply-moves` only look one folder deep
**Severity:** Medium · **Found by:** Claude · **Affects:** photos and videos · **Where:** `iter_media` in [organize.py](../skills/media-date-organizer/scripts/organize.py)

`scan` looks only at photos and videos exactly one folder below the root. `--fill-blanks`, `--sync-timestamps`, `--flatten` and `--convert-png` work at any depth.

**Steps to reproduce**
1. Create `root\loose.jpg`, `root\2019-08-30\wrong.jpg` and `root\Trip\2019-08-30\deep.jpg`, each with a Date Taken. (A `.mov` in the same places behaves the same way.)
2. Run `--report-only`.

**Expected:** All three files are in the report.
**Actual:** Only `wrong.jpg` is reported.

**Impact:** After `--flatten`, every photo and video is loose in the root, so a later `--report-only` reports none of them.

#### BUG-04 HEIF and AVIF photos are read as MP4 video
**Severity:** Low · **Found by:** Claude · **Affects:** photos (HEIF image sequences and AVIF) · **Where:** `detect_type` in [organize.py](../skills/media-date-organizer/scripts/organize.py)

Any file with an `ftyp` header whose brand is not in the known list is reported as `.mp4`. Two examples:
- a `.heic` with the `hevc` brand (a HEIF image sequence, such as an iPhone burst);
- an AVIF photo.

A HEIF photo read as video has no video date. `--fill-blanks` would then try to write video date tags into it with ExifTool.

**Steps to reproduce:** `detect_type` on a file starting `....ftyphevc` or `....ftypavif` returns `.mp4`.
**Expected:** HEIF brands (`hevc`, `heim`, `heis`, `hevx`) return `.heic`. Unknown brands return `None`.

#### BUG-05 `--dry-run` renames an audit workbook
**Severity:** Low · **Found by:** Claude · **Affects:** the audit workbook (no photo or video is touched) · **Where:** `_default_xlsx` in [organize.py](../skills/media-date-organizer/scripts/organize.py)

Working out today's workbook name renames an old-style `media_audit_<date>.xlsx` to `<folder>_<type>_media_audit_<date>.xlsx`. This happens on every run, previews included.

**Steps to reproduce:** Put today's `media_audit_<date>.xlsx` in a folder and run `--flatten --dry-run`.
**Expected:** Nothing in the folder changes.
**Actual:** The workbook is renamed to `2014_photos_media_audit_<date>.xlsx`.

</details>

<details>
<summary><strong>Resolved bugs</strong> (20: 6 found by Michele Kummer, 14 by Claude)</summary>

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
| BUG-22 | Install commands disagreed about package versions | Setup | Low | Claude | `8c6d76f` |
| BUG-23 | Minimum Python version stated but never checked | Setup | Low | Claude | `8c6d76f` |
| BUG-24 | PowerShell scripts skipped the audit log without `python` on PATH | Audit workbook | Low | Claude | `8c6d76f` |
| BUG-01 | Cleanup deleted Live Photo videos and sidecar files | Photos and videos | High | Claude | 2026-10-21 (uncommitted) |

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

`--fill-blanks` and `--sync-timestamps` only checked files exactly one folder below the root, so photos and videos in nested folders were missed. (BUG-03 is the same limit in `--report-only` and `--apply-moves`.)
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
**Found by:** Claude · **Affects:** setup · **Fixed in:** `8c6d76f`, plus two missed hints on 2026-10-21 (not yet committed)

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
**Severity:** High (permanent data loss) · **Found by:** Claude · **Affects:** photos and videos · **Fixed:** 2026-10-21 (not yet committed)

`Cleanup-Pictures.ps1` treated any two files with the same base name in a folder as duplicates, whatever their type and content, and deleted all but one. `IMG_1234.HEIC` and `IMG_1234.MOV` (a Live Photo) lost the video, and `IMG_5555.JPG` and `IMG_5555.xmp` lost the edits. A file with an extension not on the preference list always lost, and the pass also ran inside `_ads`, `_incomplete` and `_empty_folders`.
**Fix:** The only file it deletes now is a PNG photo with a JPG or JPEG of the same name beside it, and only when both are the same size and differ by no more than 1% in their pixels, as a `--convert-png` conversion does. Videos and sidecars are never deleted. Any other pair is kept, and a PNG whose JPG differs is listed as `KEPT (not the same picture)` with the reason. The holding folders are skipped. The `-PreferredExtOrder` parameter is gone, and `-MaxPixelDifference` is new. US-11 describes how the pictures are compared.

</details>
