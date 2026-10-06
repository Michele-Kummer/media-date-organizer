---
description: Ensure every photo in a folder has a Date Taken — fix extensions, write missing dates, convert PNG to JPEG where needed, sort by date, and clean up.
argument-hint: <path-to-photo-folder>
---

# /fix-photo-dates

Ensure every photo in `$ARGUMENTS` has a readable Date Taken.

## Steps

1. **Fix extensions.** Run `skills/photo-date-fixer/scripts/Fix-Extensions.ps1 -Path "$ARGUMENTS"`. Use `-WhatIf` first on unfamiliar folders.

2. **Scan metadata.** Run `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --report-only`. Writes `photo-audit.xlsx`. Share the summary before anything destructive.

3. **Write Date Taken where blank.** After user confirms: `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --fill-blanks`. Files whose containing folder is named `YYYY-MM-DD` get `DateTimeOriginal = <folder-date> 12:00:00` stamped into their EXIF.

4. **Convert PNG → JPEG (optional).** If the user wants Windows Explorer to show Date Taken for PNG screenshots, run `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --convert-png` after confirming. JPEG is lossy; the original PNG is left for the cleanup script.

5. **Move to date-matched folders.** `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --apply-moves`. Files whose Date Taken doesn't match the folder name are moved to a sibling folder named for their real date.

6. **Cleanup.** Remind the user: `skills/photo-date-fixer/scripts/Cleanup-Pictures.ps1 -Path "$ARGUMENTS"` removes duplicate base-name files and empty folders.

## Deliverables

- `photo-audit.xlsx` at the root of `$ARGUMENTS`.
- Summary message with counts (extensions corrected, dates written, files converted, files moved) plus the Cleanup-Pictures.ps1 reminder.
