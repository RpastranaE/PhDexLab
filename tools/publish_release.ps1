param([Parameter(Mandatory=$true)][string]$Version,[Parameter(Mandatory=$true)][string]$Package,[Parameter(Mandatory=$true)][string]$Notes)
$ErrorActionPreference='Stop'
if ($Version -notmatch '^\d+\.\d+\.\d+$') {throw 'Use major.minor.patch'}
$taskRepo=Split-Path -Parent $PSScriptRoot
$taskOrigin=(& git -C $taskRepo remote get-url origin)
if ($taskOrigin -notin @('https://github.com/RpastranaE/PhDexLab.git','https://github.com/RpastranaE/PhDexLab','git@github.com:RpastranaE/PhDexLab.git')) {throw 'Wrong repository'}
if (& git -C $taskRepo status --porcelain --untracked-files=no) {throw 'Commit reviewed source changes before publishing'}
$taskPackage=Get-Item -LiteralPath $Package
if ($taskPackage.Name -ne 'PhDexLab-Windows-x64.zip') {throw 'Incorrect asset name'}
$taskChecksums=Join-Path $taskPackage.Directory.FullName 'SHA256SUMS.txt'
if (-not (Test-Path -LiteralPath $taskChecksums)) {throw 'Missing checksum file'}
$taskExpected=((Get-Content -LiteralPath $taskChecksums -Raw).Trim() -split '\s+')[0]
if ((Get-FileHash -LiteralPath $taskPackage.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskExpected) {throw 'Package checksum mismatch'}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$taskZip=[IO.Compression.ZipFile]::OpenRead($taskPackage.FullName)
try {
    $taskEntry=$taskZip.GetEntry('release.json')
    if (-not $taskEntry) {throw 'Missing release manifest'}
    $taskReader=New-Object IO.StreamReader($taskEntry.Open())
    try {$taskManifest=$taskReader.ReadToEnd() | ConvertFrom-Json} finally {$taskReader.Dispose()}
    if ($taskManifest.version -ne $Version -or $taskManifest.repository -ne 'RpastranaE/PhDexLab') {throw 'Package version/repository mismatch'}
} finally {$taskZip.Dispose()}
& git -C $taskRepo tag -a "v$Version" -m "PhDexLab $Version"
if ($LASTEXITCODE -ne 0) {throw 'Could not tag release'}
& git -C $taskRepo push origin "v$Version"
if ($LASTEXITCODE -ne 0) {throw 'Could not push tag'}
& gh release create "v$Version" $taskPackage.FullName $taskChecksums --repo RpastranaE/PhDexLab --title "PhDexLab $Version" --notes-file $Notes --verify-tag
if ($LASTEXITCODE -ne 0) {throw 'Release creation failed'}
