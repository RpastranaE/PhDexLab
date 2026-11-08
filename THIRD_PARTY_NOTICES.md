# Third-party notices

PhDexLab's original source code is MIT-licensed. It uses third-party software whose licences remain in force. This file is not a replacement for those licences.

- Python: Python Software Foundation licence and its included third-party notices.
- Qt/PySide6 Essentials and Shiboken6: used under LGPLv3. These are dynamically loaded libraries, kept as separate DLL/PYD files in the onedir distribution. No modifications to Qt or PySide are made. Users may replace compatible libraries, inspect and modify this application, and rebuild it from public source. Reverse engineering for debugging modifications to LGPL libraries is not restricted by this project. Disable app updates to retain modified libraries.
- openpyxl: MIT; Matplotlib and its dependencies: their included licences; SciencePlots: MIT.
- OriginPro Python and OriginExt: OriginLab's redistribution notices are included; this does not grant a licence for OriginPro itself.
- pywin32, NumPy, Pillow, contourpy, cycler, fonttools, kiwisolver, packaging, pyparsing, python-dateutil and six: their respective included notices.
- PyInstaller: GPL with the bootloader exception permitting distributions built with it.
- Bundled toolbar assets: Lucide ISC licence in `phdexlab/assets/toolbar/LICENSE-Lucide.txt`. Theme, template, palette and update symbols follow the same geometry and were authored for this project.

The Windows package contains `Application/THIRD_PARTY_LICENSES`, including package notices and LGPL/GPL texts. Windows fonts are referenced from the system and not redistributed. Microsoft Excel and OriginPro are separate, user-installed commercial products.

Qt sources: https://download.qt.io/official_releases/qt/ and https://code.qt.io/cgit/qt/qtbase.git/ . PySide/Shiboken sources: https://code.qt.io/cgit/pyside/pyside-setup.git/ . Use the version named in `requirements.txt` and the corresponding release tag. The package inventory records exact dependency versions. Application source and build instructions: https://github.com/RpastranaE/PhDexLab .
