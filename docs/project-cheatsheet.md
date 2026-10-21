How to run all phases

Every step only previews what it would do. The commands below have --apply (-Apply for the .ps1 scripts) so they make the changes; leave it off to preview first.
cd C:\Code\media-date-organizer
$root = "D:\Pictures\20"
.\skills\media-date-organizer\scripts\Fix-Extensions.ps1 -Path $root -Apply

py skills\media-date-organizer\scripts\organize.py --root $root --quarantine-ads --apply
py skills\media-date-organizer\scripts\organize.py --root $root --move-incomplete --apply
py skills\media-date-organizer\scripts\organize.py --root $root --delete-junk --apply

py skills\media-date-organizer\scripts\organize.py --root $root --fill-blanks --apply
py skills\media-date-organizer\scripts\organize.py --root $root --convert-png --apply
py skills\media-date-organizer\scripts\organize.py --root $root --apply-moves --apply
py skills\media-date-organizer\scripts\organize.py --root $root --sync-timestamps --apply
py skills\media-date-organizer\scripts\organize.py --root $root --flatten --apply
.\skills\media-date-organizer\scripts\Cleanup-Pictures.ps1 -Path $root -Apply
py -m unittest discover tests -v

py skills\media-date-organizer\scripts\organize.py --root $root --report-only
py skills\media-date-organizer\scripts\organize.py --root $root --flatten
py -m unittest discover tests -v


$root = "D:\Videos\20"
.\skills\media-date-organizer\scripts\Fix-Extensions.ps1 -Path $root -Apply
py skills\media-date-organizer\scripts\organize.py --root $root --quarantine-ads --apply
py skills\media-date-organizer\scripts\organize.py --root $root --move-incomplete --apply
py skills\media-date-organizer\scripts\organize.py --root $root --delete-junk --apply

py skills\media-date-organizer\scripts\organize.py --root $root --fill-blanks --apply
py skills\media-date-organizer\scripts\organize.py --root $root --convert-png --apply
py skills\media-date-organizer\scripts\organize.py --root $root --apply-moves --apply
py skills\media-date-organizer\scripts\organize.py --root $root --sync-timestamps --apply
py skills\media-date-organizer\scripts\organize.py --root $root --visual-compare
py skills\media-date-organizer\scripts\organize.py --root $root --flatten --apply
.\skills\media-date-organizer\scripts\Cleanup-Pictures.ps1 -Path $root -Apply
py -m unittest discover tests -v


py skills\media-date-organizer\scripts\organize.py --root "D:\Videos" --opposite-type
py skills\media-date-organizer\scripts\organize.py --root "D:\Pictures" --opposite-type


py skills\media-date-organizer\scripts\organize.py --root $root --report-only
py skills\media-date-organizer\scripts\organize.py --root $root --flatten


Report plist and XMP files saved with a photo or video name (changes nothing)
py skills\media-date-organizer\scripts\organize.py --root $root --find-plists

Report photos in video folders and videos in photo folders, by year folder (changes nothing)
py skills\media-date-organizer\scripts\organize.py --root "D:\Videos" --opposite-type
py skills\media-date-organizer\scripts\organize.py --root "D:\Pictures" --opposite-type


## .gitignore quick reference

Already set up in this repo. The gist:

```gitignore
*.xlsx            # don't commit audit workbooks
__pycache__/      # Python bytecode cache
.venv/            # virtualenvs
Thumbs.db         # Windows file-explorer thumbnails
.DS_Store         # macOS equivalent
```

A file that's already tracked won't be ignored just by adding it here — remove it from the index first:


---


## Running `organize.py` from inside VS Code

**Fastest path — just the terminal:**

```powershell
py skills\media-date-organizer\scripts\organize.py --root "D:\Pictures\2026" --report-only
py skills\media-date-organizer\scripts\organize.py --root "D:\Pictures\2026" --fill-blanks
py skills\media-date-organizer\scripts\organize.py --root "D:\Pictures\2026" --convert-png
py skills\media-date-organizer\scripts\organize.py --root "D:\Pictures\2026" --apply-moves
py skills\media-date-organizer\scripts\organize.py --root "D:\Pictures\2026" --sync-timestamps
```

Each of these only previews (a dry run). Add `--apply` to the end of a line to make the changes.

Or the last four in one go (this also deletes `.AAE` sidecar files first), with a summary of every phase at the end. Preview, then apply:

```powershell
py skills\media-date-organizer\scripts\organize.py --root "D:\Pictures\2026" --all
py skills\media-date-organizer\scripts\organize.py --root "D:\Pictures\2026" --all --apply
```

**With the debugger** (step through code, inspect variables, set breakpoints):

Create `.vscode\launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "organize.py --report-only",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/skills/media-date-organizer/scripts/organize.py",
      "args": ["--root", "D:/Pictures/2026", "--report-only"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

Press `F5`. Click gutter next to any line number to set a breakpoint.

## Running the PowerShell scripts

Open `Fix-Extensions.ps1` or `Cleanup-Pictures.ps1`:

- `F8` — run the selected lines (or current line) in the PowerShell integrated console
- Right-click in the editor → **Run File in PowerShell Integrated Console** — run the whole script
- Or just type the full command in the terminal:
  ```powershell
  .\skills\media-date-organizer\scripts\Fix-Extensions.ps1 -Path "D:\Pictures\2026"
  ```

If PowerShell refuses to run `.ps1` files ("execution of scripts is disabled"), fix the policy once with:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```