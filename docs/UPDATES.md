# Releases and updates

Only public stable releases from `RpastranaE/PhDexLab` are accepted. The application uses GitHub's unauthenticated HTTPS releases API, checks numeric `major.minor.patch` versions and rejects draft/prerelease metadata, unexpected repositories and missing digests.

`PhDexLab-Windows-x64.zip` contains `Application/**` and `release.json` only. The manifest declares the repository, version and SHA-256 for every payload file. GitHub's asset digest verifies the outer ZIP; the inventory verifies each expanded file. No tokens are embedded in the app. Hashes provide integrity, not publisher code signing.

The downloader has size/time limits and restricted destinations. ZIP staging rejects traversal, duplicate/case-colliding paths, symlinks, Windows reserved names and files outside Application. The existing installation and experiments are untouched during download/staging. Only a writable portable installation can update itself.

On normal exit, after pending analytical work finishes and unsaved edits are resolved, a bundled PowerShell helper waits for the app process, renames Application to a backup, moves in the verified stage and runs the new executable's isolated health check. Successful startup removes the backup and relaunches the app. Failure attempts rollback and records details. A sudden power loss, disk failure, antivirus quarantine or OS restrictions can still require manual recovery; do not treat any updater as an experiment backup. User data live outside Application. The app does not force-close documents or user sessions of Excel/Origin.

The checkbox in the update window disables automatic checking/downloads and installation of a prepared update; manual checks remain available. If disabled, any prepared stage is discarded on exit. Source mode checks releases but does not overwrite Python environments.

## Publishing a later release

1. Update both version fields, source/docs and tests. Keep versions numeric and stable.
2. On Windows with Python 3.12, run `Install.ps1`, install pytest, and run the tests. Validate native Excel/Origin workflows with synthetic data on the target versions.
3. Run `Build-Windows.ps1`, then `.venv/Scripts/python.exe tools/package_windows.py`. Check the executable, health check and staged installer/rollback before publishing.
4. Commit the reviewed source in the public repository. Never add experiments, credentials, private source snapshots, local logs or build environments.
5. Authenticate with official GitHub CLI. Run `tools/publish_release.ps1 -Version X.Y.Z -Package <path-to-PhDexLab-Windows-x64.zip> -Notes <release-notes.md>`.
6. Confirm the release is public/stable, GitHub has supplied a SHA-256 digest for the asset, and the app check returns that release. Releases lacking a digest are deliberately refused.

The first public version has no preceding public binary with an updater. It must be downloaded once; subsequent compatible releases can use this channel. Updating analytical software never retrospectively changes the recorded protocol snapshots or automatically recalculates saved experiments.
