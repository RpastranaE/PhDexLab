# PhDexLab 0.9.0

Install **PhDexLab-Setup-0.9.0.exe** or update from 0.8.0. Users still on 0.7.0 need a one-time manual installer upgrade. Excel and OriginPro are separate requirements. This remains a personal AI-assisted project.

- Start and close with an empty workspace. Add your first assay explicitly; no FRAP method is selected automatically.
- Distinct icons for duplicating an assay and saving a reusable protocol variant.
- Help opens once on first real launch, with 24 real application screenshots across 12 topics in English and Spanish. Health checks do not consume this onboarding state.
- Excel-style cells: one click selects, typing starts editing, F2 or double-click edits existing content. Reading-type lists remain available with one click.
- Detect an open or opening workbook before starting a worker. Backend checks also catch later file-sharing conflicts, with a save-and-close-workbook message. User Excel sessions and unsaved changes are never closed automatically.
- A simpler update dialog: version, GitHub link, automatic-update option and progress. Download progress stays in that dialog; the main window retains analytical calculation progress.

Validated with 127 automated checks, including keyboard interaction, empty-state transitions, first-use persistence, bilingual screenshots, Windows file sharing and update-dialog behaviour. Native Excel/Origin and frozen installer checks are recorded in the validation notes.
