---
description: Sort the screenshots in a media folder into _screenshots and the phone and backup thumbnails into _thumbnails, once they have a Date Taken. Optional; run it after the dates are written. Previews only; add --apply to make the changes.
argument-hint: <path-to-media-folder> [--apply]
---

# /sort-pictures

Separate screenshots and thumbnails from the photos, so each group can be looked through on its own, after `/fix-media-dates` has written their dates.

## Dry run or apply

`$ARGUMENTS` is the media folder, optionally followed by `--apply`. Below, `<folder>` means that folder without `--apply`.

- **Without `--apply`, this is a dry run.** Run `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --sort-pictures`. Nothing is changed. Share the counts for each group and any `LEFT` or `COLLISION` lines with the user, then end with: to make these changes, type `/sort-pictures <folder> --apply`.
- **With `--apply`**, run `python skills/media-date-organizer/scripts/organize.py --root "<folder>" --sort-pictures --apply`.

## What it does

`--sort-pictures` runs `--move-thumbnails` and then `--move-screenshots`. Every file is looked for in `<folder>` and its subfolders at any depth.

**Screenshots** go straight into `<folder>/_screenshots`, with no subfolders. A screenshot is a PNG, JPEG or HEIC with no camera Make or Model that either:

- is named as phones and computers name screenshots: `Screenshot_20231220-142355.png` (Android, Samsung, Pixel, Xiaomi), `Screenshot (12).png` and `Screenshot 2023-12-20 142355.png` (Windows), `Screen Shot 2023-12-20 at 2.23.55 PM.png` and `Screenshot 2023-12-20 at 14.23.55.png` (Mac), `Screenshot from 2023-12-20 14-23-55.png` (Linux), names starting `screencap`, `Screen Capture` or `ScreenClip`, and a Mac's screenshot names in German, French, Spanish, Italian, Dutch, Swedish, Russian, Japanese and Chinese; or
- carries the "Screenshot" tag an iPhone or Mac writes inside the file, which is how an iPhone screenshot named `IMG_1234.PNG` is found.

A picture with camera information is a photo, whatever its name, and is left alone.

**Thumbnails** go straight into `<folder>/_thumbnails`, with no subfolders:

- phone gallery thumbnails: a JPEG named only by a number (`46.jpg`), at most 1024 pixels, with no camera info, as `/move-thumbnails` has always done;
- backup thumbnails: a JPEG or PNG at most 1024 pixels with no camera info that is named as a thumbnail (`IMG_1234_thumb.jpg`, `thumb_IMG_1234.jpg`, `IMG_1234.thumb.jpg`, `IMG_1234-thumbnail.png`, `tn_IMG_1234.jpg`) or kept in a thumbnail folder (`.thumbnails`, `Thumbnails`, `.thumbs`, `Thumbs`);
- thumbnail cache files: the `.ithmb` files in an iPhone or iPod backup's `Photo Cache` folder, and Android's `.thumbdata` files.

**For both groups:**

- Only a picture that **already has a Date Taken** is moved. One with none stays where it is and is listed as `LEFT (no Date Taken yet; run --fill-blanks first)`, because every step skips `_screenshots` and `_thumbnails`, and its folder's date would be lost. If the user sees `LEFT` lines, suggest running `/fix-media-dates <folder>` first, then this command again. Thumbnail cache files cannot be dated, so they move as they are.
- A name already taken in the folder gets a `_<subfolder-name>` suffix (`Screenshot (1)_2023-12-21.png`). If that is taken too, the file stays and is listed as a `COLLISION`.
- Nothing is deleted. Some thumbnails may be the only copy left of a photo, so tell the user to compare `_thumbnails` with their photos before deleting any.
- A screenshot PNG already converted to a JPEG moves with its JPEG. The cleanup step skips `_screenshots`, so the PNG stays beside its JPEG there. To have it moved into `_converted` instead, run the cleanup step before this command.
- It is optional and not part of `/fix-media-dates --all`. To include it in a full run, add `--sort-pictures`: `/fix-media-dates <folder> --all --sort-pictures --apply` runs it after the dates are written and before `--apply-moves` or `--flatten`.
- To sort only one group, ask in plain words ("Move the screenshots in D:\Pictures\2026 aside"), which runs `--move-screenshots` on its own, or use `/move-thumbnails` for the thumbnails.

## Deliverables

- The run (and the dry run) is recorded in the Run log and Run counts sheets of the audit workbook (`<folder name>_<photos|videos>_media_audit_<date>.xlsx`) at the root of `<folder>`.
- Summary message with counts (screenshots moved; phone thumbnails, backup thumbnails and thumbnail cache files moved; files left because they have no date yet; collisions), saying "would" for a dry run.
- After a dry run: the line `/sort-pictures <folder> --apply` for the user to type.
