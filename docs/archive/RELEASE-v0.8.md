> **Archivo histórico.** Este texto describe una versión concreta y puede contener instrucciones superadas. Para descargar y utilizar la aplicación actual, consulta el [manual vigente](../MANUAL.md). El [historial de cambios](../../CHANGELOG.md) explica la evolución.

# PhDexLab 0.8.0

Install **PhDexLab-Setup-0.8.0.exe**. It includes Python and application dependencies, creates desktop/Start menu shortcuts and an uninstaller. Excel and OriginPro remain separate requirements. English is the first-run default; existing preferences are preserved.

**For 0.7.0 users:** download and run this installer once. The 0.7.0 updater was missing a CA-policy runtime file and could report `[Errno 2] No such file or directory`. This release includes that file without disabling TLS checks. Subsequent updates can use the normal automatic-update channel.

Changes:
- Results, calibration and dose-curve previews now use the real plotting renderer and show palette, marker, line, error-bar and typography changes.
- Built-in protocol text and condition values follow the chosen language; custom text and archived experiment snapshots remain intact. Catalogue names/status no longer say BORRADOR; incomplete procedures still require their missing conditions.
- Source links open the corresponding original publications. Font family and source-reference translations use distinct contexts.
- Choosing the empty Reading type clears the whole reading row.
- Figures opens the root until genuine figures exist; a single assay with exports can open directly.
- A single Save variant action remains next to Variant; the other action opens protocol conditions for editing.
- Hover descriptions cover toolbar and dialog actions. Replaced protocol-help widgets no longer overlap.
- Update checks can fall back to public release metadata when GitHub limits anonymous API requests. Downloads keep SHA-256/inventory checks, isolated staging, startup verification and rollback.

This is a personal AI-assisted project. The application and installer are unsigned. Reference protocols and software checks do not constitute analytical validation for any sample matrix. See the repository validation notes for the tested local configuration and practical limits.
