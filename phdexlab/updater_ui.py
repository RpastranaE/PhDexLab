"""Non-blocking update checks and downloads; never interrupt analytical work."""
import os,sys,tempfile,json,shutil
from pathlib import Path
from PySide6.QtCore import QObject,QThread,Signal,QTimer
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QCheckBox,QPushButton,QProgressBar,QDialogButtonBox
from . import __version__,updater
from .i18n import t,add

for pair in '''Actualizaciones de PhDexLab|PhDexLab updates
Buscar actualizaciones|Check for updates
Buscar e instalar automáticamente al cerrar|Check and install automatically on exit
Se conserva tu trabajo. La actualización solo reemplaza Application, comprueba SHA-256 y prueba el arranque; si falla, recupera la versión anterior.|Your work is preserved. Updates replace Application only, verify SHA-256 and test startup; failure restores the previous version.
Comprobando GitHub…|Checking GitHub…
Descargando actualización…|Downloading update…
Verificando actualización…|Verifying update…
Actualización preparada: se instalará al cerrar.|Update ready: it will install on exit.
Tienes la versión más reciente.|You have the latest version.
Actualización disponible. Activa las actualizaciones automáticas para descargarla.|Update available. Enable automatic updates to download it.
No se pudo comprobar o descargar la actualización. Puedes volver a intentarlo.|Could not check or download the update. You can try again.
La actualización automática está disponible en el ejecutable portátil de Windows.|Automatic updates are available in the installed Windows application.
Esperando a que termine la comprobación para cerrar…|Waiting for the update check to finish before closing…
Versión instalada|Installed version
Ver repositorio y versiones|View repository and releases
No se pudo preparar la instalación de la actualización.|Could not prepare the update installation.
Actualización cancelada.|Update cancelled.'''.splitlines():add(*pair.split('|',1))

class UpdateWorker(QThread):
    progress=Signal(int,str)
    completed=Signal(object,str)
    def __init__(self,root,automatic,parent=None):super().__init__(parent);self.root=root;self.automatic=automatic
    def run(self):
        staged=None
        try:
            self.progress.emit(1,'Comprobando GitHub…');release=updater.latest()
            if self.isInterruptionRequested():raise InterruptedError()
            if release['newer'] and self.automatic and self.root:
                directory=updater.user_data_dir()/'updates';directory.mkdir(parents=True,exist_ok=True)
                descriptor,path=tempfile.mkstemp(prefix='download-',suffix='.zip',dir=directory);os.close(descriptor);path=Path(path)
                def progress(value,phase):self.progress.emit(value,'Descargando actualización…' if phase=='download' else 'Verificando actualización…')
                try:
                    updater.download(release,path,progress,cancel=self.isInterruptionRequested)
                    if self.isInterruptionRequested():raise InterruptedError()
                    staged=updater.stage(path,self.root,release['version'],progress)
                finally:path.unlink(missing_ok=True)
            self.completed.emit(dict(release=release,stage=str(staged) if staged else None),'')
        except InterruptedError:self.completed.emit(None,'cancelled')
        except Exception as error:self.completed.emit(None,str(error))

class UpdateController(QObject):
    def __init__(self,window):
        super().__init__(window);self.window=window;self.worker=None;self.ready=None;self.closing=False;self.status='';self.detail='';self.percent=0;self.dialog=None
        self.root=Path(sys.executable).resolve().parent.parent if getattr(sys,'frozen',False) and Path(sys.executable).parent.name=='Application' else None
        heading=window.centralWidget().layout().itemAt(0).layout();self.button=window.make_button('Actualizaciones de PhDexLab',self.show_dialog,'update',heading)
        window.buttons.remove(self.button)
        self.bar=QProgressBar();self.bar.setRange(0,100);self.bar.setMaximumHeight(23);self.bar.hide();window.centralWidget().layout().addWidget(self.bar)
        self.timer=QTimer(self);self.timer.setInterval(6*60*60*1000);self.timer.timeout.connect(self.automatic_check)
        if self.root and not any(arg in sys.argv for arg in ('--smoke-test','--update-healthcheck')):
            QTimer.singleShot(4000,self.automatic_check);self.timer.start()
    def automatic_check(self):
        if updater.settings()['automatic'] and not self.ready:self.check()
    def check(self):
        if self.worker and self.worker.isRunning():return
        if self.ready:self.set_status(100,'Actualización preparada: se instalará al cerrar.');return
        self.detail='';self.worker=UpdateWorker(self.root,updater.settings()['automatic'],self);self.worker.progress.connect(self.set_status);self.worker.completed.connect(self.finished)
        self.worker.finished.connect(self.after_finished);self.worker.start()
    def set_status(self,value,text):
        self.percent=value;self.status=text;self.bar.setValue(value);self.bar.setFormat(t(text)+' · %p%');self.bar.setVisible(0<value<100 or bool(self.ready));self.button.setToolTip(t('Actualizaciones de PhDexLab')+'\n'+t(text));self.update_dialog()
    def finished(self,result,error):
        self.detail=error
        if error:self.set_status(0,'Actualización cancelada.' if error=='cancelled' else 'No se pudo comprobar o descargar la actualización. Puedes volver a intentarlo.');return
        if result.get('stage'):
            self.ready=Path(result['stage']);self.set_status(100,'Actualización preparada: se instalará al cerrar.')
        elif result['release']['newer']:self.set_status(0,'Actualización disponible. Activa las actualizaciones automáticas para descargarla.' if self.root else 'La actualización automática está disponible en el ejecutable portátil de Windows.')
        else:self.set_status(0,'Tienes la versión más reciente.')
    def after_finished(self):
        self.update_dialog()
        if self.closing:QTimer.singleShot(0,self.window.close)
    def update_dialog(self):
        if self.dialog:
            self.status_label.setText(t(self.status));self.detail_label.setText(self.detail);self.dialog_bar.setValue(self.percent);self.dialog_bar.setFormat(t(self.status)+' · %p%');self.dialog_bar.setVisible(0<self.percent<100)
            self.check_button.setEnabled(not (self.worker and self.worker.isRunning()))
    def show_dialog(self):
        if self.dialog:self.dialog.show();self.dialog.raise_();return
        dialog=QDialog(self.window);self.dialog=dialog;dialog.setWindowTitle(t('Actualizaciones de PhDexLab'));dialog.resize(610,300);layout=QVBoxLayout(dialog)
        layout.addWidget(QLabel(t('Versión instalada')+': '+__version__))
        link=QLabel(f'<a href="{updater.REPO_URL}/releases">{t("Ver repositorio y versiones")}</a>');link.setOpenExternalLinks(True);layout.addWidget(link)
        automatic=QCheckBox(t('Buscar e instalar automáticamente al cerrar'));automatic.setChecked(updater.settings()['automatic']);automatic.toggled.connect(updater.set_automatic);layout.addWidget(automatic)
        note=QLabel(t('Se conserva tu trabajo. La actualización solo reemplaza Application, comprueba SHA-256 y prueba el arranque; si falla, recupera la versión anterior.'));note.setWordWrap(True);layout.addWidget(note)
        self.status_label=QLabel();self.status_label.setWordWrap(True);layout.addWidget(self.status_label);self.detail_label=QLabel();self.detail_label.setWordWrap(True);self.detail_label.setTextInteractionFlags(self.detail_label.textInteractionFlags());layout.addWidget(self.detail_label)
        self.dialog_bar=QProgressBar();layout.addWidget(self.dialog_bar);self.check_button=QPushButton(t('Buscar actualizaciones'));self.check_button.clicked.connect(self.check);layout.addWidget(self.check_button)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);buttons.rejected.connect(dialog.close);layout.addWidget(buttons)
        dialog.finished.connect(lambda *args:setattr(self,'dialog',None));self.update_dialog();dialog.show()
    def prepare_close(self):
        if self.worker and self.worker.isRunning():
            self.closing=True;self.worker.requestInterruption();self.window.log.appendPlainText(t('Esperando a que termine la comprobación para cerrar…'));return False
        if self.ready and not updater.settings()['automatic']:
            root=self.root.resolve();stage=self.ready.resolve()
            if stage.parent==root and stage.name.startswith('.PhDexLab-update-') and not stage.is_symlink():
                try:shutil.rmtree(stage)
                except OSError:pass
            self.ready=None
        if self.ready:
            try:updater.schedule_install(self.ready,self.root);self.ready=None
            except Exception as error:
                self.window.log.appendPlainText(t('No se pudo preparar la instalación de la actualización.')+' '+str(error));self.set_status(0,'No se pudo preparar la instalación de la actualización.')
        return True
