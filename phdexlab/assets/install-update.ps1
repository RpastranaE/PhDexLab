param([Parameter(Mandatory=$true)][string]$Job)
$ErrorActionPreference='Stop'
$taskJob=Get-Content -LiteralPath $Job -Raw | ConvertFrom-Json
$taskRoot=[IO.Path]::GetFullPath($taskJob.root)
$taskStage=[IO.Path]::GetFullPath($taskJob.stage)
$taskTarget=Join-Path $taskRoot 'Application'
$taskNew=Join-Path $taskStage 'Application'
$taskBackup=Join-Path $taskRoot ('.PhDexLab-backup-'+[Guid]::NewGuid().ToString('N'))
$taskMoved=$false
$taskInstalled=$false
function Write-Receipt($state,$detail) {
    @{state=$state;detail=$detail;time=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $taskJob.receipt -Encoding UTF8
}
try {
    if ((Split-Path -Parent $taskStage) -ne $taskRoot -or (Split-Path -Leaf $taskStage) -notmatch '^\.PhDexLab-update-[a-f0-9]{32}$') {throw 'Invalid stage path'}
    if (-not (Test-Path -LiteralPath (Join-Path $taskNew 'PhDexLab.exe'))) {throw 'Missing new executable'}
    foreach ($taskPath in @($taskTarget,$taskStage,$taskNew)) {
        if ((Get-Item -LiteralPath $taskPath).Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'Update path is a reparse point'}
    }
    $taskParent=Get-Process -Id $taskJob.pid -ErrorAction SilentlyContinue
    if ($taskParent) {$taskParent.WaitForExit()}
    for ($taskAttempt=0; $taskAttempt -lt 30; $taskAttempt++) {
        try {Move-Item -LiteralPath $taskTarget -Destination $taskBackup; $taskMoved=$true; break}
        catch {if ($taskAttempt -eq 29) {throw};Start-Sleep -Milliseconds 500}
    }
    Move-Item -LiteralPath $taskNew -Destination $taskTarget
    $taskInstalled=$true
    $taskExe=Join-Path $taskTarget 'PhDexLab.exe'
    $taskHealth=Start-Process -FilePath $taskExe -ArgumentList '--update-healthcheck' -WorkingDirectory $taskRoot -WindowStyle Hidden -PassThru
    if (-not $taskHealth.WaitForExit(60000)) {$taskHealth.Kill();throw 'New version health check timed out'}
    if ($taskHealth.ExitCode -ne 0) {throw 'New version failed its startup health check'}
    Write-Receipt 'installed' 'Application updated; user experiments and preferences preserved.'
    # Both paths are generated children of the verified installation root.
    try {
        if ((Split-Path -Parent $taskBackup) -eq $taskRoot -and (Split-Path -Leaf $taskBackup) -match '^\.PhDexLab-backup-[a-f0-9]{32}$') {Remove-Item -LiteralPath $taskBackup -Recurse -Force}
        if ((Split-Path -Parent $taskStage) -eq $taskRoot) {Remove-Item -LiteralPath $taskStage -Recurse -Force}
    } catch {Write-Receipt 'installed' ('Application updated; optional cleanup: '+$_.Exception.Message)}
    if ($taskJob.relaunch) {Start-Process -FilePath $taskExe -WorkingDirectory $taskRoot -WindowStyle Hidden}
} catch {
    $taskError=$_.Exception.Message
    try {
        if ($taskInstalled -and (Test-Path -LiteralPath $taskTarget)) {
            # Return the failed new version to its own stage, keeping its diagnostics.
            Move-Item -LiteralPath $taskTarget -Destination $taskNew
        }
        if ($taskMoved -and (Test-Path -LiteralPath $taskBackup)) {Move-Item -LiteralPath $taskBackup -Destination $taskTarget}
        if ($taskJob.relaunch -and (Test-Path -LiteralPath (Join-Path $taskTarget 'PhDexLab.exe'))) {Start-Process -FilePath (Join-Path $taskTarget 'PhDexLab.exe') -WorkingDirectory $taskRoot -WindowStyle Hidden}
    } catch {$taskError+='; rollback: '+$_.Exception.Message}
    Write-Receipt 'failed' $taskError
    exit 1
}
