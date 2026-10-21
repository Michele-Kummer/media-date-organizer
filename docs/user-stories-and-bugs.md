# User stories and bugs

This document records the requirements for **media-date-organizer** as user stories grouped into epics, followed by every known bug, open and resolved, and who found each one. It is meant as a worked example of how requirements were generated for this project.

**How it was made (2026-10-21)**

- **User stories:** written with Claude Code (Claude Opus 5.5) by reading the plugin's code, docs and git history. Each story's acceptance criteria describe how the plugin behaves today.
- **Open bugs:** found by Claude while writing the stories. Each one was reproduced on synthetic files.
- **Resolved bugs:** taken from the git history. Michele Kummer, the project's author, said which ones they found.

**Status** on each story is *Done* when every criterion holds, or *Partly done* when some do not, with the gap named.

Each epic below can be expanded and collapsed.

**Who the stories are for**

- **Photo owner:** someone on Windows with folders of photos and videos from phones, cameras and apps, who wants Explorer to show the right Date Taken.
- **Maintainer:** whoever changes or tests the plugin.

## At a glance

| | Count |
|---|---|
| Epics | 7 |
| User stories | 25 (16 Done, 9 Partly done) |
| Bugs | 24 (5 open, 19 resolved) |

| Bugs found by | Open | Resolved | Total |
|---|---|---|---|
| Michele Kummer | 0 | 6 | 6 |
| Claude | 5 | 13 | 18 |
| Automated tests | 0 | 0 | 0 |

---

## Part 1 — User stories

<details>
<summary><strong>Epic 1 — Setup and getting started</strong> (US-01 to US-03)</summary>

Install the plugin, learn what it needs, and find out what it can do.

#### US-01 Install the plugin
As a photo owner, I want to install the plugin with one command, so that I can start organizing without copying files around.

- `/plugin install media-date-organizer --marketplace Michele-Kummer/media-date-organizer` installs 3 skills and 4 slash commands.
- Requires Claude Code 2.1.275+, Python 3.9+, `pillow>=10.0`, `openpyxl>=3.1`, and Windows PowerShell 5.1+ or PowerShell 7.
- `/plugin marketplace update michele-kummer` picks up a newer version.

**Status:** Done

#### US-02 Be told what is missing
As a photo owner, I want a clear message when something the plugin needs is missing, so that I know what to install instead of seeing a crash.

- Python older than 3.9: the script stops with "Python 3.9 or later is needed".
- No Pillow: a warning with the `pip install` command. Writing EXIF and converting PNG are refused.
- No openpyxl: scanning still works. The audit workbook is skipped, with a message saying so.
- No ExifTool: HEIC and video files that need a date are listed as `SKIPPED (needs exiftool)`. ExifTool is found on PATH or in winget's default folder.
- No ffmpeg: comparing videos is refused, with the `pip install "imageio-ffmpeg>=0.5"` command.
- The PowerShell scripts find Python as `python`, or through the `py` launcher. They ignore the Microsoft Store stub. With neither available, they say the run was not recorded.

**Status:** Done

#### US-03 See what I can ask for
As a photo owner, I want to see everything the plugin can do, with what to type for each, so that I don't have to read the README.

- `/media-help` lists every command and plain-language request with an example. It changes nothing.

**Status:** Done

</details>

<details>
<summary><strong>Epic 2 — Correct file types and dates</strong> (US-04 to US-08)</summary>

Make every photo and video report its real format and its real Date Taken, and make Windows Explorer show it.

#### US-04 Correct wrong file extensions
As a photo owner, I want files whose extension does not match their content renamed, so that every tool reads them correctly.

- `Fix-Extensions.ps1` reads the start of every file (recursively) and recognises PNG, JPEG, HEIC/HEIF, MP4/MOV, 3GP/3G2, M2TS/MTS, MPG, WMV, AVI, GIF, WEBP, TIFF and BMP.
- A mismatched extension is corrected. 3GP/3G2 keep their own extension.
- Empty files are listed as `EMPTY`. Unrecognised non-empty files are listed as `UNKNOWN`. Sony `.modd`/`.moff` sidecars are counted, not reported as unknown.
- `-WhatIf` previews without renaming.

**Status:** Done

#### US-05 See which files have no Date Taken
As a photo owner, I want a report of every file's real date and what would happen to it, so that I can decide before anything changes.

- `--report-only` reads the dates of JPEG, PNG and TIFF from EXIF, of HEIC from its embedded EXIF, and of MOV/MP4 from the container. It needs no external tools.
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
As a photo owner, I want videos with a blank Media Created to get a date, so that they sort with the photos from the same day.

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
- The original PNG is left for the cleanup script.
- The conversion runs only after the user confirms.

**Status:** Partly done. There is no `--dry-run` preview (US-22).

</details>

<details>
<summary><strong>Epic 3 — Organize folders</strong> (US-09 to US-11)</summary>

Put each file where its date says it belongs, then tidy the folder structure.

#### US-09 Move files to the folder for their date
As a photo owner, I want each file in a folder named for its real date, so that folder names can be trusted.

- `--apply-moves` moves a file whose Date Taken differs from its folder's date into a sibling `YYYY-MM-DD` folder.
- A file with no date inside it, in a dated folder, gets that folder's date appended to its name (`IMG_1_2019-08-30.jpg`), so the date survives a later move.
- A name already taken at the target is skipped as a `COLLISION` and never overwritten.

**Status:** Partly done. Files loose in the root, or more than one folder deep, are not moved (BUG-03). There is no `--dry-run` preview, though `--report-only` shows the plan.

#### US-10 Flatten dated subfolders
As a photo owner, I want every dated file moved up into the media folder itself, so that I have one flat folder per year.

- `--flatten` (or `/flatten-media`) moves files that have a Date Taken up out of their subfolders. A name already taken in the root gets a `_<date-taken>` ending.
- Camcorder, MPEG, WMV and AVI videos move too, going by the date in the filename, else the subfolder name. The date is appended to the name when it came from the folder.
- Inside `_ads`, files move up into `_ads` itself, dated or not.
- Subfolders left empty are moved into `_empty_folders`, keeping their path. Nothing is deleted.
- `--dry-run` previews.

**Status:** Done

#### US-11 Remove leftover copies after conversion
As a photo owner, I want the PNG left behind by a conversion removed, and empty folders set aside, so that the folder is clean.

- `Cleanup-Pictures.ps1` keeps one file per base name in each folder, preferring HEIC, then JPG, then video, then PNG. It deletes the others.
- Empty folders are moved into `_empty_folders`, keeping their path.
- `-WhatIf` previews.

**Status:** Partly done. It also deletes Live Photo videos and sidecar files that share a photo's name (BUG-01).

</details>

<details>
<summary><strong>Epic 4 — Clear out files that aren't photos</strong> (US-12 to US-14)</summary>

Move ads and broken files out of the way, and delete files that hold no picture.

#### US-12 Set ad images aside
As a photo owner, I want ad and app-cache images moved out of my photos, so that I can review and delete them in one place.

- `--quarantine-ads` moves files with an ad-style name and no camera Make/Model into `_ads`. Examples of ad-style names: a UUID, `UnityAdsCache-<hash>`, `news_images%2F…`.
- A file with camera information is never treated as an ad.
- Nothing is deleted. `--dry-run` previews.

**Status:** Done

#### US-13 Set incomplete files aside
As a photo owner, I want failed copies moved out of the way, so that they stop showing up as photos with no date.

- `--move-incomplete` moves files that are 0 bytes, all null bytes, or videos with no video header into `_incomplete`, keeping their subfolder path.
- Files in the older `_no-image-data` folder are folded into `_incomplete`.
- Nothing is deleted. `--dry-run` previews.

**Status:** Done

#### US-14 Delete leftover sidecar files
As a photo owner, I want files that hold no picture deleted, so that they don't clutter the folder.

- `--delete-junk` deletes `.AAE` iPhone edit files, `Thumbs.db`/`ehthumbs*.db`, and macOS `._` sidecars.
- A `._` file is deleted only when its contents carry the AppleDouble signature.
- Thumbnail caches are matched by whole file name only, so `west sucking thumb.jpg` is safe.
- This is a real delete. `--dry-run` previews, and Claude asks before running it.

**Status:** Done

</details>

<details>
<summary><strong>Epic 5 — Check and report, without changing anything</strong> (US-15 to US-18)</summary>

Reports that show duplicates, misfiled files and anything left over.

#### US-15 Find duplicate photos and videos
As a photo owner, I want to know which files are copies of each other, so that I can free up space.

- `find_duplicates.py --root <folder>` searches at every depth.
- Byte-for-byte copies are reported as `IDENTICAL`.
- Likely copies (re-saved, resized or re-tagged) are reported as `DUPLICATE` or `POSSIBLE`. These are found among files that share a Date Taken, a name or a size.
- Videos are compared by four frames and their length, which needs ffmpeg.
- Nothing is moved, renamed or deleted.

**Status:** Done

#### US-16 Check whether a skipped collision is a real copy
As a photo owner, I want to know whether a file skipped as a `COLLISION` is the same as the file in its way, so that I know which one to delete.

- `--compare-collisions` lists each pair as `IDENTICAL` or `DIFFERENT`. It also covers files `--flatten` renamed or left behind.
- `--visual-compare --dry-run` compares pixels, or four frames for video. It reports `DUPLICATE`, `DIFFERENT` or `UNSURE` with a confidence level, which goes into its own column in the audit workbook.
- Both run entirely on the computer and change nothing.

**Status:** Done

#### US-17 Find photos filed with videos
As a photo owner, I want to see photos sitting in my video folders and videos in my photo folders, so that I can refile them.

- `/report-opposite-type D:\Videos` gives a count for each year folder and lists the files.
- Nothing is changed.

**Status:** Done

#### US-18 See what is left after organizing
As a photo owner, I want one report of everything still needing attention, so that I know when a year is finished.

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

Run the steps together, preview them, never lose a file by surprise, and keep a history.

#### US-19 Run every step in one command
As a photo owner, I want one command that runs the routine steps in the right order, so that I don't have to remember it.

- `--all` runs, in order: delete junk, move incomplete files, fill blanks, convert PNG, apply moves, sync timestamps.
- `--quarantine-ads` and `--flatten` can be added to it.
- It ends with one summary of every step's counts and up to 50 problems per step.

**Status:** Partly done. `--all --dry-run` is refused, so the combined run cannot be previewed.

#### US-20 Match Explorer's dates to Date Taken
As a photo owner, I want Date Created and Date Modified to match when the picture was taken, so that every Explorer column agrees.

- `--sync-timestamps` sets Date Created to Date Taken on every dated file, at any depth.
- Date Modified is set too, but only on files that look unedited. A file looks edited when EXIF `DateTime` differs from `DateTimeOriginal` by a minute or more, or when `Software` names a known editor (Photoshop, Lightroom, Snapseed and others). An edited file keeps its Date Modified.
- Date Created is set through the Win32 API. On other systems only Date Modified is synced.

**Status:** Partly done. One unreadable file stops the whole step (BUG-02). There is no `--dry-run` preview.

#### US-21 Never delete without saying so
As a photo owner, I want files moved aside rather than deleted, except in steps that say they delete, so that mistakes can be undone.

- `_ads`, `_incomplete` and `_empty_folders` hold what was set aside. Every step skips them.
- Only `--delete-junk` and `Cleanup-Pictures.ps1` delete files.

**Status:** Partly done. `Cleanup-Pictures.ps1` deletes more than leftover copies (BUG-01).

#### US-22 Preview before anything changes
As a photo owner, I want to see what a step will do before it does it, so that I never lose a photo by surprise.

- `--dry-run` works with fill blanks, flatten, quarantine ads, move incomplete, delete junk, visual compare and final check. `-WhatIf` works with both PowerShell scripts.
- Claude previews each changing step and asks before going ahead.

**Status:** Partly done. These have no dry run:
- `--convert-png`
- `--apply-moves`
- `--sync-timestamps`
- `--all`

`--dry-run` also renames an old-style audit workbook (BUG-05).

#### US-23 Keep a history of everything done to a folder
As a photo owner, I want a record of every step run on a folder, so that I can see later what changed and when.

- The workbook is named `<folder>_<photos|videos>_media_audit_<date>.xlsx`, in the media folder. Runs on the same day share it.
- Every step appends to the Run log and Run counts sheets. That includes dry runs and both PowerShell scripts.
- If the workbook is open in Excel, the step runs but is not recorded.

**Status:** Partly done. A step that stops on an error records nothing, and in `--all` neither do the steps that finished before it (BUG-02).

</details>

<details>
<summary><strong>Epic 7 — Maintain the plugin</strong> (US-24 to US-25)</summary>

Change and test the plugin safely.

#### US-24 Test without real photos
As a maintainer, I want tests that run on generated files, so that I can check a change without risking my own photos.

- `py -m unittest discover tests -v` runs the suite. It currently has 21 tests.
- `sample-data/generate.py` makes synthetic test photos.
- Video tests are skipped when ffmpeg is missing. The video date-writing test is skipped when ExifTool is missing. The Date Created test runs only on Windows.

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
<summary><strong>Open bugs</strong> (5, all found by Claude on 2026-10-21)</summary>

Each was reproduced on synthetic files, except where noted.

#### BUG-01 Cleanup deletes Live Photo videos and sidecar files
**Severity:** High (permanent data loss) · **Found by:** Claude · **Where:** [Cleanup-Pictures.ps1](../skills/media-date-organizer/scripts/Cleanup-Pictures.ps1), pass 1

The script treats any two files with the same base name in a folder as duplicates, whatever their type and content, and deletes all but one.

**Steps to reproduce**
1. In a folder, put `IMG_1234.HEIC` and `IMG_1234.MOV` (an iPhone Live Photo pair), and `IMG_5555.JPG` and `IMG_5555.xmp`.
2. Run `Cleanup-Pictures.ps1 -Path <folder> -WhatIf`.

**Expected:** Nothing is dropped. The video is a separate recording, and the `.xmp` file holds edits.
**Actual:** `KEEP: IMG_1234.HEIC  DROP: IMG_1234.MOV` and `KEEP: IMG_5555.JPG  DROP: IMG_5555.xmp`. Without `-WhatIf`, both are deleted for good.

**Also affected**
- Any file with an extension not on the preference list ranks last and is deleted.
- The pass also runs inside `_ads`, `_incomplete` and `_empty_folders`.

**Suggested fix:** Only treat files as copies when they are a photo and a photo (never a photo and a video), and only for the conversion case: a PNG next to a JPG of the same name. Never delete a file whose extension is not a known media type.

#### BUG-02 One unreadable file stops a step, and nothing is recorded
**Severity:** Medium · **Found by:** Claude · **Where:** [organize.py](../skills/media-date-organizer/scripts/organize.py) `sync_timestamps`, `scan`

`fill_blanks` catches read errors per file, but `sync_timestamps` and `scan` do not. `scan` is used by `--report-only`, `--apply-moves`, `--compare-collisions` and `--visual-compare`.

**Steps to reproduce**
1. Make a file that cannot be read during the step. The repro simulated this with a `PermissionError`; in real use it could be a file locked by another program, or an HEIC or video large enough to cause a `MemoryError`, since both are read whole when no header is found.
2. Run `--sync-timestamps`.

**Expected:** That file is reported as failed and the rest are synced.
**Actual:** The step stops with a traceback, and no audit workbook is written. Under `--all`, the record of the steps that had already finished is lost too, because the workbook is written once at the end.

#### BUG-03 Report and `--apply-moves` only look one folder deep
**Severity:** Medium · **Found by:** Claude · **Where:** `iter_media` in [organize.py](../skills/media-date-organizer/scripts/organize.py)

`scan` looks only at files exactly one folder below the root. `--fill-blanks`, `--sync-timestamps`, `--flatten` and `--convert-png` work at any depth.

**Steps to reproduce**
1. Create `root\loose.jpg`, `root\2019-08-30\wrong.jpg` and `root\Trip\2019-08-30\deep.jpg`, each with a Date Taken.
2. Run `--report-only`.

**Expected:** All three files are in the report.
**Actual:** Only `wrong.jpg` is reported.

**Impact:** After `--flatten`, every file is loose in the root, so a later `--report-only` reports none of them.

#### BUG-04 Unrecognised ISO media files are read as MP4 video
**Severity:** Low · **Found by:** Claude · **Where:** `detect_type` in [organize.py](../skills/media-date-organizer/scripts/organize.py)

Any file with an `ftyp` header whose brand is not in the known list is reported as `.mp4`. Two examples:
- a `.heic` with the `hevc` brand (a HEIF image sequence);
- an AVIF file.

A HEIF file read as video has no video date. `--fill-blanks` would then try to write video date tags into it with ExifTool.

**Steps to reproduce:** `detect_type` on a file starting `....ftyphevc` or `....ftypavif` returns `.mp4`.
**Expected:** HEIF brands (`hevc`, `heim`, `heis`, `hevx`) return `.heic`. Unknown brands return `None`.

#### BUG-05 `--dry-run` renames an audit workbook
**Severity:** Low · **Found by:** Claude · **Where:** `_default_xlsx` in [organize.py](../skills/media-date-organizer/scripts/organize.py)

Working out today's workbook name renames an old-style `media_audit_<date>.xlsx` to `<folder>_<type>_media_audit_<date>.xlsx`. This happens on every run, previews included.

**Steps to reproduce:** Put today's `media_audit_<date>.xlsx` in a folder and run `--flatten --dry-run`.
**Expected:** Nothing in the folder changes.
**Actual:** The workbook is renamed to `2014_photos_media_audit_<date>.xlsx`.

</details>

<details>
<summary><strong>Resolved bugs</strong> (19: 6 found by Michele Kummer, 13 by Claude)</summary>

The list is oldest first. **Fixed in** gives the commit. Bugs fixed before the history begins point to [case-study.md](case-study.md) instead.

| ID | Bug | Severity | Found by | Fixed in |
|---|---|---|---|---|
| BUG-06 | Wrong extensions hid real dates | High | Claude | case study |
| BUG-07 | PNG Date Taken hidden in Explorer | Medium | Claude | case study |
| BUG-08 | Command line and docs disagreed | Medium | Michele Kummer | `c742389`, `3b99ebb`, `89f2044` |
| BUG-09 | Filling a date re-encoded JPEGs | Medium | Claude | `b58aef6` |
| BUG-10 | Filename dates ignored | Medium | Michele Kummer | `b58aef6` |
| BUG-11 | Case-only renames reported as collisions | Low | Claude | `48dde7a` |
| BUG-12 | Video dates in the wrong time zone, whole video read | Medium | Claude | `0c3f7e3` |
| BUG-13 | One unreadable file stopped fill and convert | Medium | Claude | `0c3f7e3`, `8d47bde` |
| BUG-14 | Cleanup `-WhatIf` looped forever | Medium | Claude | `df37cf1` |
| BUG-15 | Older video formats reported as UNKNOWN | Low | Michele Kummer | `df37cf1`, `8d47bde` |
| BUG-16 | Image files left open | Low | Claude | `e82fc06` |
| BUG-17 | `--apply-moves` renamed files | Medium | Claude | `8d47bde` |
| BUG-18 | Edited files skipped by timestamp sync | Low | Claude | `8d47bde` |
| BUG-19 | Fill and sync only looked one level deep | Medium | Michele Kummer | `9f23c22` |
| BUG-20 | Plugin could not be installed | High | Michele Kummer | `9f23c22` |
| BUG-21 | Folder dates read only from exact `YYYY-MM-DD` names | Medium | Michele Kummer | `89f2044` |
| BUG-22 | Install commands disagreed about package versions | Low | Claude | 2026-10-21 (uncommitted) |
| BUG-23 | Minimum Python version stated but never checked | Low | Claude | 2026-10-21 (uncommitted) |
| BUG-24 | PowerShell scripts skipped the audit log without `python` on PATH | Low | Claude | 2026-10-21 (uncommitted) |

#### BUG-06 Wrong extensions hid real dates
**Found by:** Claude · **Fixed:** before the first commit ([case-study.md](case-study.md))

On the first real run, 14 of 35 files seemed to have no Date Taken. Writing EXIF to the first one failed, which showed the file was not what its extension said. Of 13 `.PNG` files, 8 were HEIC and 3 were QuickTime video, and 2 `.HEIC` files were PNG.
**Fix:** Correcting extensions from the file's first bytes became the first phase (`Fix-Extensions.ps1`). With each file read by the right reader, all 35 had a date.

#### BUG-07 PNG Date Taken hidden in Explorer
**Found by:** Claude · **Fixed:** before the first commit ([case-study.md](case-study.md))

Four PNGs showed a blank Date Taken in Windows Explorer although the EXIF date was in the file. Explorer never shows Date Taken for PNG.
**Fix:** `--convert-png` converts PNG to JPEG at quality 95, keeping the EXIF.

#### BUG-08 Command line and docs disagreed
**Found by:** Michele Kummer · **Fixed in:** `c742389`, `3b99ebb`, `89f2044`

The docs described `--apply-moves`, `--fill-blanks` and `--sync-timestamps`, but the script had `--apply` and neither of the other two. Later, help text still said "ad images" for a step that also moves videos, and the `--sync-timestamps` help contained a stray `$root`.
**Fix:** The script was rewritten to match the docs, and the help text was corrected.

#### BUG-09 Filling a date re-encoded JPEGs
**Found by:** Claude · **Fixed in:** `b58aef6`

Every JPEG given a date was re-saved at Pillow's default quality, losing picture quality.
**Fix:** The EXIF block is now swapped in place, and the image data is left untouched.

#### BUG-10 Filename dates ignored
**Found by:** Michele Kummer · **Fixed in:** `b58aef6`

Photos without an EXIF date, such as Snapchat exports, were given their folder's date even when the filename held the real one (`IMG_20231220_142355.jpg`). Files in folders without a date in their name got no date at all.
**Fix:** The filename date is used first, then the folder date. The file's modified time is never used.

#### BUG-11 Case-only renames reported as collisions
**Found by:** Claude · **Fixed in:** `48dde7a`

A move that only changed letter case (`img.JPG` → `img.jpg`) was reported as a collision on Windows, where names are not case-sensitive.
**Fix:** Case-only renames are no longer treated as collisions.

#### BUG-12 Video dates in the wrong time zone, whole video read
**Found by:** Claude · **Fixed in:** `0c3f7e3`

Video dates are stored in UTC but were treated as local time, so they were off by the time-zone difference. Finding the date also read the whole video into memory.
**Fix:** Dates are converted between UTC and local time when read and written. Only the header atoms are read.

#### BUG-13 One unreadable file stopped fill and convert
**Found by:** Claude · **Fixed in:** `0c3f7e3`, `8d47bde`

A single unreadable file stopped `--fill-blanks`. A `.png` that wasn't a picture stopped `--convert-png` and could leave a half-written JPEG behind.
**Fix:** The file is reported and counted as `read-failed`, the rest are processed, and a half-written JPEG is removed. (BUG-02 is the same problem in other steps.)

#### BUG-14 Cleanup `-WhatIf` looped forever
**Found by:** Claude · **Fixed in:** `df37cf1`

`Cleanup-Pictures.ps1 -WhatIf` never finished on a folder with an empty subfolder, because the preview never removed the folder it kept finding.
**Fix:** The empty-folder pass was rewritten. Since `89f2044` it moves empty folders into `_empty_folders` instead of removing them.

#### BUG-15 Older video formats reported as UNKNOWN
**Found by:** Michele Kummer · **Fixed in:** `df37cf1`, `8d47bde`

`Fix-Extensions.ps1` reported camcorder (`.m2ts`, `.mts`), MPEG, Windows Media and AVI videos as `UNKNOWN`, and Sony `.modd`/`.moff` sidecars as unknown files.
**Fix:** All are recognised and left with their own extension. `--flatten` moves them by the date in the filename.

#### BUG-16 Image files left open
**Found by:** Claude · **Fixed in:** `e82fc06`

Image files stayed open after reading metadata, converting PNGs and comparing photos, which can stop Windows from moving or deleting them.
**Fix:** Every image is closed after use.

#### BUG-17 `--apply-moves` renamed files
**Found by:** Claude · **Fixed in:** `8d47bde`

Besides moving files, `--apply-moves` changed their extension to the detected type in capitals and stripped `_YYYY-MM-DD` endings that carried a file's only date. `--convert-png` also named files `.JPG` instead of `.jpg`.
**Fix:** `--apply-moves` no longer changes extensions or strips date endings. Only `Fix-Extensions.ps1` changes extensions.

#### BUG-18 Edited files skipped by timestamp sync
**Found by:** Claude · **Fixed in:** `8d47bde`

`--sync-timestamps` skipped edited files entirely, so their Date Created still showed the import date.
**Fix:** Edited files get Date Created set, and keep their Date Modified.

#### BUG-19 Fill and sync only looked one level deep
**Found by:** Michele Kummer · **Fixed in:** `9f23c22`

`--fill-blanks` and `--sync-timestamps` only checked photos exactly one folder below the root, so nested folders were missed. (BUG-03 is the same limit in `--report-only` and `--apply-moves`.)
**Fix:** Both now look at every depth.

#### BUG-20 Plugin could not be installed
**Found by:** Michele Kummer · **Fixed in:** `9f23c22`

The plugin manifest failed validation because its skill and command paths lacked a leading `./`, and the README's `/plugin install .` instructions did not work.
**Fix:** The paths were corrected, a marketplace file was added, and the README gives the marketplace install command.

#### BUG-21 Folder dates read only from exact `YYYY-MM-DD` names
**Found by:** Michele Kummer · **Fixed in:** `89f2044`

Folders named `2026-08-19 11-44-31`, `2019_08_30`, `30-08-2019` or `Aug 19 2026` were not recognised as dated, so files in them got no fallback date and were not moved.
**Fix:** All of these forms are read. A year-only name is still not a date.

#### BUG-22 Install commands disagreed about package versions
**Found by:** Claude · **Fixed:** 2026-10-21 (not yet committed)

The two `SKILL.md` files, `commands/fix-media-dates.md` and the scripts' error messages said `pip install pillow openpyxl` with no versions. The README and `requirements.txt` require `pillow>=10.0` and `openpyxl>=3.1`.
**Fix:** Every install hint now gives the minimum version, including `imageio-ffmpeg>=0.5`.

#### BUG-23 Minimum Python version stated but never checked
**Found by:** Claude · **Fixed:** 2026-10-21 (not yet committed)

The README said Python 3.9+, but nothing enforced it, and the skill docs did not mention it.
**Fix:** `organize.py` (and through it `find_duplicates.py`) stops with a clear message on Python older than 3.9. The skill docs and `/fix-media-dates` state the requirement.

#### BUG-24 PowerShell scripts skipped the audit log without `python` on PATH
**Found by:** Claude · **Fixed:** 2026-10-21 (not yet committed)

`Write-AuditLog.ps1` looked only for `python`. A python.org install often provides only the `py` launcher, which is also what the cheatsheet uses. Where Python was missing, the Microsoft Store `python` stub could be picked instead.
**Fix:** It tries a real `python` first, then `py -3`, and ignores the WindowsApps stub.

</details>
