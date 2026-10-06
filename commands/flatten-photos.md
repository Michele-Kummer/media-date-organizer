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
- A name already taken in the root gets a `_<date-taken>` suffix; if that is taken as well, the file is skipped and reported.
- Subfolders left empty are deleted. Folders still holding anything are kept.

## Deliverables

- Summary message with counts (moved, renamed, left undated, folders removed, folders kept).
