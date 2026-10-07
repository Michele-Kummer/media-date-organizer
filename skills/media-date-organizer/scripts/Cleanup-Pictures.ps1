<#
.SYNOPSIS
    Housekeeping for the pictures tree: removes empty folders and leftover
    "duplicate" files (same base name, different extension — e.g. a PNG
    that was converted to JPG but the PNG still sits alongside).

.PARAMETER Path
    Root folder to clean. Defaults to the current directory.

.PARAMETER PreferredExtOrder
    When two or more files share the same base name in the same folder,
    the file whose extension comes EARLIEST in this list is kept; the
    others are deleted. Default order favors HEIC and JPG (lossy/EXIF-rich)
    over PNG so camera/phone content survives.

.PARAMETER WhatIf
    PowerShell built-in. Use -WhatIf to preview without deleting.

.EXAMPLE
    .\Cleanup-Pictures.ps1 -Path "D:\Pictures\2026" -WhatIf
    .\Cleanup-Pictures.ps1 -Path "D:\Pictures\2026"
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Path = (Get-Location).Path,
    [string[]]$PreferredExtOrder = @('.heic', '.heif', '.jpg', '.jpeg', '.mov', '.mp4', '.m4v', '.3gp', '.3g2', '.tif', '.tiff', '.gif', '.bmp', '.webp', '.png')
)

$preferRank = @{}
for ($i = 0; $i -lt $PreferredExtOrder.Count; $i++) {
    $preferRank[$PreferredExtOrder[$i].ToLower()] = $i
}

# Everything reported is also recorded in the audit workbook at the end
. (Join-Path $PSScriptRoot 'Write-AuditLog.ps1')
$audit = [System.Collections.Generic.List[string]]::new()

# ---- Pass 1: remove duplicate base-name files ----
$files = Get-ChildItem -Path $Path -File -Recurse |
    Where-Object { $_.Extension -notin '.ps1', '.xlsx' }

$deletedDupes = 0
$groups = $files | Group-Object { Join-Path $_.DirectoryName $_.BaseName }
foreach ($g in $groups) {
    if ($g.Count -lt 2) { continue }
    # Rank: known extensions by $preferRank (lower = better), unknown go last
    $ranked = $g.Group | Sort-Object `
        @{Expression = { if ($preferRank.ContainsKey($_.Extension.ToLower())) { $preferRank[$_.Extension.ToLower()] } else { 9999 } }},
        @{Expression = { $_.Length }; Descending = $true}
    $keep = $ranked[0]
    $drop = $ranked | Select-Object -Skip 1
    Write-Host ("Duplicates for " + $keep.BaseName + " in " + $keep.DirectoryName + ":") -ForegroundColor Cyan
    Write-Host ("  KEEP: " + $keep.Name) -ForegroundColor Green
    foreach ($d in $drop) {
        Write-Host ("  DROP: " + $d.Name) -ForegroundColor Yellow
        if ($PSCmdlet.ShouldProcess($d.FullName, 'Remove duplicate')) {
            Remove-Item -LiteralPath $d.FullName -Force
            $deletedDupes++
            $audit.Add("DELETED (duplicate of " + $keep.Name + "): " + $d.FullName)
        } elseif ($WhatIfPreference) {
            $audit.Add("WOULD DELETE (duplicate of " + $keep.Name + "): " + $d.FullName)
        }
    }
}

# ---- Pass 2: remove empty folders (iterate until stable) ----
$deletedFolders = 0
do {
    $removedThisPass = 0
    $empties = Get-ChildItem -Path $Path -Directory -Recurse |
               Where-Object { $_.GetFileSystemInfos().Count -eq 0 }
    foreach ($e in $empties) {
        if ($PSCmdlet.ShouldProcess($e.FullName, 'Remove empty folder')) {
            Remove-Item -LiteralPath $e.FullName -Force
            $deletedFolders++
            $removedThisPass++
            Write-Host ("REMOVED EMPTY: " + $e.FullName) -ForegroundColor DarkYellow
            $audit.Add("REMOVED EMPTY: " + $e.FullName)
        } elseif ($WhatIfPreference) {
            $audit.Add("WOULD REMOVE EMPTY: " + $e.FullName)
        }
    }
    # Stop once a pass removes nothing: under -WhatIf the same empty folders
    # would otherwise be found forever
} while ($removedThisPass -gt 0)

Write-Host ""
Write-Host "Cleanup summary:" -ForegroundColor Cyan
Write-Host ("  Duplicate files removed : " + $deletedDupes)
Write-Host ("  Empty folders removed   : " + $deletedFolders)

$audit.Add("SUMMARY: duplicate files removed $deletedDupes, empty folders removed $deletedFolders")
Write-AuditLog -Path $Path -Phase 'cleanup' -Lines $audit -DryRun:$WhatIfPreference
