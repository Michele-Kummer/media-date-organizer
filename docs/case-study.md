# Case study: ensuring Date Taken on a messy photo folder

A real example of using photo-date-fixer on a mixed folder of 35 photos and short videos. The folder was organized by import date into subfolders named `YYYY-MM-DD`, but the files inside were a mix of HEIC images, Live Photo MOV clips, and PNG screenshots — and many had the wrong extension. "Make sure every photo has a Date Taken" turned out to require working through four interlocking problems.

## The ask

> Scan the folder. For each picture, suggest setting Date Taken to the folder date if blank, and flag any file where the EXIF date doesn't match the folder date.

## First pass — the easy framing

A straightforward reader: open each file with Pillow, read `EXIF.DateTimeOriginal`, compare to the folder date. For HEIC (which Pillow can't open natively without `pillow-heif`, and the sandbox had no network to install it), scan the raw bytes for the TIFF magic markers `II*\x00` or `MM\x00*` and walk the IFD by hand.

The initial counts came back: 8 files matched their folder, 13 had EXIF dates on a different day, 14 came back "blank Date Taken." A clean story — write folder-date into the 14 blanks, flag the 13 mismatches for the user to review.

## The moment the framing broke

Writing EXIF to the first "blank" PNG failed with `cannot identify image file`. That's Pillow's way of saying the bytes aren't the format the extension claims. The first 16 bytes of the file:

```
00000000: 0000 0024 6674 7970 6865 6963  ...$ftypheic
```

The `.PNG` was really a HEIC. Running a magic-byte check across every file revealed the full picture:

| Claimed extension | Count | Real content |
|---|---|---|
| `.PNG` | 13 | 2 real PNG, 8 HEIC, 3 QuickTime/MOV |
| `.HEIC` | 22 | 20 real HEIC, 2 real PNG |

The `ftypqt` brand on three "PNG" files identified them as Live Photo video companions.

## Rebuilding the pipeline

**Phase 1 moved to the top: fix extensions.** Rename every file so its extension matches its real format, detected from magic bytes. Only then does any metadata reader get called.

**The "blank Date Taken" group vanished.** Once each file's real format was known, the appropriate reader found a date in every one:

- HEIC → embedded TIFF/EXIF `DateTimeOriginal`
- MOV → `mvhd` atom `creation_time` (QuickTime epoch, 1904-01-01)
- PNG → standard Pillow EXIF

Zero files had truly blank Date Taken. The "write folder-date into blanks" code path stayed in the plugin for the general case but didn't fire on this folder.

## The Windows "Date Taken" surprise

After everything was correct in metadata, four PNG files still showed blank Date Taken in Windows Explorer. Not because the EXIF was missing — `DateTimeOriginal` was right there in each file's eXIf chunk — but because **the Windows Shell PNG property handler doesn't surface Date Taken for PNG files, period**. It reads Date Taken from JPEG, HEIC, TIFF, and raw formats, but PNG goes to blank regardless of what's inside.

Two fixes considered:
1. Set file-system timestamps to match the EXIF date. Sorts correctly, wrong column.
2. Convert PNG → JPEG preserving EXIF. Populates Date Taken, slight lossy re-encode.

The user picked option 2 for the four screenshots. The plugin's PNG-to-JPEG converter re-encodes at quality 95, copies the EXIF bytes through, and leaves the original PNG for the cleanup script to remove.

## Final move: sort by real date

Many of the import-date folders held files whose real Date Taken was in October or November of the previous year. The last phase of the plugin moves those files to sibling folders named for their actual date. The user sees a clean date-sorted tree afterward.

## Takeaways

1. **Never trust an extension.** Especially on files that arrived through share sheets, email, or anywhere other than a direct camera-roll export.
2. **"Blank EXIF" is often "wrong parser."** Pick the parser from the magic bytes, not the extension.
3. **Date Taken in Windows Explorer is a Shell UI concept, not a file concept.** The data can be present and unreadable to the UI simultaneously; PNG is the common offender.
4. **Sandboxes can't delete everything.** The automation does what it can; a user-run PowerShell cleanup step closes the gap.
5. **Capture the ruleset in a skill.** Four iterations of this pipeline existed before the shape in this repo. The SKILL.md is where that distilled ruleset lives so the next run starts from the right place.

## Numbers from this run

- Folders scanned: 13
- Files processed: 35
- Extensions corrected: 16
- Files whose Date Taken already existed in real metadata: 35 (100%, once formats were right)
- PNGs converted to JPEG so Windows Explorer shows the date: 4
- Files moved to date-matched sibling folders: 27
- Empty folders removed afterward: 10

The audit workbook from the run is in `docs/example-audit.xlsx`.
