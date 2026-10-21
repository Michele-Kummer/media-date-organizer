<#
.SYNOPSIS
    Records lines in the audit workbook (<folder name>_<photos|videos>_media_audit_<date>.xlsx in the target
    folder), on the same Run log sheet organize.py writes to.

.DESCRIPTION
    Dot-sourced by Fix-Extensions.ps1 and Cleanup-Pictures.ps1. Hands the
    lines to "organize.py --audit-log", which owns the workbook format.
    Needs Python with openpyxl; without it the lines are not recorded and a
    note says so.
#>

function Write-AuditLog {
    param(
        [string]$Path,
        [string]$Phase,
        [string[]]$Lines,
        [switch]$DryRun
    )
    if (-not $Lines -or $Lines.Count -eq 0) { return }
    # "python" first, then the "py" launcher, which is often all a python.org
    # install puts on PATH. The Microsoft Store stub in WindowsApps only opens
    # the Store, so it does not count as Python.
    $pyArgs = @()
    $python = Get-Command python -CommandType Application -ErrorAction SilentlyContinue |
        Where-Object { $_.Source -notlike '*\WindowsApps\*' } | Select-Object -First 1
    if (-not $python) {
        $python = Get-Command py -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($python) { $pyArgs += '-3' }
    }
    if (-not $python) {
        Write-Host "Python not found; this run is NOT recorded in the audit workbook." -ForegroundColor DarkYellow
        return
    }
    $pyArgs += @((Join-Path $PSScriptRoot 'organize.py'), '--root', $Path, '--audit-log', $Phase)
    # organize.py records a run as a dry run unless it is told otherwise
    if (-not $DryRun) { $pyArgs += '--apply' }
    # File names can hold non-ASCII characters; the default pipe encoding
    # would turn them into question marks
    $previous = $OutputEncoding
    $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    try {
        $Lines | & $python.Source @pyArgs
    } finally {
        $OutputEncoding = $previous
    }
}
