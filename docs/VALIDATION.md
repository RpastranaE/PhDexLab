# Validation evidence — 0.9.0

[Documentation index](README.md) · [Current user manual](MANUAL.md) · [Development](DEVELOPMENT.md)

This page records checks performed for the stated release; it is not a second installation or usage guide.

This is software verification with synthetic data, not analytical validation of a chemical method or matrix. Protocol conditions and independence of biological units remain the operator's responsibility.

## Automated checks

**127 tests passed** in the release source. The final frozen FRAP/DPPH refresh completed in 42.32 seconds on the test machine; a verified unchanged repeat took 0.73 seconds including process startup. These are local measurements for this two-assay fixture, not a general performance guarantee.

The pytest suite checks analytical input rules, formula generation, independent expected results, traceability, workbook round trips, assay isolation, incomplete protocols, technical/biological replicates, data templates, language/theme changes, graphical settings and cache invalidation. Update checks cover numeric version ordering, the expected GitHub release/repository, digests, download corruption, unsafe/duplicate paths, symlinks, manifest/version mismatch, disabled automatic downloads and unsaved-work cancellation.

Old presentation schema 1 retains its original appearance settings. Schema 2 records independent result/calibration/dose settings and invalidates presentation caches when a field changes. Saved personal styles contain no experimental data. Exponent conversion prevents missing Unicode superscript-minus glyphs in Windows fonts.

## Native Windows checks

Tested locally on Windows 11 x64 with desktop Excel and OriginPro 2024 (`@V = 10.100178`). FRAP and kinetic DPPH synthetic experiments exercise three varieties, technical/biological grouping, one consolidated workbook, one Origin project, separate assay folders and editable plots. Excel values are read back from Origin and compared before export. Colour, symbol and line settings are also read back. Native plot rendering is visually inspected because a successful property assignment alone does not prove the correct appearance.

The frozen executable is tested independently of source mode: GUI startup, FRAP/DPPH calculation, Origin connection/export, Publication export, and unchanged-result reuse. Figures are exported as PNG/PDF/SVG. The final compiled module inventory is compared against source to detect stale build caches.

The graph-script checker reports no plotting configuration issues. The SVG heuristic flags the rotated Y-axis title as potential overflow because its bounding-box estimate does not account for rotation; inspection of the actual rendered figure confirms the title fits. Publication figures retain editable SVG text and vector PDF output. Origin-native text decorations and rendering can vary with installed templates/fonts; inspect exported native figures before submission and use the Publication alternative when needed. Custom colours do not automatically guarantee accessibility, contrast or journal compliance.

## Updater checks

The exact release ZIP is verified and staged in a separate disposable installation. The installer waits for a real frozen executable to exit, replaces only Application, passes the new executable's isolated startup health check and removes its backup after success. A sentinel experiment outside Application and personal style settings remain byte-for-byte unchanged.

Separate Windows executable fixtures exercise successful installation and forced health-check failure. The latter restores the previous executable and reports failure. Neither test touches a user's experiment or an existing Excel/Origin session. Network access is tested against the actual public GitHub release after publication; releases without the expected asset or GitHub digest are refused.

## Practical limits

- Tests apply to the stated local installation, not every Windows/Office/Origin build. No automated Excel↔Origin synchronisation or portable relative connector paths are claimed.
- Automatic updates require a writable installed or portable application, network access, PowerShell and a stable release with its SHA-256 digest. Version 0.7.0 users must install the latest version once manually to repair its missing TLS-policy file.
- Hashes verify integrity, not publisher identity through Authenticode. The executable is unsigned.
- Rollback cannot guarantee recovery from power loss, disk failure or external antivirus removal. Keep independent backups of experiments.
- No automatic significance tests, outlier exclusion or declaration of experimental method validity are performed.

## Version 0.8.0 regressions

New checks cover first-run English and saved preferences, protocol translation without input mutation, original DOI links, empty reading-type deletion, one Save variant action, visible hover descriptions, and image differences for result/calibration/dose controls and typography. Protocol widgets are also inspected visually after switching methods. The frozen module inventory matches all release Python modules.

The single-file Inno installer was installed into a disposable workspace folder. Desktop and Start menu shortcut targets were checked, and the installed executable passed its isolated GUI health check. The exact update ZIP then replaced Application successfully and passed the frozen health check while preserving sentinel experiment and personal-style files. Installer tests redirect shortcuts into disposable test folders.

The 0.7.0 frozen TLS failure was reproduced independently. Its Python runtime expected `codex-rejected-cas.pem` adjacent to ssl.py, but the previous build omitted the file. The release conditionally bundles this public CA-policy sidecar without removing certificate checks or changing that runtime’s trust policy. Anonymous API quota failure has a separately validated public-release-metadata fallback.

After publication, the installed 0.8.0 executable successfully checked the actual public GitHub release (`tls_initialized: true`, `ok: true`, version 0.8.0). The anonymous API was quota-limited on this connection, so this also exercised the live public-metadata fallback. GitHub’s SHA-256 digests matched all four uploaded assets. The disposable installation was then uninstalled successfully: both shortcuts and the executable were removed, while the sentinel experiment and personal style remained unchanged.

## Version 0.9.0 regressions

The initial workspace contains no assay or protocol; closing returns to that state, and the first explicit assay is A01. Tests exercise repeated transitions, language changes while empty, distinct duplicate/save-variant icons, first-use help persistence, all 24 bilingual help images, real Qt mouse/keyboard events for select/type/F2 editing, asynchronous shell-open preflight and update progress confined to its own dialog. First-run onboarding is dispatched by the normal app launch path; health checks do not consume it.

Real Excel checks cover both an already-open workbook and a workbook opened after recalculation but before replacement. Both are blocked with the save-and-close-workbook message. The original workbook remains open and byte-for-byte unchanged. The latter leaves an actionable failed status and preserves the calculation history. Tests use dedicated synthetic workbooks and close only their own Excel instance.

The final frozen FRAP/DPPH run completed with 12 Origin and 12 Publication exports; native style values were read back. The module inventory matches release source, and all 24 help screenshots are present in the frozen payload. The single-file installer passed isolated installation, shortcut and frozen GUI checks. A real 0.8.0 Application copy was upgraded with the exact 0.9.0 release ZIP: startup passed, screenshots were present and experiment/style sentinels were unchanged. Installer verification uses its own InstallId and redirected desktop/menu folders so an existing real installation’s uninstall registration is preserved.

After 0.9.0 publication, the installed frozen 0.9.0 executable reported version 0.9.0 with TLS initialized and `ok: true`. The frozen 0.8.0 checker independently detected 0.9.0 with `newer: true`. All four uploaded asset digests matched their tested local files. The exact installer’s isolated uninstall registration was confirmed before removal; uninstall removed its executable and shortcuts while retaining the sentinel experiment and personal style.
