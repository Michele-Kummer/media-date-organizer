# Sample data

A synthetic folder of photos and videos that shows each problem media-date-organizer fixes, and a copy with the tool run on it, so you can compare them side by side. No real photos are used.

## Make it

From the repository root:

```
py sample-data/generate.py
```

This writes into `sample-data/Sample_Pictures` (ignored by git):

| What | What it is |
|---|---|
| `Before` | The samples as they start out. |
| `After` | A copy of `Before` with `organize.py --all --quarantine-ads --apply-moves --flatten --apply` run on each year folder, as you would on `E:\Pictures\2024`. |
| `Comparison.md` | Every file in each folder, with its real format and Date Taken. |
| `After_log.txt` | What the tool printed while making `After`. |

`--before-only` writes only `Before`, so you can run the plugin on it yourself. `--out <folder>` writes somewhere else. Running it again moves the old `Before` and `After` into `_previous`, as `Before_<date>_<time>` and `After_<date>_<time>`, rather than deleting them. Output from an older version, in `Sample Pictures`, is moved into `Sample_Pictures` the same way.

Videos need ffmpeg (`pip install "imageio-ffmpeg>=0.5"`) and are left out without it. Writing a video's date in `After` needs ExifTool.

## What's in it

`Before` holds year folders with day folders inside, like a real library. In `After`, each year's good photos and videos are flattened into the year folder itself, and what isn't a real photo is set aside in that year's own `_ads`, `_junk`, `_thumbnails` and `_incomplete`. The emptied day folders go into `_empty_folders`. Each picture has its problem written on it, so you can tell them apart in Explorer.

| In Before | The problem | In After |
|---|---|---|
| `2024/2024-07-04/IMG_20240704_183012.jpg` | No Date Taken; the date is only in the name | `2024`, Date Taken 2024-07-04 18:30 |
| `2024/2024-07-04/Fireworks.png` | A PNG, so Explorer never shows its Date Taken | `2024/Fireworks.jpg`, dated |
| `2024/2024-07-04/Beach.PNG` | Really a JPEG | `2024/Beach.JPG` |
| `2024/2024-07-04/VID_20240704_201500.mp4` | No Media Created; the date is only in the name | `2024`, Media Created 2024-07-04 20:15 |
| `2024/2024-07-04/46.jpg`, `47.jpg` | A phone gallery's thumbnails | `2024/_thumbnails` |
| `2024/2024-07-04/0c4cda27-….jpg` | An app ad | `2024/_ads`, with the folder's date in its name |
| `2024/2024-01-15/IMG_0412.JPG` | Taken 2024-01-01, filed under the import date | `2024` |
| `2024/2024-01-15/IMG_0413.HEIC` | Really a JPEG, and filed under the import date | `2024/IMG_0413.JPG` |
| `2024/2024-01-15/clip.mp4` | Recorded 2024-03-10, filed under the import date | `2024` |
| `2024/2024-01-15/Screenshot_20240115-093000.png` | A PNG with the date only in its name | `2024/Screenshot_20240115-093000.jpg`, dated |
| `2024/2024-01-15/IMG_0412.AAE`, `._IMG_0412.JPG`, `Thumbs.db` | iPhone edit file, Mac sidecar, Windows thumbnail cache | `2024/_junk` |
| `2024/2024-01-15/IMG_0420.jpg` | A copy that stopped before any data was written | `2024/_incomplete` |
| `2024/2024-01-15/32#xffa2defe.png` | An app's colour swatch | `2024/_ads` |
| `2023/Aug 19 2023/Party.jpg` | No Date Taken; the date is only in the folder's name | `2023`, Date Taken 2023-08-19 |
| `2023/Aug 19 2023/Cake.jpg` | None: a good photo | `2023` |
| `2023/Aug 19 2023/scribble2mammoth_over@2x.png` | A kids' app button image | `2023/_ads` |

The misfiled photos were taken in the same year they were filed under. The tool moves a photo next to the folder it is in, so one taken in another year would stay in the year folder it was found in.

Converted PNGs are kept beside their JPEGs until you run the cleanup step, which deletes them and asks first.
