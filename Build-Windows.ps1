$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython=Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Prepara el entorno fuente con Install.ps1 primero.' }
& $taskPython -I -m pip install --isolated pyinstaller
if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar PyInstaller' }
$taskAssets=Join-Path $PSScriptRoot 'phdexlab/assets'
& $taskPython -I -m compileall -q -f phdexlab
# Some Python distributions require this adjacent public CA policy file.
# Preserve their TLS trust policy in the frozen executable as well.
$taskCa = & $taskPython -c "import ssl;from pathlib import Path;p=Path(ssl.__file__).with_name('codex-rejected-cas.pem');print(p if p.is_file() else '')"
$taskTlsArgs = @()
if ($taskCa) { $taskTlsArgs = @('--add-data', "$taskCa;.") }
& $taskPython -I -m PyInstaller @taskTlsArgs --clean --noconfirm --onedir --windowed --name PhDexLab --icon "$taskAssets/phdexlab.ico" --add-data "$taskAssets;phdexlab/assets" --collect-all originpro --collect-all OriginExt --collect-data scienceplots --hidden-import matplotlib.backends.backend_svg --hidden-import matplotlib.backends.backend_pdf --hidden-import phdexlab.__main__ --hidden-import phdexlab.diagnostics --hidden-import win32timezone --hidden-import pythoncom --hidden-import pywintypes --distpath build-output --workpath build-cache --specpath build-cache launcher.py
if ($LASTEXITCODE -ne 0) { throw 'No se pudo construir el ejecutable' }
New-Item -ItemType Directory -Force Application | Out-Null
Copy-Item -Path build-output/PhDexLab/* -Destination Application -Recurse -Force
# Qt on Windows uses the OS ICU. Do not ship an unrelated ICU found on the build host PATH.
Remove-Item -LiteralPath Application/_internal/icuuc.dll -ErrorAction SilentlyContinue
Remove-Item -LiteralPath Application/_internal/icudt78.dll -ErrorAction SilentlyContinue
Write-Host 'Ejecutable: Application/PhDexLab.exe'
