# Sample data

A tiny synthetic set someone can test the plugin against without needing real photos from any particular source.

Three generated files, each stamped with a known EXIF `DateTimeOriginal`:

| File | Real format | Date Taken | Starts in folder |
|---|---|---|---|
| `2024-01-05/sample_a.png` | PNG | 2024-01-05 10:00:00 | 2024-01-05 (matches) |
| `2024-01-05/sample_b.heic` *(claimed)* | PNG with .heic extension | 2024-01-05 10:00:00 | 2024-01-05 (extension lies) |
| `2024-01-05/sample_c.png` *(claimed)* | JPEG with .png extension, date is Dec 2023 | 2023-12-20 14:30:00 | 2024-01-05 (mismatch + extension lies) |

Expected outcome after running the plugin:
1. `sample_b.heic` → renamed to `sample_b.png` (extension corrected).
2. `sample_c.png` → renamed to `sample_c.jpg` (extension corrected), then moved to a new sibling folder `2023-12-20/sample_c.jpg`.
3. `sample_a.png` stays in `2024-01-05/`.

Generate the samples locally with `python generate.py` — the small script in this folder writes three real image files with real EXIF so the plugin behaves as documented.
