<#
.SYNOPSIS
    Housekeeping for the pictures tree: removes leftover "duplicate" files
    (same base name, different extension — e.g. a PNG that was converted to
    JPG but the PNG still sits alongside), and moves empty folders into an
    _empty_folders folder, keeping their path, instead of deleting them.

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

# ---- Pass 2: move empty folders into _empty_folders (not deleted) ----
# A folder is empty when nothing but other folders is in it, at any depth.
# Only the topmost of a nested run is moved; its empty subfolders go with it,
# keeping their path relative to $Path. A path already taken in
# _empty_folders gets a " (2)", " (3)" ... ending.
$root = (Resolve-Path -LiteralPath $Path).ProviderPath.TrimEnd('\')
$emptyRoot = Join-Path $root '_empty_folders'
$movedFolders = 0
$empties = @(Get-ChildItem -LiteralPath $root -Directory -Recurse |
    Where-Object {
        -not ($_.FullName + '\').StartsWith($emptyRoot + '\', [StringComparison]::OrdinalIgnoreCase) -and
        @(Get-ChildItem -LiteralPath $_.FullName -File -Recurse -Force).Count -eq 0
    })
$emptyPaths = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($e in $empties) { [void]$emptyPaths.Add($e.FullName) }
foreach ($e in ($empties | Sort-Object FullName)) {
    if ($emptyPaths.Contains($e.Parent.FullName)) { continue }   # moves with its parent
    $rel = $e.FullName.Substring($root.Length + 1)
    $dst = $base = Join-Path $emptyRoot $rel
    $n = 2
    while (Test-Path -LiteralPath $dst) { $dst = "$base ($n)"; $n++ }
    $nested = @($empties | Where-Object { $_.FullName -eq $e.FullName -or $_.FullName.StartsWith($e.FullName + '\') }).Count
    $relDst = $dst.Substring($root.Length + 1)
    if ($PSCmdlet.ShouldProcess($e.FullName, "Move empty folder to $relDst")) {
        New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
        Move-Item -LiteralPath $e.FullName -Destination $dst
        $movedFolders += $nested
        Write-Host ("MOVED EMPTY: " + $rel + " -> " + $relDst) -ForegroundColor DarkYellow
        $audit.Add("MOVED EMPTY: " + $rel + " -> " + $relDst)
    } elseif ($WhatIfPreference) {
        $audit.Add("WOULD MOVE EMPTY: " + $rel + " -> " + $relDst)
    }
}

Write-Host ""
Write-Host "Cleanup summary:" -ForegroundColor Cyan
Write-Host ("  Duplicate files removed       : " + $deletedDupes)
Write-Host ("  Empty folders moved aside     : " + $movedFolders + " (into _empty_folders)")

$audit.Add("SUMMARY: duplicate files removed $deletedDupes, empty folders moved into _empty_folders $movedFolders")
Write-AuditLog -Path $Path -Phase 'cleanup' -Lines $audit -DryRun:$WhatIfPreference
