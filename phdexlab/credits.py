"""User-facing attribution and local redistribution licences."""
import sys
from pathlib import Path
from PySide6.QtCore import QUrl
from . import i18n,__version__

def topic():
    root=Path(sys.executable).parent/'THIRD_PARTY_LICENSES' if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]
    url=QUrl.fromLocalFile(str(root)).toString()
    common=f'<p>PhDexLab {__version__} · RpastranaE</p><p><a href="https://github.com/RpastranaE/PhDexLab">GitHub</a> · <a href="mailto:rpe10@alu.ua.es">rpe10@alu.ua.es</a></p>'
    if i18n.LANGUAGE=='en':
        return ('13 · Credits and licences',common+f'<h2>Personal project</h2><p>Developed with AI assistance (ChatGPT/Codex). No official affiliation with OpenAI, Microsoft or OriginLab.</p><h2>Licences</h2><p>PhDexLab source code: MIT. PySide6/Qt: LGPL/GPL/commercial terms as applicable; this distribution uses dynamically linked Qt libraries. NumPy, SciPy, Matplotlib, openpyxl, SciencePlots, PyInstaller, pywin32 and the Origin automation libraries retain their respective licences and notices.</p><p><a href="{url}">Open included licence texts and third-party notices</a></p><p>Microsoft Excel and OriginPro are independent products requiring their own licences. Software verification does not validate an analytical method or sample matrix.</p>')
    return ('13 · Créditos y licencias',common+f'<h2>Proyecto personal</h2><p>Desarrollado con asistencia de IA (ChatGPT/Codex). Sin afiliación oficial con OpenAI, Microsoft u OriginLab.</p><h2>Licencias</h2><p>Código de PhDexLab: MIT. PySide6/Qt: condiciones LGPL/GPL/comerciales según corresponda; esta distribución utiliza bibliotecas Qt enlazadas dinámicamente. NumPy, SciPy, Matplotlib, openpyxl, SciencePlots, PyInstaller, pywin32 y las bibliotecas de automatización de Origin conservan sus respectivas licencias y avisos.</p><p><a href="{url}">Abrir textos de licencias y avisos de terceros incluidos</a></p><p>Microsoft Excel y OriginPro son productos independientes y requieren sus propias licencias. La verificación informática no valida el método analítico ni su aplicación a una matriz.</p>')
