<#
.SYNOPSIS
    Housekeeping for the pictures tree: removes PNGs left behind after
    organize.py --convert-png (a PNG with a JPG of the same name, the same
    picture size and the same pixels beside it), and moves empty folders into
    an _empty_folders folder, keeping their path, instead of deleting them.

.DESCRIPTION
    Only that one pair is ever deleted from. A Live Photo video next to its
    photo (IMG_1.HEIC / IMG_1.MOV), a sidecar (IMG_1.JPG / IMG_1.xmp), a
    HEIC next to a JPG, or a PNG whose JPG is a different size or a different
    picture are all kept. _ads, _incomplete, _no-image-data and
    _empty_folders are left alone.

.PARAMETER Path
    Root folder to clean. Defaults to the current directory.

.PARAMETER MaxPixelDifference
    Largest pixel difference, in percent, at which a PNG and its JPG count as
    the same picture. Both are shrunk to 128x128 and the mean difference of
    their pixels is taken, as in organize.py --visual-compare, where up to 1%
    is a DUPLICATE with high confidence. Default 1.

.PARAMETER WhatIf
    PowerShell built-in. Use -WhatIf to preview without deleting.

.EXAMPLE
    .\Cleanup-Pictures.ps1 -Path "D:\Pictures\2026" -WhatIf
    .\Cleanup-Pictures.ps1 -Path "D:\Pictures\2026"
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Path = (Get-Location).Path,
    [double]$MaxPixelDifference = 1.0
)

Add-Type -AssemblyName System.Drawing

# Everything reported is also recorded in the audit workbook at the end
. (Join-Path $PSScriptRoot 'Write-AuditLog.ps1')
$audit = [System.Collections.Generic.List[string]]::new()

# Width x height of a picture, or $null when it cannot be read. Only the
# header is read (validateImageData off), not the whole picture.
function Get-PictureSize([string]$file) {
    try {
        $stream = [System.IO.File]::OpenRead($file)
        try {
            $img = [System.Drawing.Image]::FromStream($stream, $false, $false)
            try { return "$($img.Width)x$($img.Height)" } finally { $img.Dispose() }
        } finally { $stream.Dispose() }
    } catch { return $null }
}

# How far apart two pictures are, 0 (same) to 100 (opposite): the mean
# difference of their pixels once both are shrunk to 128x128. The same
# measure as organize.py --visual-compare (_pixel_difference). $null when
# either cannot be read.
function Get-PixelDifference([string]$a, [string]$b) {
    $edge = 128
    $pixels = foreach ($file in $a, $b) {
        $small = [System.Drawing.Bitmap]::new($edge, $edge, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
        try {
            $stream = [System.IO.File]::OpenRead($file)
            try {
                $img = [System.Drawing.Image]::FromStream($stream, $false, $true)
                try {
                    $g = [System.Drawing.Graphics]::FromImage($small)
                    try {
                        $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBilinear
                        $g.DrawImage($img, 0, 0, $edge, $edge)
                    } finally { $g.Dispose() }
                } finally { $img.Dispose() }
            } finally { $stream.Dispose() }
            $rect = [System.Drawing.Rectangle]::new(0, 0, $edge, $edge)
            $data = $small.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::ReadOnly, $small.PixelFormat)
            try {
                $bytes = [byte[]]::new($data.Stride * $edge)
                [System.Runtime.InteropServices.Marshal]::Copy($data.Scan0, $bytes, 0, $bytes.Length)
                , $bytes
            } finally { $small.UnlockBits($data) }
        } catch { return $null } finally { $small.Dispose() }
    }
    $pa, $pb = $pixels
    $total = [long]0
    for ($i = 0; $i -lt $pa.Length; $i++) { $total += [Math]::Abs([int]$pa[$i] - [int]$pb[$i]) }
    return $total / $pa.Length / 255 * 100
}

$root = (Resolve-Path -LiteralPath $Path).ProviderPath.TrimEnd('\')
# Same holding folders organize.py leaves alone (HOLDING_DIRS)
$holding = '_ads', '_incomplete', '_no-image-data', '_empty_folders'
function Test-InHolding([string]$dir) {
    if ($dir.Length -le $root.Length) { return $false }
    $first = $dir.Substring($root.Length + 1).Split('\')[0]
    return $holding -contains $first
}

# ---- Pass 1: remove PNGs already converted to JPG ----
$deletedDupes = 0
$keptPairs = 0
$pngs = Get-ChildItem -LiteralPath $root -File -Recurse -Filter '*.png' |
    Where-Object { $_.Extension -eq '.png' -and -not (Test-InHolding $_.DirectoryName) }
foreach ($png in $pngs) {
    $jpg = foreach ($ext in '.jpg', '.jpeg') {
        $candidate = Join-Path $png.DirectoryName ($png.BaseName + $ext)
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { Get-Item -LiteralPath $candidate; break }
    }
    if (-not $jpg) { continue }
    $pngSize = Get-PictureSize $png.FullName
    $jpgSize = Get-PictureSize $jpg.FullName
    if (-not $pngSize -or -not $jpgSize -or $pngSize -ne $jpgSize -or $jpg.Length -eq 0) {
        # Not a finished conversion of this PNG: a different picture that
        # happens to share its name, or a file that cannot be read
        $keptPairs++
        $why = if (-not $pngSize -or -not $jpgSize) { 'cannot read picture size' } else { "PNG $pngSize, JPG $jpgSize" }
        Write-Host ("KEPT (not the same picture, $why): " + $png.FullName) -ForegroundColor DarkCyan
        $audit.Add("KEPT (not the same picture, $why): " + $png.FullName)
        continue
    }
    # Same size is not enough: two screenshots from one phone share it. A
    # conversion at quality 95 differs by well under the limit.
    $diff = Get-PixelDifference $png.FullName $jpg.FullName
    if ($null -eq $diff -or $diff -gt $MaxPixelDifference) {
        $keptPairs++
        $why = if ($null -eq $diff) { 'cannot read pixels' } else { 'pixel difference {0:N1}%' -f $diff }
        Write-Host ("KEPT (not the same picture, $why): " + $png.FullName) -ForegroundColor DarkCyan
        $audit.Add("KEPT (not the same picture, $why): " + $png.FullName)
        continue
    }
    Write-Host ("Converted PNG in " + $png.DirectoryName + ":") -ForegroundColor Cyan
    Write-Host ("  KEEP: " + $jpg.Name) -ForegroundColor Green
    Write-Host ("  DROP: " + $png.Name) -ForegroundColor Yellow
    if ($PSCmdlet.ShouldProcess($png.FullName, 'Remove PNG already converted to ' + $jpg.Name)) {
        Remove-Item -LiteralPath $png.FullName -Force
        $deletedDupes++
        $audit.Add("DELETED (converted to " + $jpg.Name + "): " + $png.FullName)
    } elseif ($WhatIfPreference) {
        $audit.Add("WOULD DELETE (converted to " + $jpg.Name + "): " + $png.FullName)
    }
}

# ---- Pass 2: move empty folders into _empty_folders (not deleted) ----
# A folder is empty when nothing but other folders is in it, at any depth.
# Only the topmost of a nested run is moved; its empty subfolders go with it,
# keeping their path relative to $Path. A path already taken in
# _empty_folders gets a " (2)", " (3)" ... ending.
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
Write-Host ("  Converted PNGs removed        : " + $deletedDupes)
Write-Host ("  PNG/JPG pairs kept (differ)   : " + $keptPairs)
Write-Host ("  Empty folders moved aside     : " + $movedFolders + " (into _empty_folders)")

$audit.Add("SUMMARY: converted PNGs removed $deletedDupes, PNG/JPG pairs kept $keptPairs, empty folders moved into _empty_folders $movedFolders")
Write-AuditLog -Path $Path -Phase 'cleanup' -Lines $audit -DryRun:$WhatIfPreference
