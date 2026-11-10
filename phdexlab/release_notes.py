"""Offline, bilingual release highlights shown once after a version change."""
import html,json
from PySide6.QtWidgets import QDialog,QVBoxLayout,QTextBrowser,QDialogButtonBox
from . import __version__,i18n
from .data_templates import user_data_dir
from .integration import dump
from .updater import version,REPO_URL

NOTES={
    'es':[
        'Gestiona y elimina plantillas de datos y variantes personales desde la biblioteca. Los protocolos incluidos pueden ocultarse y restaurarse sin afectar a experimentos guardados.',
        'El resumen de lecturas tiene contadores separados y un indicador verde cuando las entradas están listas para calcular.',
        'Resultados muestra media ± desviación estándar con cifras significativas coherentes y acceso directo a la carpeta de figuras. Excel conserva los valores completos.',
        'Las exportaciones y previsualizaciones de Origin corrigen las líneas espurias sobre los títulos; se conserva el SVG original. El defecto local puede permanecer dentro del proyecto editable de Origin.',
        'Unidad experimental / extracción sustituye a Unidad biológica. La ayuda explica muestras, preparaciones independientes y repeticiones de lectura.',
        'La fuente del protocolo es opcional. La ayuda aclara los papeles del patrón cero y el blanco de reactivos.',
        'Esta ventana de novedades aparece una sola vez después de actualizar.'
    ],
    'en':[
        'Manage and delete data templates and personal protocol variants in the library. Included protocols can be hidden and restored without changing saved experiments.',
        'The reading summary now has separate counters and a green indicator when inputs are ready to calculate.',
        'Results shows mean ± standard deviation with consistent significant figures and direct access to the figures folder. Excel retains full values.',
        'Origin exports and previews remove spurious lines above axis titles and retain the original SVG. The local rendering defect may remain inside the editable Origin project.',
        'Experimental unit / extraction replaces Biological unit. Help explains samples, independent preparations and repeated readings.',
        'The protocol source is optional. Help clarifies the roles of the zero standard and reagent blank.',
        'These release notes appear only once after an update.'
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
