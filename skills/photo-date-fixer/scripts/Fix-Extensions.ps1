<#
.SYNOPSIS
    Detects true file format from magic bytes and renames files whose
    extension does not match their actual content.

.DESCRIPTION
    Scans every file under the target folder (recursively) and reads the
    first 16 bytes to identify PNG, JPEG, HEIC/HEIF, MP4/MOV/QuickTime,
    3GP/3G2, GIF, WEBP, TIFF, and BMP. If the current extension doesn't match
    the detected type, the file is renamed to use the correct extension.
    Empty (0-byte) files are listed as EMPTY and left alone.

.PARAMETER Path
    Folder to scan. Defaults to the current directory.

.PARAMETER WhatIf
    PowerShell built-in. Use -WhatIf to preview without renaming.

.EXAMPLE
    .\Fix-Extensions.ps1 -Path "D:\Pictures\2026" -WhatIf
    .\Fix-Extensions.ps1 -Path "D:\Pictures\2026"
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Path = (Get-Location).Path
)

function Get-FileType {
    param([string]$FilePath)

    try {
        $fs = [System.IO.File]::OpenRead($FilePath)
        $buf = New-Object byte[] 16
        $read = $fs.Read($buf, 0, 16)
        $fs.Close()
    } catch {
        return $null
    }
    if ($read -lt 12) { return $null }

    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if ($buf[0] -eq 0x89 -and $buf[1] -eq 0x50 -and $buf[2] -eq 0x4E -and $buf[3] -eq 0x47) {
        return '.png'
    }
    # JPEG: FF D8 FF
    if ($buf[0] -eq 0xFF -and $buf[1] -eq 0xD8 -and $buf[2] -eq 0xFF) {
        return '.jpg'
    }
    # GIF: 'GIF8'
    if ($buf[0] -eq 0x47 -and $buf[1] -eq 0x49 -and $buf[2] -eq 0x46 -and $buf[3] -eq 0x38) {
        return '.gif'
    }
    # BMP: 'BM'
    if ($buf[0] -eq 0x42 -and $buf[1] -eq 0x4D) {
        return '.bmp'
    }
    # TIFF LE 'II*\0' or BE 'MM\0*'
    if (($buf[0] -eq 0x49 -and $buf[1] -eq 0x49 -and $buf[2] -eq 0x2A -and $buf[3] -eq 0x00) -or
        ($buf[0] -eq 0x4D -and $buf[1] -eq 0x4D -and $buf[2] -eq 0x00 -and $buf[3] -eq 0x2A)) {
        return '.tif'
    }
    # ISO BMFF ('ftyp' at byte 4)
    if ($buf[4] -eq 0x66 -and $buf[5] -eq 0x74 -and $buf[6] -eq 0x79 -and $buf[7] -eq 0x70) {
        $brand = [System.Text.Encoding]::ASCII.GetString($buf, 8, 4)
        switch -regex ($brand) {
            '^heic|heix|mif1|msf1$' { return '.heic' }
            '^qt\s*$'                { return '.mov' }
            '^mp4[12]$'              { return '.mp4' }
            '^M4V'                   { return '.m4v' }
            '^3g2'                   { return '.3g2' }
            '^3g'                    { return '.3gp' }
            '^isom$'                 { return '.mp4' }
            default                  { return '.mp4' }
        }
    }
    # RIFF/WEBP
    if ($buf[0] -eq 0x52 -and $buf[1] -eq 0x49 -and $buf[2] -eq 0x46 -and $buf[3] -eq 0x46 -and
        $buf[8] -eq 0x57 -and $buf[9] -eq 0x45 -and $buf[10] -eq 0x42 -and $buf[11] -eq 0x50) {
        return '.webp'
    }
    return $null
}

$equivalents = @{
    '.jpg'  = @('.jpg','.jpeg')
    '.jpeg' = @('.jpg','.jpeg')
    '.tif'  = @('.tif','.tiff')
    '.tiff' = @('.tif','.tiff')
    '.heic' = @('.heic','.heif')
    '.heif' = @('.heic','.heif')
}

$files = Get-ChildItem -Path $Path -File -Recurse
$changed = 0
$ok = 0
$unknown = 0
$empty = 0
$plan = @()

foreach ($f in $files) {
    if ($f.Extension -ieq '.xlsx' -or $f.Extension -ieq '.ps1') { continue }
    if ($f.Length -eq 0) {
        # A failed copy or transfer: nothing to detect a format from
        $empty++
        Write-Host ("EMPTY    : " + $f.FullName) -ForegroundColor DarkYellow
        continue
    }
    $detected = Get-FileType $f.FullName
    if (-not $detected) {
        $unknown++
        Write-Host ("UNKNOWN  : " + $f.FullName) -ForegroundColor DarkYellow
        continue
    }
    $curExt = $f.Extension.ToLower()
    $okExts = if ($equivalents.ContainsKey($detected)) { $equivalents[$detected] } else { @($detected) }
    if ($okExts -contains $curExt) {
        $ok++
        continue
    }
    # Preserve the case style of the original extension (upper or lower)
    $newExt = if ($f.Extension.ToUpper() -ceq $f.Extension) { $detected.ToUpper() } else { $detected }
    $newPath = [System.IO.Path]::ChangeExtension($f.FullName, $newExt)
    $plan += [pscustomobject]@{
        Folder    = (Split-Path $f.FullName -Parent)
        OldName   = $f.Name
        NewName   = (Split-Path $newPath -Leaf)
        OldExt    = $f.Extension
        NewExt    = $newExt
        Detected  = $detected
    }
    if ($PSCmdlet.ShouldProcess($f.FullName, "Rename to $(Split-Path $newPath -Leaf)")) {
        Rename-Item -LiteralPath $f.FullName -NewName (Split-Path $newPath -Leaf)
        $changed++
        Write-Host ("RENAMED  : " + $f.Name + "  ->  " + (Split-Path $newPath -Leaf)) -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host ("  Correct extension : " + $ok)
Write-Host ("  Renamed           : " + $changed)
Write-Host ("  Unknown format    : " + $unknown)
Write-Host ("  Empty (0 bytes)   : " + $empty)
if ($plan.Count -gt 0 -and -not $PSBoundParameters.ContainsKey('WhatIf')) {
    $plan | Format-Table -AutoSize
}
