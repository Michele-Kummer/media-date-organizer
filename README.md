# media-date-organizer

**Fixes the dates on your photos and videos so they sort correctly in Windows.**

Photos copied from phones, cameras and apps often show a blank or wrong **Date Taken** in Windows Explorer. As a result, they sort by the day they were copied, not the day they were taken. media-date-organizer finds each file's real date, writes it in where it's missing, and files every photo and video in a folder named for that date. It runs as a [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) plugin, so you can ask for things in plain English. It is also a standalone Python command-line tool.

| Before | After |
|---|---|
| ![Before: a PNG with no Date Taken, a HEIC with no Date Taken, and a file whose created and modified dates are wrong](docs/screenshots/Before.jpg) | ![After: every file is a JPG in a folder named for its date, and Date created, Date modified and Date taken all match](docs/screenshots/After.png) |

## Why it's useful

Missing dates are rarely just missing. They come from a handful of everyday problems, and this tool handles each one:

- **Extensions that lie.** A file named `.PNG` may really be an iPhone HEIC photo or a Live Photo video, and then the date reader fails. On the first real folder, 13 of 35 files were misnamed this way ([case study](docs/case-study.md)). The tool reads each file's first bytes to find its true format.
- **Formats Windows won't show.** Explorer never shows Date Taken for PNG, even when the date is inside the file. The tool can convert PNGs to JPEG and keep the date.
- **Dates that only live in a name.** `IMG_20231220_142355.jpg` or a folder named `Aug 19 2026` holds the real date. The tool writes it into the file.
- **Clutter that isn't a photo at all.** App ads, half-copied files, Mac and iPhone sidecar files, and edit data saved as `.JPG`. These are set aside or reported, never silently deleted.

## What makes it different

- **Nothing changes until you say so.** Every step is a dry run by default: it lists what it *would* do and touches nothing. Add `--apply` to make the changes.
- **Nothing is lost by surprise.** Files are moved into review folders (`_ads`, `_incomplete`, `_empty_folders`) rather than deleted. The only steps that delete say so plainly.
- **A full audit trail.** Every run, previews included, is logged to an Excel workbook in the folder. You can see later what changed, when, and why.
- **Reads metadata itself.** It parses HEIC, MOV/MP4, JPEG, PNG and TIFF metadata directly, with no external tools needed just to read dates. ExifTool is only needed to write dates into HEIC and video files.
- **Plain English or command line.** In Claude Code you can type "Fill in the missing dates in D:\Pictures\2026". Every step is also a command-line flag you can script.
- **Tested on generated files.** 41 automated tests run against synthetic photos and videos, never real ones. They cover every step, the dry-run guarantee and the PowerShell scripts.

## Quick start

**You need:** Windows, Python 3.9+, and [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) 2.1.275+ to use the plugin.

1. Install the plugin. In Claude Code:

   ```
   /plugin install media-date-organizer --marketplace Michele-Kummer/media-date-organizer
   ```

2. Install the Python packages:

   ```bash
   pip install "pillow>=10.0" "openpyxl>=3.1"
   ```

3. See what it would change. This changes nothing:

   ```
   /fix-media-dates D:\Pictures\2026
   ```

4. Happy with the preview? Make the changes:

   ```
   /fix-media-dates D:\Pictures\2026 --apply
   ```

Type these in the Claude Code chat (VS Code, the desktop app, or `claude` in a terminal), not in PowerShell itself. Not sure what to type? Run **`/media-help`**. First time? Try it on a copy of a small folder.

**Without Claude Code**, the same steps run from a clone:

```bash
git clone https://github.com/Michele-Kummer/media-date-organizer.git
cd media-date-organizer
pip install -r requirements.txt
python skills/media-date-organizer/scripts/organize.py --root "D:\Pictures\2026" --all           # preview
python skills/media-date-organizer/scripts/organize.py --root "D:\Pictures\2026" --all --apply   # make the changes
```

## What you can ask for

Lines starting with `/` are slash commands. The others are plain requests: any wording works, and Claude picks the right skill. Every step that changes files is previewed first.

| I want to… | Type |
|---|---|
| See what fixing the dates would change (changes nothing) | `/fix-media-dates D:\Pictures\2026` |
| Then make those changes | `/fix-media-dates D:\Pictures\2026 --apply` |
| See what the routine steps would change, all in one go (changes nothing; add `--quarantine-ads` or `--flatten` to include those) | `/fix-media-dates D:\Pictures\2026 --all` |
| Then make all of those changes | `/fix-media-dates D:\Pictures\2026 --all --apply` |
| See what moving everything up out of its subfolders would do (changes nothing) | `/flatten-media D:\Pictures\2026` |
| Then move them | `/flatten-media D:\Pictures\2026 --apply` |
| Find photos or videos that are copies of each other | `Find duplicates in D:\Pictures\2012` |
| See photos filed among videos, or videos among photos | `/report-opposite-type D:\Videos` |
| Find plist or XMP files saved with a photo name (changes nothing) | `Check D:\Pictures\2023 for plist files` |
| See what is left over after organizing | `Run the final check on D:\Videos` |
| Fill in only the missing dates | `Fill in the missing dates in D:\Pictures\2026` |
| Convert PNG screenshots to JPEG so Explorer shows their date | `Convert the PNGs in D:\Pictures\2026 to JPEG` |
| Set aside ad and app junk images | `Quarantine the ads in D:\Pictures\2026` |
| Make Date Created and Date Modified match Date Taken | `Sync the timestamps in D:\Pictures\2026` |

## How it works

`/fix-media-dates` runs these steps in order. Each one can also run on its own.

| Step | What it does |
|---|---|
| 1. Fix extensions | Reads each file's first bytes and renames any whose extension doesn't match its real format (PNG, JPEG, HEIC, MOV/MP4, 3GP, M2TS, MPG, WMV, AVI, GIF, WEBP, TIFF, BMP). |
| 2. Scan | Reads every file's real date (HEIC and JPEG EXIF, the MOV/MP4 creation time) and writes the audit workbook. Changes nothing. |
| 3. Fill missing dates | Writes Date Taken (Media Created for video) from a date in the filename, else from the folder name. File modified time is never trusted, because copying resets it. |
| 4. Convert PNG (optional) | Re-encodes PNG as JPEG at quality 95 with its date kept, so Explorer shows it. PNGs with transparency stay PNG. |
| 5. Move | Moves each file whose date doesn't match its folder into a folder named for its real date. An existing file is never overwritten. |
| 6. Sync timestamps (optional) | Sets Date Created, and Date Modified on unedited files, to the date taken. |
| 7. Flatten (optional) | Moves everything up out of its dated subfolders into one folder per year. |
| 8. Clean up | Removes PNGs already converted to JPEG (only after checking that the pixels match) and sets empty folders aside. |

Housekeeping steps set aside ad images (`_ads`) and broken copies (`_incomplete`), and delete iPhone `.AAE`, `Thumbs.db` and macOS `._` sidecar files. Read-only reports find duplicates (byte-identical or visually the same), photos filed among videos, plist files named as photos, and anything left over at the end.

The full reference, with every flag, rule and edge case, is in the skill guide: [skills/media-date-organizer/SKILL.md](skills/media-date-organizer/SKILL.md).

## How it's built

- **Python 3.9+** (`organize.py`, about 2,400 lines) does the metadata parsing, date logic, moves and audit workbook. It uses Pillow for images and openpyxl for Excel. It reads HEIC and QuickTime metadata by walking the file's internal structure itself.
- **PowerShell** scripts detect file formats and clean up, using .NET `System.Drawing` to compare pixels.
- **Claude Code plugin:** three skills and four slash commands. These turn plain-English requests into the right steps, with a preview and a confirmation before any change.
- **Tests:** `py -m unittest discover tests -v` runs 41 tests on generated photos and videos. Video tests need ffmpeg; the ones that write video dates also need ExifTool, and they are skipped when it is missing.

```
.
├── .claude-plugin/              Plugin manifest and marketplace entry
├── commands/                    Slash commands: fix-media-dates, flatten-media, report-opposite-type, media-help
├── skills/media-date-organizer/ Main skill: organize.py and the PowerShell scripts
├── skills/final-check-report/   Skill: what is left after organizing
├── skills/find-duplicates/      Skill: identical and likely duplicate files
├── tests/                       Automated tests
├── docs/                        Case study, user stories and bugs, screenshots, example audit
└── sample-data/                 Generator for synthetic test photos
```

## Project documents

- **[User stories and bugs](docs/user-stories-and-bugs.md):** the project's requirements, written as 28 user stories in 7 epics, each with acceptance criteria and a status. Also every known bug, open and resolved, with severity, who found it and the commit that fixed it. It's a worked example of how the requirements were gathered and tracked.
- **[Case study](docs/case-study.md):** how the approach changed on the first real folder, when a "blank Date Taken" problem turned out to be files with the wrong extension.
- **[Example audit workbook](docs/example-audit.xlsx):** what the Excel audit trail looks like.
- **[Command cheatsheet](docs/project-cheatsheet.md):** every command, ready to copy.

## Working on the plugin

To try changes from a local clone without installing, start Claude Code with the plugin loaded for that session:

```bash
claude --plugin-dir .
```

To pick up a newer published version, run `/plugin marketplace update michele-kummer`. Managing plugins (`/plugin`) works only in Claude Code in a terminal, not in the VS Code extension; from PowerShell, `claude plugin list` shows what is installed.

## License

MIT. See [LICENSE](LICENSE).
