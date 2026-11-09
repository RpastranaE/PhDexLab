param([string]$Compiler = 'ISCC.exe')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath Application/PhDexLab.exe)) { throw 'Run Build-Windows.ps1 first.' }
& $Compiler installer/PhDexLab.iss
if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed.' }
Write-Host 'Installer is in the parent directory.'
