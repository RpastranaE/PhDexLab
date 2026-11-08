param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
try {
    $taskExe = Join-Path $PSScriptRoot 'Application/PhDexLab.exe'
    if (Test-Path -LiteralPath $taskExe) {
        if ($CheckOnly) { Write-Output 'READY: portable executable'; exit 0 }
        Start-Process -FilePath $taskExe -WorkingDirectory $PSScriptRoot
        exit 0
    }
    $taskPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
    $taskReady = $false
    if (Test-Path -LiteralPath $taskPython) {
        & $taskPython -c 'import PySide6.QtWidgets,openpyxl,matplotlib,scienceplots,win32com.client,originpro' 2>$null
        $taskReady = ($LASTEXITCODE -eq 0)
    }
    if ($CheckOnly) {
        if ($taskReady) { Write-Output 'READY: Python environment'; exit 0 }
        Write-Output 'SETUP REQUIRED: first launch will install dependencies'; exit 2
    }
    if (-not $taskReady) {
        Write-Host 'Preparando PhDexLab para el primer inicio...'
        & (Join-Path $PSScriptRoot 'Install.ps1')
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo completar la instalacion.' }
    }
    $taskPythonw = Join-Path $PSScriptRoot '.venv/Scripts/pythonw.exe'
    Start-Process -FilePath $taskPythonw -ArgumentList @('-m','phdexlab') -WorkingDirectory $PSScriptRoot
} catch {
    Write-Host ('No se pudo iniciar PhDexLab: ' + $_.Exception.Message) -ForegroundColor Red
    Read-Host 'Pulsa Intro para cerrar'
    exit 1
}
