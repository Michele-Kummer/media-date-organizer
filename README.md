# photo-date-fixer

A Claude Code plugin that ensures every photo in a folder has a readable **Date Taken** — reading the real EXIF (even when the extension lies), converting formats that Windows can't surface Date Taken for (notably PNG) to JPEG with EXIF preserved, writing metadata where it's missing, and sorting files into folders matching their real date.

Works on any photo source. The author built it from a cleanup on a mixed folder of HEIC images, Live Photo MOV clips, and PNG screenshots exported to Windows, but nothing in the pipeline is tied to a specific camera or phone.

---

## What it does

1. **Fixes wrong file extensions.** Reads the first 16 bytes of each file and renames anything whose extension doesn't match its real format (PNG, JPEG, HEIC/HEIF, MOV/MP4/M4V, GIF, BMP, TIFF, WEBP).
2. **Reads the true Date Taken.** HEIC embedded TIFF/EXIF, MOV/MP4 `mvhd` creation time, JPEG/PNG standard EXIF — all parsed without external tools like `exiftool` (which is only needed, optionally, to write dates into HEIC and video files).
3. **Writes Date Taken where it's missing.** Falls back to the containing folder's date (if the folder is named `YYYY-MM-DD`) and stamps `DateTimeOriginal` into the EXIF.
4. **Converts PNG to JPEG when needed.** Windows Explorer only shows Date Taken for JPEG/HEIC/TIFF/raw; PNG dates stay invisible there. The plugin re-encodes PNG → JPEG at quality 95, preserving EXIF, so Explorer surfaces the date. PNGs with transparency are left as PNG.
5. **Moves files to date-matched folders.** Files whose Date Taken doesn't match their current folder's name are moved to a sibling folder named for their real date.
6. **Produces an audit workbook** and finishes with a PowerShell cleanup script that removes duplicates and empty folders.
7. **Flattens the result, if you want.** An optional last step moves every dated photo up out of its `YYYY-MM-DD` subfolder into the photo folder itself and deletes the emptied subfolders. Runs on its own with `/flatten-photos <folder>`.
8. **Quarantines ad images, if you want.** `organize.py --quarantine-ads` moves images that have an ad-style name (a UUID, `bed51b94a_1595`, `gmsnet2`) and no camera Make/Model into an `_ads` folder for you to review and delete. Preview with `--dry-run` first.
9. **Sets aside files with no image data, if you want.** `organize.py --move-no-data` moves media files that are 0 bytes or all null bytes (a failed copy or transfer) into a `_no-image-data` folder, keeping their subfolder path. Nothing is deleted. Preview with `--dry-run` first.

Several steps can run in one command: `organize.py --root <folder> --all` runs steps 3–5 plus the timestamp sync, and prints one summary of every step's counts and problems at the end. Add `--move-no-data`, `--quarantine-ads` or `--flatten` to include those.

End state: every photo has a Date Taken, is in a folder matching that date, has a correct file extension, and shows up correctly in Windows Explorer.

## Install

Requires [Claude Code](https://docs.anthropic.com/claude/docs/claude-code), Python 3.9+, and Windows PowerShell 5.1+ (or PowerShell 7).

```bash
git clone https://github.com/Michele-Kummer/photo-date-fixer.git
cd photo-date-fixer
pip install -r requirements.txt     # Pillow + openpyxl
# Then in Claude Code:
/plugin install .
```

Or install directly from a URL: `/plugin install https://github.com/Michele-Kummer/photo-date-fixer`.

## Use

In Claude Code, describe the task:

```
Fix the dates on my photos in D:\Pictures\2026
```

Or invoke the slash command explicitly:

```
/fix-photo-dates D:\Pictures\2026
```

Claude walks through: extension fix → metadata read → date-write for blanks → PNG→JPG conversion (with confirmation) → moves → cleanup reminder. An audit XLSX is written alongside your photos.

## Project layout

```
.
├── .claude-plugin/plugin.json         Plugin manifest
├── skills/photo-date-fixer/           The skill
├── commands/                          Slash commands (fix-photo-dates, flatten-photos)
├── docs/                              Case study, screenshots, example audit
└── sample-data/                       Synthetic test photos
```

## Case study

See [docs/case-study.md](docs/case-study.md) for how the ruleset evolved — including the moment a "blank Date Taken" finding turned out to be a wrong-extension problem instead, and why "ensuring Date Taken" is as much about file formats and Windows Shell behavior as about metadata.

## License

MIT — see [LICENSE](LICENSE).
