---
description: Move every dated photo up out of its subfolder into the photo folder itself, then delete the subfolders left empty.
argument-hint: <path-to-photo-folder>
---

# /flatten-photos

Move the dated photos in `$ARGUMENTS` up one level, out of their subfolders, and remove the folders that end up empty.

## Steps

1. **Preview.** Run `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --flatten --dry-run`. Nothing is changed. Share the counts and any `LEFT`, `COLLISION` or renamed lines with the user.

2. **Flatten.** After the user confirms: `python skills/photo-date-fixer/scripts/organize.py --root "$ARGUMENTS" --flatten`.

## What it does

- Every file one level down that has a Date Taken moves into `$ARGUMENTS` itself.
- Files with no Date Taken stay where they are, so their folders are kept. Run `/fix-photo-dates` first if the user wants those dated and moved too.
- Exception: inside `$ARGUMENTS/_ads`, every file moves up from its subfolder into `_ads` itself, with or without a Date Taken. A name already taken there gets a `_<subfolder-name>` suffix.
- Camcorder videos (`.m2ts`, `.mts`) move up as well, going by the date in the filename. Ones with no date in the name, or holding no data, stay.
- Sony `.modd`/`.moff` sidecar files move with the file they belong to. A sidecar whose file is not beside it is permanently deleted; the dry run lists these as `WOULD DELETE (sidecar with no file)`, so share that list before running for real.
- A name already taken in the root gets a `_<date-taken>` suffix; if that is taken as well, the file is skipped and reported.
- Subfolders left empty are deleted. Folders still holding anything are kept.

## Deliverables

- The run (and the dry run) is recorded in the Run log and Run counts sheets of `media_audit_<date>.xlsx` at the root of `$ARGUMENTS`.
- Summary message with counts (moved, ads moved, sidecars moved, orphan sidecars deleted, renamed, left undated, folders removed, folders kept).
