---
description: Show everything the media-date-organizer plugin can do, with an example of what to type for each. Changes nothing.
argument-hint: (nothing needed)
---

# /media-help

Show the user the list below as it is, then ask which one they want to do and for which folder. Do not run anything.

## What you can do

**Fix dates and tidy a folder**

| I want to… | Type |
|---|---|
| Step by step: see what each step would change, and choose the optional ones, cleanup included (changes nothing) | `/fix-media-dates D:\Pictures\2026` |
| Then make the changes you chose | `/fix-media-dates D:\Pictures\2026 --apply` |
| All in one go: see what the routine steps would change, with no questions (changes nothing; add `--quarantine-ads` or `--flatten` to include those) | `/fix-media-dates D:\Pictures\2026 --all` |
| Then make all of those changes | `/fix-media-dates D:\Pictures\2026 --all --apply` |
| See what moving everything up out of its subfolders would do (changes nothing) | `/flatten-media D:\Pictures\2026` |
| Then move them | `/flatten-media D:\Pictures\2026 --apply` |

**Check, without changing anything**

| I want to… | Type |
|---|---|
| Find photos or videos that are copies of each other | `Find duplicates in D:\Pictures\2012` |
| See photos filed among videos, or videos among photos | `/report-opposite-type D:\Videos` |
| Find plist or XMP files saved with a photo name | `Check D:\Pictures\2023 for plist files` |
| See what is left over after organizing | `Run the final check on D:\Videos` |

**Single steps** (ask in plain words)

| I want to… | Type |
|---|---|
| Fill in only the missing dates | `Fill in the missing dates in D:\Pictures\2026` |
| Convert PNG screenshots to JPEG so Explorer shows their date | `Convert the PNGs in D:\Pictures\2026 to JPEG` |
| Convert BMP pictures to dated JPEGs | `Convert the BMPs in D:\Pictures\2026 to JPEG` |
| Fix extensions that don't match the file | `Fix the extensions in D:\Pictures\2026` |
| Set aside ad and app junk images | `Quarantine the ads in D:\Pictures\2026` |
| Set aside AAE, Thumbs.db and Mac `._` files | `Move the junk files in D:\Pictures\2026` |
| Set aside broken or empty files | `Move the incomplete files in D:\Pictures\2026` |
| Make Date Created and Date Modified match Date Taken | `Sync the timestamps in D:\Pictures\2026` |
| Clean up converted files (deletes PNGs and BMPs already turned into JPEGs) | `Clean up the converted files in D:\Pictures\2026` |

## Good to know

- Lines starting with `/` are typed in the Claude chat, not in PowerShell.
- `/fix-media-dates` and `/flatten-media` only show what they would do. Nothing changes until you type the same command again with `--apply` on the end.
- The plain-language steps are previewed first too, and Claude asks before going ahead.
- `/fix-media-dates` on its own goes step by step and asks which optional steps you want. With `--all` it runs the routine steps in one go without asking, and leaves out ads, flatten, BMP conversion and cleanup unless you ask for them.
- Ads, junk, incomplete files and empty folders are moved into `_ads`, `_junk`, `_incomplete` and `_empty_folders`, not deleted. The only step that deletes is cleaning up converted files, and Claude asks first.
- Each folder gets an audit spreadsheet (`.xlsx`) recording everything that was done.
- First time? Try it on a small folder, or a copy of one.
