# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

media-date-organizer makes sure every photo and video in a folder has a readable **Date Taken** (Media Created for video) so it sorts correctly in Windows Explorer. It is a Claude Code plugin (skills plus slash commands) and also a standalone Python command-line tool. It targets Windows and Python 3.9+.

## Layout

| Path | What it holds |
|---|---|
| `.claude-plugin/` | `plugin.json` (lists the skills and commands) and `marketplace.json`. A new skill or command must be added to `plugin.json`. |
| `skills/media-date-organizer/scripts/organize.py` | The core tool, about 3,500 lines. Every phase is a function here. |
| `skills/media-date-organizer/scripts/Cleanup-Pictures.ps1` | Moves PNG, BMP and WebP originals left after conversion into `_converted` and empty folders into `_empty_folders`. Takes `-Path` and `-Apply`. |
| `skills/media-date-organizer/scripts/Write-AuditLog.ps1` | Helper that records the PowerShell script's output in the audit workbook via `organize.py --audit-log`. |
| `skills/find-duplicates/scripts/find_duplicates.py` | Report-only duplicate finder. Imports `organize.py` from the sibling skill, so the two must stay side by side. |
| `skills/*/SKILL.md` | The instructions Claude reads for each skill (`media-date-organizer`, `final-check-report`, `find-duplicates`). |
| `commands/*.md` | Slash commands (`/fix-media-dates`, `/flatten-media`, `/move-thumbnails`, `/sort-pictures`, `/report-opposite-type`, `/media-help`). |
| `tests/` | `unittest` suite. Every test builds its own synthetic photos and videos in a temp folder. |
| `sample-data/generate.py` | Builds a synthetic `Before` and `After` library in `sample-data/Sample_Pictures` (git-ignored). |
| `scripts/import_github_issues.py` | One-off importer of stories and bugs into GitHub Issues (previews unless `--apply`). |
| `scripts/close_finished_epics.py` | Closes an issue's epic once all its stories and bugs are closed. Run by `.github/workflows/close-epics.yml` each time an issue closes (previews unless `--apply`). |
| `scripts/close_finished_stories.py` | Closes each user story whose **Status:** line was waiting only on issues now closed as completed, sets that line to `**Status:** Done`, and checks the story's epic. Run by the same workflow (previews unless `--apply`). |
| `docs/` | Cheat sheet, case study, screenshots, example audit, and `user-stories-and-bugs.md`. |
| `_review/` | Retired scripts kept aside (git-ignored). `Fix-Extensions.ps1` was replaced by `organize.py --fix-extensions`. |

## Commands

```powershell
py -m pip install -r requirements.txt           # pillow, openpyxl, imageio-ffmpeg (ffmpeg only for --visual-compare)
py -m unittest discover tests -v                # full suite
py -m unittest tests.test_dry_run -v            # one file
py -m unittest tests.test_smoke.SmokeTests.test_name -v   # one test (check the class name in the file)
py sample-data/generate.py                      # rebuild the sample library
claude --plugin-dir .                           # try the plugin without installing it
```

Running the tool (see [docs/project-cheatsheet.md](docs/project-cheatsheet.md) for every phase):

```powershell
py skills\media-date-organizer\scripts\organize.py --root "E:\Pictures\2026" --audit
py skills\media-date-organizer\scripts\organize.py --root "E:\Pictures\2026" --all            # preview
py skills\media-date-organizer\scripts\organize.py --root "E:\Pictures\2026" --all --apply    # make the changes
```

Video date tests need ffmpeg, and the ones that write video dates also need ExifTool on `PATH`; they are skipped otherwise. CI ([.github/workflows/tests.yml](.github/workflows/tests.yml)) runs the suite on `windows-latest` with Python 3.9 and 3.12 and installs ExifTool.

## How organize.py works

- **Phases are flags.** `main()` collects the chosen flags, orders them by `PHASE_ORDER` (whatever order they were typed in), and `_run_phase()` dispatches each to its function (`fix_extensions`, `move_junk`, `fill_blanks`, `convert_pngs`, `flatten`, ...). Each phase function takes `(root, dry_run)` and returns a `dict` of counts.
- **`--all`** runs `ALL_PHASES`: fix extensions, move junk, move incomplete, fill blanks, convert PNG, sync timestamps. Ads, thumbnails, screenshots, BMP and WebP conversion, apply moves and flatten are opt-in.
- **Report-only phases** are listed in `REPORT_PHASES` and run the same with or without `--apply`. `--final-check` is not in that list because it renames audit workbooks.
- **Output.** Each phase prints `WOULD ...` lines in a dry run, then a JSON block of counts. Multi-phase runs end with a `Summary of this run` block. `_IssueTee` captures stdout and stderr so problem lines (`FAILED`, `SKIPPED`, `COLLISION`, `NOTE`) can be repeated in the summary and logged.
- **Audit workbook.** Every run, previews included, is appended to `<folder>_<photos|videos>_media_audit_<date>.xlsx` in the root (Run log and Run counts sheets). `--audit` and `--apply-moves` also write the Summary and Plan sheets from `scan()`.
- **Metadata is parsed directly** (HEIC, MOV/MP4 `mvhd`, JPEG, PNG, TIFF) without external tools. ExifTool is only used to write dates into HEIC and video files (`_find_exiftool`).
- **Fallback dates** for `--fill-blanks` come from the filename (`_filename_date`), else the nearest dated folder (`_folder_name_date`, `_nearest_folder_date`).
- **Holding folders** (`HOLDING_DIRS`: `_ads`, `_incomplete`, `_junk`, `_thumbnails`, `_screenshots`, `_converted`, `_empty_folders`, legacy `_no-image-data`) are where files are moved instead of deleted, and phases skip them when walking the tree. A name already taken in a holding folder gets a suffix, or the file stays put and is reported as a `COLLISION`.

## Rules for changes

These come from [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) and keep the tool safe on a real photo library:

- **Preview first.** Every phase that changes files must only list what it would do unless `--apply` (or `-Apply` for the PowerShell script) is given. A new changing phase must be added to `CHANGING` in [tests/test_dry_run.py](tests/test_dry_run.py) and to `CHANGING_FLAGS` in [tests/test_commands.py](tests/test_commands.py).
- **Never delete.** Move files into a holding folder instead.
- **Add tests** on generated files for new and changed code. Never use real photos. Shared helpers (`make_image`, `run`, `names`, `date_taken`) live in [tests/test_smoke.py](tests/test_smoke.py).
- **Keep the docs in step.** A change to a phase usually touches the `organize.py` docstring and its `--help` text, [README.md](README.md), [docs/project-cheatsheet.md](docs/project-cheatsheet.md), the relevant `SKILL.md` and the slash commands. `tests/test_commands.py` checks that current docs don't mention retired flags such as `--dry-run` or `-WhatIf`.
- **Old flag names stay working** (`--report-only`, `--delete-junk`, `--move-no-data`, `--dry-run`) so older command lines keep running.
- **Writing style:** proper casing in names, headings and output text; no double spaces or stray dashes.
- **Commits:** short imperative summary ("Skip hidden folders when flattening"). Branch from `main`; pull requests say `Fixes #<issue>`.

## Tracking stories and bugs

New user stories and bugs go into [GitHub Issues](https://github.com/Michele-Kummer/media-date-organizer/issues) and the project board, using the forms in `.github/ISSUE_TEMPLATE/`. [docs/user-stories-and-bugs.md](docs/user-stories-and-bugs.md) is kept as the record of the original requirements gathering; US and BUG numbers are never reused.
