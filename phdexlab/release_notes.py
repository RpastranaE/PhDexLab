"""Offline, bilingual release highlights shown once after a version change."""
import html,json
from PySide6.QtWidgets import QDialog,QVBoxLayout,QTextBrowser,QDialogButtonBox
from . import __version__,i18n
from .data_templates import user_data_dir
from .integration import dump
from .updater import version,REPO_URL

NOTES={
    'es':[
        'Importación: reconoce Patrón, Blanco, Muestra y Control en español e inglés.',
        'Los errores indican fila, campo y una corrección breve.',
        'Los campos de importación se adaptan a la señal y las condiciones del protocolo.',
        'Arrastra encabezados o columnas hasta su campo de destino, o utiliza las listas.'
    ],
    'en':[
        'Import recognises short Spanish and English names for standards, blanks, samples and controls.',
        'Errors identify the row, field and a short suggested fix.',
        'Import fields follow the protocol signal and conditions.',
        'Drag headers or columns onto their destination field, or use the lists.'
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
