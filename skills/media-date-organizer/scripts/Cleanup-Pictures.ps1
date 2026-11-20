<#
.SYNOPSIS
    Housekeeping for the pictures tree: moves the PNGs, BMPs and WebPs left
    behind after organize.py --convert-png, --convert-bmp or --convert-webp
    (a PNG, BMP or WebP with a JPG of the same name, the same picture size
    and the same pixels beside it) into a _converted folder, and moves empty
    folders into an _empty_folders folder, keeping their path. Nothing is
    deleted.
    Ends by counting the photos and videos whose Date Taken is in a
    different year from the folder (organize.py --other-year); that count
    changes nothing.

.DESCRIPTION
    Only the original of those pairs is ever moved. A Live Photo video next
    to its photo (IMG_1.HEIC / IMG_1.MOV), a sidecar (IMG_1.JPG / IMG_1.xmp),
    a HEIC next to a JPG, or a PNG, BMP or WebP whose JPG is a different size
    or a different picture are all kept. _ads, _incomplete, _no-image-data,
    _junk, _thumbnails, _screenshots, _converted and _empty_folders are left
    alone.

    Each original goes straight into <Path>\_converted, with no subfolders,
    as organize.py --convert-webp does. A name already there gets its
    folder's name added (scan.png from 2021-05-04 becomes
    scan_2021-05-04.png); when that is taken too, the original stays and is
    listed as COLLISION. WebP is read through the Windows Imaging Component
    (the WebP Image Extension, part of Windows 11), since System.Drawing
    cannot read it; a WebP it cannot read is listed as KEPT.

.PARAMETER Path
    Root folder to clean. Defaults to the current directory.

.PARAMETER MaxPixelDifference
    Largest pixel difference, in percent, at which an original and its JPG count as
    the same picture. Both are shrunk to 128x128 and the mean difference of
    their pixels is taken, as in organize.py --visual-compare, where up to 1%
    is a DUPLICATE with high confidence. Default 1.

.PARAMETER Apply
    Move the converted originals and the empty folders. Without it the
    script only lists what it would do (a dry run) and changes nothing.
    -WhatIf also previews.

.EXAMPLE
    .\Cleanup-Pictures.ps1 -Path "D:\Pictures\2026"
    .\Cleanup-Pictures.ps1 -Path "D:\Pictures\2026" -Apply
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Path = (Get-Location).Path,
    [double]$MaxPixelDifference = 1.0,
    [switch]$Apply
)

# A dry run unless -Apply is given
if (-not $Apply) { $WhatIfPreference = $true }

Add-Type -AssemblyName System.Drawing
# WIC decodes WebP, which System.Drawing cannot
$script:HasWic = $true
try { Add-Type -AssemblyName PresentationCore } catch { $script:HasWic = $false }

# Everything reported is also recorded in the audit workbook at the end
. (Join-Path $PSScriptRoot 'Write-AuditLog.ps1')
$audit = [System.Collections.Generic.List[string]]::new()

# A stream System.Drawing can read for a picture: the file itself, or for
# a WebP, the picture decoded by WIC and saved as PNG in memory. The caller
# disposes of it. Throws when the file cannot be read.
function Open-PictureStream([string]$file) {
    if ([System.IO.Path]::GetExtension($file) -ne '.webp') { return [System.IO.File]::OpenRead($file) }
    if (-not $script:HasWic) { throw 'WIC is not available' }
    $in = [System.IO.File]::OpenRead($file)
    try {
        $decoder = [System.Windows.Media.Imaging.BitmapDecoder]::Create($in,
            [System.Windows.Media.Imaging.BitmapCreateOptions]::None,
            [System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad)
        $encoder = [System.Windows.Media.Imaging.PngBitmapEncoder]::new()
        $encoder.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($decoder.Frames[0]))
        $out = [System.IO.MemoryStream]::new()
        $encoder.Save($out)
        $out.Position = 0
        return , $out
    } finally { $in.Dispose() }
}

# Width x height of a picture, or $null when it cannot be read. Only the
# header is read (validateImageData off), not the whole picture.
function Get-PictureSize([string]$file) {
    try {
        $stream = Open-PictureStream $file
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
            $stream = Open-PictureStream $file
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
$holding = '_ads', '_incomplete', '_no-image-data', '_empty_folders', '_junk', '_thumbnails', '_screenshots', '_converted'
function Test-InHolding([string]$dir) {
    if ($dir.Length -le $root.Length) { return $false }
    # At any depth: --quarantine-ads gives each year folder its own _ads
    foreach ($part in $dir.Substring($root.Length + 1).Split('\')) {
        if ($holding -contains $part) { return $true }
    }
    return $false
}

# ---- Pass 1: move PNGs, BMPs and WebPs already converted to JPG ----
# Into $root\_converted, flat, as organize.py --convert-webp does
# (_flat_dest): the name as it is, else with its folder's name added.
$convertedRoot = Join-Path $root '_converted'
$claimed = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
function Get-ConvertedDestination([System.IO.FileInfo]$file) {
    $candidates = @($file.Name)
    if ($file.DirectoryName.Length -gt $root.Length) {
        $candidates += $file.BaseName + '_' + $file.Directory.Name + $file.Extension
    }
    foreach ($name in $candidates) {
        $dst = Join-Path $convertedRoot $name
        if (-not $claimed.Contains($dst) -and -not (Test-Path -LiteralPath $dst)) {
            [void]$claimed.Add($dst)
            return $dst
        }
    }
    return $null
}

$movedConverted = 0
$keptPairs = 0
$collisions = 0
$originals = Get-ChildItem -LiteralPath $root -File -Recurse |
    Where-Object { ('.png', '.bmp', '.webp') -contains $_.Extension.ToLower() -and -not (Test-InHolding $_.DirectoryName) } |
    Sort-Object FullName
foreach ($original in $originals) {
    $kind = $original.Extension.TrimStart('.').ToUpper()
    $rel = $original.FullName.Substring($root.Length + 1)
    $jpg = foreach ($ext in '.jpg', '.jpeg') {
        $candidate = Join-Path $original.DirectoryName ($original.BaseName + $ext)
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { Get-Item -LiteralPath $candidate; break }
    }
    if (-not $jpg) { continue }
    $originalSize = Get-PictureSize $original.FullName
    $jpgSize = Get-PictureSize $jpg.FullName
    if (-not $originalSize -or -not $jpgSize -or $originalSize -ne $jpgSize -or $jpg.Length -eq 0) {
        # Not a finished conversion of this original: a different picture
        # that happens to share its name, or a file that cannot be read
        $keptPairs++
        $why = if (-not $originalSize -or -not $jpgSize) { 'cannot read picture size' } else { "$kind $originalSize, JPG $jpgSize" }
        Write-Host ("KEPT (not the same picture, $why): " + $original.FullName) -ForegroundColor DarkCyan
        $audit.Add("KEPT (not the same picture, $why): " + $original.FullName)
        continue
    }
    # Same size is not enough: two screenshots from one phone share it. A
    # conversion at quality 95 differs by well under the limit.
    $diff = Get-PixelDifference $original.FullName $jpg.FullName
    if ($null -eq $diff -or $diff -gt $MaxPixelDifference) {
        $keptPairs++
        $why = if ($null -eq $diff) { 'cannot read pixels' } else { 'pixel difference {0:N1}%' -f $diff }
        Write-Host ("KEPT (not the same picture, $why): " + $original.FullName) -ForegroundColor DarkCyan
        $audit.Add("KEPT (not the same picture, $why): " + $original.FullName)
        continue
    }
    $dst = Get-ConvertedDestination $original
    if (-not $dst) {
        $collisions++
        Write-Host "COLLISION, skipping: $rel (its name is taken in _converted)" -ForegroundColor DarkYellow
        $audit.Add("COLLISION, skipping: $rel (its name is taken in _converted)")
        continue
    }
    $relDst = $dst.Substring($root.Length + 1)
    if ($PSCmdlet.ShouldProcess($original.FullName, "Move $kind already converted to " + $jpg.Name + " into $relDst")) {
        New-Item -ItemType Directory -Force -Path $convertedRoot | Out-Null
        Move-Item -LiteralPath $original.FullName -Destination $dst
        $movedConverted++
        Write-Host ("MOVED (converted to " + $jpg.Name + "): $rel -> $relDst") -ForegroundColor Yellow
        $audit.Add("MOVED (converted to " + $jpg.Name + "): $rel -> $relDst")
    } elseif ($WhatIfPreference) {
        $movedConverted++
        Write-Host ("WOULD MOVE (converted to " + $jpg.Name + "): $rel -> $relDst") -ForegroundColor Yellow
        $audit.Add("WOULD MOVE (converted to " + $jpg.Name + "): $rel -> $relDst")
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
        $movedFolders += $nested
        Write-Host ("WOULD MOVE EMPTY: " + $rel + " -> " + $relDst) -ForegroundColor DarkYellow
        $audit.Add("WOULD MOVE EMPTY: " + $rel + " -> " + $relDst)
    }
}

# ---- Pass 3: count media from a different year (report only) ----
# organize.py --other-year reads each file's Date Taken (Media Created for a
# video), which PowerShell cannot do for HEIC or MOV, and records its own
# run in the audit workbook. Only its OTHER YEAR lines are shown here.
$otherYear = $null
$otherYearNote = 'not counted'
$python = Get-PythonCommand
if ($python) {
    $previous = [Console]::OutputEncoding
    $previousIo = $env:PYTHONIOENCODING
    # File names can hold characters the console code page cannot
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $env:PYTHONIOENCODING = 'utf-8'
    try {
        $pyArgs = @($python | Select-Object -Skip 1) + @((Join-Path $PSScriptRoot 'organize.py'), '--root', $root, '--other-year')
        $lines = & $python[0] @pyArgs 2>&1 | ForEach-Object { "$_" }
    } finally {
        [Console]::OutputEncoding = $previous
        $env:PYTHONIOENCODING = $previousIo
    }
    foreach ($line in $lines) {
        if ($line -match '^OTHER YEAR: (\d[\d,]*) of ') {
            $otherYear = [int]($Matches[1] -replace ',', '')
            $otherYearNote = $line.Substring('OTHER YEAR: '.Length)
            Write-Host $line -ForegroundColor Cyan
        } elseif ($line -like 'OTHER YEAR*') {
            Write-Host $line -ForegroundColor DarkYellow
        }
    }
    if ($null -eq $otherYear -and $LASTEXITCODE -ne 0) {
        Write-Host "Could not count media from a different year:" -ForegroundColor DarkYellow
        $lines | Select-Object -Last 5 | ForEach-Object { Write-Host "  $_" }
    }
} else {
    Write-Host "Python not found; media from a different year were not counted." -ForegroundColor DarkYellow
}

$would = if ($WhatIfPreference) { 'would be ' } else { '' }
Write-Host ""
Write-Host "Cleanup summary:" -ForegroundColor Cyan
Write-Host ("  Converted PNGs, BMPs and WebPs " + $would + "moved : " + $movedConverted + " (into _converted)")
Write-Host ("  Pairs kept (not the same picture) : " + $keptPairs)
if ($collisions) { Write-Host ("  Name taken in _converted, kept : " + $collisions) }
Write-Host ("  Empty folders " + $would + "moved aside : " + $movedFolders + " (into _empty_folders)")
Write-Host ("  Media from a different year : " + $(if ($null -eq $otherYear) { $otherYearNote } else { $otherYear }))
if ($otherYear) { Write-Host "    (each is listed above as OTHER YEAR (<year>): <file>)" }

$audit.Add("SUMMARY: converted PNGs, BMPs and WebPs ${would}moved into _converted $movedConverted, pairs kept $keptPairs, name taken in _converted $collisions, empty folders ${would}moved into _empty_folders $movedFolders, media from a different year $(if ($null -eq $otherYear) { $otherYearNote } else { $otherYear })")
Write-AuditLog -Path $Path -Phase 'cleanup' -Lines $audit -DryRun:$WhatIfPreference
if ($WhatIfPreference) {
    Write-Host ""
    Write-Host "DRY RUN: nothing was moved. Run the same command again with -Apply to make these changes." -ForegroundColor Cyan
}
