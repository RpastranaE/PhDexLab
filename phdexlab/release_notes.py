"""Offline, bilingual release highlights shown once after a version change."""
import html,json
from PySide6.QtWidgets import QDialog,QVBoxLayout,QTextBrowser,QDialogButtonBox
from . import __version__,i18n
from .data_templates import user_data_dir
from .integration import dump
from .updater import version,REPO_URL

NOTES={
    'es':[
        'Repeticiones: numeración automática y creación de nuevas filas sin copiar las absorbancias.',
        'Edición de celdas: arrastrar series, sugerencias de nombres, rellenar abajo/derecha y deshacer/rehacer.',
        'Excel: un resumen completo y dos pestañas por ensayo. Los cálculos y resultados quedan juntos.',
        'Estilos de Excel: paletas editables, tipografía, altura de filas y plantillas personales reutilizables.',
        'Los experimentos anteriores se pueden abrir. Al guardar o actualizar se adopta el nuevo formato; el Excel anterior queda en el historial. El formato agrupado requiere 0.11.0 o posterior.'
    ],
    'en':[
        'Repeated readings: automatic numbering and new rows without copying absorbance measurements.',
        'Spreadsheet editing: drag to fill series, name suggestions, fill down/right and undo/redo.',
        'Excel: one complete overview and two sheets per assay, with calculations and results together.',
        'Excel styles: editable palettes, fonts, row heights and reusable personal presets.',
        'Existing experiments can be opened. Saving or updating adopts the new layout and keeps the previous workbook in history. The compact layout requires 0.11.0 or later.'
    ]}


def show_after_update(window):
    path=user_data_dir()/'onboarding.json'
    try:data=json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):return False
    if not data.get('help_seen'):return False
    previous=data.get('last_version')
    if previous:
        try:
            if version(previous)>=version(__version__):return False
        except (TypeError,ValueError):pass
    es=i18n.LANGUAGE=='es';dialog=QDialog(window);dialog.resize(660,530)
    dialog.setWindowTitle('Novedades de PhDexLab' if es else "What's new in PhDexLab")
    layout=QVBoxLayout(dialog);browser=QTextBrowser();browser.setOpenExternalLinks(True)
    title=('Novedades de la versión ' if es else "What's new in version ")+__version__
    body='<h2>'+html.escape(title)+'</h2><ul>'+''.join('<li><p>'+html.escape(note)+'</p></li>' for note in NOTES['es' if es else 'en'])+'</ul>'
    body+='<p><a href="'+REPO_URL+'/releases/tag/v'+__version__+'">'+('Ver la versión y el historial en GitHub' if es else 'View the release and history on GitHub')+'</a></p>'
    browser.setHtml(body);layout.addWidget(browser)
    buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
    buttons.button(QDialogButtonBox.StandardButton.Close).setText('Cerrar' if es else 'Close')
    window.whats_new_dialog=dialog;dialog.show()
    data['last_version']=__version__;dump(path,data)
    return True


def show_on_launch(window):
    from .onboarding import show_on_first_use
    if show_on_first_use(window):return
    show_after_update(window)
