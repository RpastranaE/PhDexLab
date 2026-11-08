# Validation scope — 0.7.0

This is software verification with synthetic data, not analytical validation of a chemical method or matrix. Protocol conditions and independence of biological units remain the operator's responsibility.

## Automated checks

**93 tests passed** in the curated public source checkout. The final frozen FRAP/DPPH refresh completed in 41.22 seconds on the test machine; a verified unchanged repeat took 1.05 seconds including process startup. These are local measurements for this two-assay fixture, not a general performance guarantee.

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
- Automatic updates require a writable portable installation, network access, PowerShell and a stable release with its SHA-256 digest. The first public version must be installed once manually.
- Hashes verify integrity, not publisher identity through Authenticode. The executable is unsigned.
- Rollback cannot guarantee recovery from power loss, disk failure or external antivirus removal. Keep independent backups of experiments.
- No automatic significance tests, outlier exclusion or declaration of experimental method validity are performed.
