<#
.SYNOPSIS
Runs --move-incomplete on each year folder under a root, so each year's
incomplete files go into that year's own _incomplete folder.

.EXAMPLE
.\scripts\Move-IncompleteByYear.ps1 -Root "E:\Pictures"            # preview
.\scripts\Move-IncompleteByYear.ps1 -Root "E:\Pictures" -Apply     # move
#>
param(
    [Parameter(Mandatory)] [string] $Root,
    [switch] $Apply
)

$organize = Join-Path $PSScriptRoot '..\skills\media-date-organizer\scripts\organize.py'
$python = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }

$years = Get-ChildItem -LiteralPath $Root -Directory | Where-Object Name -match '^\d{4}$' | Sort-Object Name
if (-not $years) {
    Write-Host "No year folders found in $Root"
    exit 0
}

$failed = 0
foreach ($year in $years) {
    Write-Host "===== $($year.Name) ====="
    $cmd = @($organize, '--root', $year.FullName, '--move-incomplete')
    if ($Apply) { $cmd += '--apply' }
    & $python @cmd
    if ($LASTEXITCODE -ne 0) { $failed++ }
}

Write-Host "Done: $($years.Count) year folder(s), $failed with errors."
exit [int]($failed -gt 0)
