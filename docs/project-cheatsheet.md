How to run all phases

Every step only previews what it would do. The commands below have --apply (-Apply for the .ps1 script) so they make the changes; leave it off to preview first.

```powershell
cd C:\Code\media-date-organizer
$root = "D:\Pictures\2026"

py skills\media-date-organizer\scripts\organize.py --root $root --report-only

py skills\media-date-organizer\scripts\organize.py --root $root --all
py skills\media-date-organizer\scripts\organize.py --root $root --all --apply

.\skills\media-date-organizer\scripts\Fix-Extensions.ps1 -Path $root
.\skills\media-date-organizer\scripts\Fix-Extensions.ps1 -Path $root -Apply

py skills\media-date-organizer\scripts\organize.py --root $root --fix-extensions
py skills\media-date-organizer\scripts\organize.py --root $root --fix-extensions --apply

py skills\media-date-organizer\scripts\organize.py --root $root --quarantine-ads
py skills\media-date-organizer\scripts\organize.py --root $root --quarantine-ads --apply
py skills\media-date-organizer\scripts\organize.py --root $root --move-incomplete
py skills\media-date-organizer\scripts\organize.py --root $root --move-incomplete --apply
py skills\media-date-organizer\scripts\organize.py --root $root --move-junk
py skills\media-date-organizer\scripts\organize.py --root $root --move-junk --apply
py skills\media-date-organizer\scripts\organize.py --root $root --find-plists
py skills\media-date-organizer\scripts\organize.py --root $root --find-plists --apply

py skills\media-date-organizer\scripts\organize.py --root $root --convert-bmp
py skills\media-date-organizer\scripts\organize.py --root $root --convert-bmp --apply

py skills\media-date-organizer\scripts\organize.py --root $root --fill-blanks
py skills\media-date-organizer\scripts\organize.py --root $root --fill-blanks --apply

py skills\media-date-organizer\scripts\organize.py --root $root --convert-png
py skills\media-date-organizer\scripts\organize.py --root $root --convert-png --apply

py skills\media-date-organizer\scripts\organize.py --root $root --sync-timestamps
py skills\media-date-organizer\scripts\organize.py --root $root --sync-timestamps --apply
py skills\media-date-organizer\scripts\organize.py --root $root --apply-moves
py skills\media-date-organizer\scripts\organize.py --root $root --apply-moves --apply
py skills\media-date-organizer\scripts\organize.py --root $root --flatten
py skills\media-date-organizer\scripts\organize.py --root $root --flatten --apply
py skills\media-date-organizer\scripts\organize.py --root $root --visual-compare
.\skills\media-date-organizer\scripts\Cleanup-Pictures.ps1 -Path $root
.\skills\media-date-organizer\scripts\Cleanup-Pictures.ps1 -Path $root -Apply
py -m unittest discover tests -v

py skills\media-date-organizer\scripts\organize.py --root $root --opposite-type
py skills\media-date-organizer\scripts\organize.py --root $root --opposite-type
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

## Running the PowerShell cleanup script

Open `Cleanup-Pictures.ps1`:

- `F8` — run the selected lines (or current line) in the PowerShell integrated console
- Right-click in the editor → **Run File in PowerShell Integrated Console** — run the whole script
- Or just type the full command in the terminal:
  ```powershell
  .\skills\media-date-organizer\scripts\Cleanup-Pictures.ps1 -Path "D:\Pictures\2026"
  ```

If PowerShell refuses to run `.ps1` files ("execution of scripts is disabled"), fix the policy once with:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```