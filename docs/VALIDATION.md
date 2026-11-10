# Validation evidence

[Documentation index](README.md) · [Current user manual](MANUAL.md) · [Development](DEVELOPMENT.md)

Software verification with synthetic data is not analytical validation of a chemical method or matrix. The operator must review conditions, units and experimental independence.

## 0.10.1 libraries, result precision and figure exports

- The full suite passed **224 tests**. After the final compact-summary changes, **58 focused regressions passed**, including readiness counters, both languages/themes, one-time update notes, first-install Help, library operations and source optionality.
- The **24 native Excel equation cases covering all 15 catalogue variants** passed again. Calculations are unchanged; result rounding is display-only, and Excel numeric formatting now uses General rather than a fixed four-decimal mask.
- Library tests verify confirmed deletion, cancellation, stale-file protection, hiding/restoring bundled variants, user-data isolation and preservation of open assays, RAW observations and saved workbooks.
- Independent display cases check two significant figures for SD, matching mean precision, carry, small/large and negative numbers, zero SD and unavailable SD. Full values remain in saved Excel and result tooltips.
- A native source run of FRAP, ABTS, DPPH and adapted TPC produced **24 Origin + 24 Publication exports**, with blank protocol source accepted and unknown precision/no-marker styles preserved. Eight graphs had exactly two title-overline paths removed each; original SVGs were archived. SVG tests protect plot groups, fit lines and unrelated annotations and verify idempotence.
- Export cleanup applies to SVG/PNG/PDF and app previews; the editable Origin project may retain the local native rendering defect. It is not represented as a verified native Origin font-format repair.
- The exact final frozen executable repeated the four-assay native run: **24 Origin + 24 Publication exports**, all expected means, no-marker settings and unknown precision retained. It took 82.64 s while packaging ran concurrently; an integrity-verified unchanged repeat took 1.17 s. These fixture measurements are not performance guarantees. All four Results views matched display-rounded saved means/SDs and verified images.
- The compiled module inventory and bundled assets matched final source. Frozen startup passed. A real frozen normal launch consumed the pending version notes; its health check left those notes unseen.
- The exact installer passed an isolated installation, desktop/menu shortcuts and frozen startup. An isolated **0.10.0 → 0.10.1** update using the exact ZIP passed startup, retained 24 help images and preserved experiment/style sentinels and the pending version-notes state.


- After publication, all four GitHub asset SHA-256 digests matched the tested local files. The installed 0.10.1 executable verified HTTPS and reported itself current; the 0.10.0 executable detected 0.10.1 as newer. Isolated uninstallation removed its managed shortcuts and retained experiment/style sentinels.

## 0.10.0 input validation and final results

- **204 automated tests passed**, including delayed missing-cell highlighting, clearing highlights after correction, multi-assay issue locations, zero/false values, optional mean precision, autosave of dirty tables and the active cell editor, cancellation of first-save dialogs, protection against external workbook changes, explicit partial-export choice and stale-result/figure checks. The GUI test harness now destroys test windows between cases so old Qt event filters/timers cannot be collected inside a later modal loop.
- The **24 native Excel equation cases covering all 15 catalogue variants** were repeated successfully. No chemistry equations were added to the results view.
- A source GUI integration test saved an incomplete draft, displayed the real issue dialog without starting a worker, corrected the field, and exported through real Excel and Origin. An active cell editor's text persisted in the workbook before native processing. The final cards exactly matched saved Excel values, with **3 sample cards and 2 verified Origin previews**.
- Bilingual results/validation screens, dark appearance and DPPH dose-response previews were captured with synthetic data. Updated help screenshots render at 3000 × 2000; figure previews retain device pixel density and the enlargement viewer reads original files.
- After the final visual cleanup/high-DPI changes, all **13 focused 0.10.0 regressions passed**. Switching assays hides old widgets immediately, before deferred destruction, so previous figures cannot remain behind new results.
- The exact frozen executable generated FRAP, ABTS, DPPH and adapted TPC through real Excel/Origin, producing **24 Origin + 24 Publication exports** with expected means, unknown precision and no-marker styles preserved. The local fixture took 72.39 s while packaging was also running; an unchanged integrity-verified repeat took 1.42 s. These are fixture measurements, not performance guarantees.
- All four resulting assay views matched the exact saved Excel values and displayed two verified Origin previews each. The compiled module inventory and bundled assets matched final source, and frozen GUI startup passed.
- An isolated **0.9.3 → 0.10.0** update using the exact release ZIP passed frozen startup, retained 24 help images and preserved sentinel experiment/style files.
- The exact installer passed an isolated installation with desktop/menu shortcuts pointing to the installed executable; its frozen GUI startup passed.
- After publication, all four GitHub asset SHA-256 digests matched the tested local artifacts. The installed 0.10.0 executable verified HTTPS and reported itself current; the 0.9.3 executable detected 0.10.0 as newer. Isolated uninstallation removed the managed shortcuts and preserved sentinel experiment/style files.

## 0.9.3 calculation audit

- **191 automated tests passed** after the calculation/validation changes. Additional regressions cover several dilutions within one independent extraction, rejection of ambiguous mass-bearing control rows, dimensional unit guards, the TFC mass basis, explicit DPPH adaptation and the visible normalisation chain.
- **24 native Microsoft Excel equation cases cover all 15 catalogue variants**, with independent dimensional factors. All eight optical variants were checked on both before-reaction and final-mixture axes, with a nonzero fitted intercept, measured blank/sample background, two prior dilutions per extraction and two independent extractions. Final values, biological n/SD and 90% control recovery matched independent expectations. No unexpected Excel formula errors were found.
- Gravimetric checks include moisture, complementary dry matter and ash on initial/dry bases. Two incomplete TAPPI variants remain blocked in the catalogue; only explicitly labelled software-test operating conditions were used to exercise their equations. DPPH EC50 interpolation and 98% sieve mass recovery also matched independent values.
- The local FRAP reference cross-check regressed **raw observations independently**, without reading cached coefficients or expected results. All **nine extraction means and within-unit SDs** matched the generated Excel. Six readings at two dilutions remain one extraction, with biological n=3 per lot. The manufacturer source was separately reviewed; a sample-example transcription discrepancy and rounding differences are documented in [Protocol sources](PROTOCOL_SOURCES.md).
- These checks establish numerical behaviour for stated inputs, not analytical validity, sample extraction recovery or the cause of an unprovided app-generated workbook's exact cell. See the auditable method/units review before interpreting scientific results.

- The native individual/known-mean/unknown-mean comparison was repeated: **216 biological-summary comparisons across 10 methods and 3 additional variants passed**, including technical SD scaling and direct-delta/paired FRAP equivalence.

- The final **frozen 0.9.3 executable** reproduced the local FRAP case through real Excel and Origin (9 extraction results, 3 biological units per lot, 6 Origin + 6 Publication exports). On a disposable copy, doubling prior dilution or extract volume doubled the per-reading result; doubling mass halved it, with interpolated concentration unchanged. The native exported calculation header layout was visually reviewed.
- A separate frozen four-assay test (FRAP, ABTS, DPPH, adapted TPC) generated **24 Origin + 24 Publication exports**, preserved unknown precision and no-marker styles, and completed in 63.33 s locally. An integrity-verified unchanged repeat took 1.03 s. These fixture timings are not a general performance guarantee.
- The exact installer passed isolated desktop/menu shortcuts and startup checks. The installed executable, bundled resources and compiled modules matched the final source/build.

- An isolated **0.9.2 → 0.9.3** update installed the exact release ZIP, passed frozen startup, retained 24 help images and preserved sentinel experiment/style files.

- After publication, all four GitHub asset digests matched the tested local artifacts. The installed 0.9.3 binary verified HTTPS and reported itself current; the 0.9.2 binary detected 0.9.3 as newer. The isolated installer was then removed; its managed shortcuts were removed and sentinel user files were retained.

## 0.9.2 verification

- **181 automated tests passed.** Coverage includes all 15 catalogue variants, context-specific fields, individual/mean exclusivity, optional known precision, meaningful unknown precision, variable counts, unused entry slots, legacy template/input activation, explicit blank modes, signal-change protection, lossless switching between old/new variants, calibration minimums and prevention of provenance loss through the legacy writer.
- The explicit native Excel comparison covered **10 methods + 3 additional variants**, with **216 biological-summary comparisons** across individual readings, means with precision and means without precision. Independent expected means matched; supplied technical SD matched the individual-reading result; unknown n/SD remained `#N/A`. Direct ΔA matched paired FRAP results. The rerunnable case is `tests/native_reading_validation.py`.
- The final **frozen 0.9.2 executable** processed four assays (FRAP, ABTS, DPPH and adapted TPC), including one calibration mean without n/SD and DPPH means without technical precision. It produced **24 Origin + 24 Publication exports**. Native values/styles were read back, no-marker options remained applied, expected biological means matched, unknown precision stayed unavailable, and captions retained mean provenance.
- That four-assay frozen run took 89.33 s while packaging was also running; an integrity-verified unchanged repeat took **1.49 s**, including process startup. These are local fixture timings, not a general speed guarantee.
- The exact installer passed isolated installation, desktop/menu shortcut and frozen-startup checks. An actual isolated 0.9.1 Application was replaced using the release ZIP; startup passed and sentinel experiment/preferences files were preserved. The compiled module inventory matched source.
- After publication, all four asset SHA-256 digests matched the corrected tested packages. The installed 0.9.2 binary verified HTTPS and reported itself current; the 0.9.1 binary reported 0.9.2 as newer. Isolated uninstallation removed managed shortcuts and preserved sentinel experiment/style files.
- Catalogue version 3 changes the new adapted TPC default to 760 nm, matching the available operating protocol. Older saved protocol snapshots remain unchanged. The 14 supplied operating protocols plus the existing TFC reference were reviewed for required entries; this is not experimental validation of their transfer to a matrix. TAPPI conditions remain pending.

## 0.9.1 verification

- **141 automated tests passed.** New regressions cover clearing cells, cut/copy/paste, atomic rejection of invalid pasted roles, row insertion/deletion, fresh IDs for pasted rows, update timing choices, restart scheduling, unsaved-work cancellation, first-save choices, image zoom and credits.
- The final frozen executable generated the consolidated FRAP/DPPH workbook/project and **12 Origin + 12 Publication exports**, with native value and style readback. An unchanged verified repeat took **1.13 s**, including process startup, on the test machine.
- A second frozen refresh changed the existing styled project to **No markers** in all three roles: all four native plots read back as symbol 0, all 24 exports were present, and captions explicitly described hidden biological-unit markers. Error bars and connecting/fitted lines remained visible.
- All 24 bilingual help screenshots were recaptured at twice their previous pixel resolution. The image viewer retains originals and supports fit-to-window and 100% zoom.
- The exact installer was tested in a separate installation identity with isolated desktop/menu destinations. Both shortcuts and frozen startup passed. An isolated actual 0.9.0 Application was upgraded using the release ZIP; the new health check passed and sentinel experiment/preferences files were unchanged.
- Windows executable fixtures verified successful installation **and relaunch**, plus failed health-check rollback **and relaunch of the previous application**. These fixtures are separate from native analytical tests and do not operate a user's running session.
- Excel writing was benchmarked on the same synthetic 1,200-reading input before/after replacing repeated worksheet-size scans with explicit row indices: **12.54 s → 4.76 s**. Every worksheet's values and formula strings matched. This measures workbook construction, not total Excel/Origin/export time, and is not a performance guarantee.
- After publication, all four GitHub asset sizes/SHA-256 digests matched the tested local files. The actual installed 0.9.1 binary verified HTTPS and reported 0.9.1 as current; the 0.9.0 binary reported it as newer. The isolated installer was then uninstalled: managed shortcuts were removed while sentinel experiment and personal-style files remained unchanged.
- The final compiled Python module inventory matched the reviewed source. ZIP staging, installer identity and user-data preservation remain part of the checks. See below for earlier evidence and practical limits.

## 0.9.0 evidence retained

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
