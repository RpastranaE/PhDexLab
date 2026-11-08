$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    try { $taskPython = (& py -3.12 -c 'import sys;print(sys.executable)' 2>$null) } catch { $taskPython = $null }
}
if (-not $taskPython -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $taskPython = (Get-Command python).Source
}
if (-not $taskPython) { throw 'Instala Python 3.12 de 64 bits y vuelve a abrir PhDexLab.bat.' }
& $taskPython -I -c 'import sys;assert (3,11)<=sys.version_info[:2]<(3,14) and sys.maxsize>2**32'
if ($LASTEXITCODE -ne 0) { throw 'Version de Python incompatible' }
& $taskPython -I -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno' }
& '.\.venv\Scripts\python.exe' -I -m pip install --isolated -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron descargar las dependencias. Revisa la conexion a Internet.' }
Write-Host 'Instalacion terminada. Iniciando PhDexLab...'
