"""PySide6 desktop UI; expensive COM work runs in an isolated child process."""
import copy
import json
import os
import sys
import time
import html
from pathlib import Path
from PySide6.QtCore import QProcess, Qt, QTimer, QSize
from PySide6.QtGui import QKeySequence,QFont,QFontDatabase,QIcon
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
    QPushButton,QLabel,QComboBox,QTabWidget,QTableWidget,QTableWidgetItem,QPlainTextEdit,
    QFileDialog,QMessageBox,QInputDialog,QHeaderView,QToolButton,QStyle,QSpinBox,QProgressBar,QMenu,QDialog,QDialogButtonBox,QLineEdit,QFormLayout)
from .protocols import catalog,save_variant,METHODS,validate,FE
from .data_entry import COLUMNS,parse_tsv,demo_rows,demo_varieties,normalize
from .excel import read_inputs
from .integration import create_experiment,file_hash,verify
from .paths import Layout,migrate_legacy
from .ui_fields import FIELDS,KIND_LABELS,PARAMETERS,ENUMS
from .data_table import RawTable
from .ui_icons import icon as app_icon
from .i18n import ActivityLog

class Window(QMainWindow):
    def __init__(self):
        super().__init__();self.folder=None;self.open_hash=None;self.proc=None;self.dirty=False;self.loading=False
        self.variant_folder=Path.home()/"Documents"/"PhDexLab"/"protocol_variants"
        self.setWindowTitle("PhDexLab");self.resize(1480,920)
        self.setWindowIcon(QIcon(str(Path(__file__).parent/'assets'/'phdexlab.ico')))
        self.setStyleSheet(STYLE)
        root=QWidget();layout=QVBoxLayout(root);self.setCentralWidget(root)
        heading=QHBoxLayout();layout.addLayout(heading)
        logo=QLabel();logo.setPixmap(self.windowIcon().pixmap(38,38));heading.addWidget(logo)
        title=QLabel("PhDexLab");title.setObjectName('hero');heading.addWidget(title);heading.addStretch()
        self.pathlabel=QLabel("Nuevo experimento sin guardar");heading.addWidget(self.pathlabel)
        bar=QHBoxLayout();layout.addLayout(bar);self.buttons=[]
        def button(label,callback,icon,container=bar):
            b=QToolButton();b.setProperty('iconName',icon);b.setIcon(app_icon(icon));b.setIconSize(QSize(22,22));b.setFixedSize(36,36)
            b.setToolTip(label);b.setAccessibleName(label);b.clicked.connect(lambda:self.guard(callback));container.addWidget(b);self.buttons.append(b);return b
        self.make_button=button
        button("Nuevo experimento",self.new,'new')
        button("Abrir experimento",self.open_experiment,'open')
        button("Cerrar experimento",self.close_experiment,'close')
        button("Guardar / generar Excel",self.save,'save')
        button("Actualizar y exportar resultados",self.update,'refresh').setObjectName('primary')
        bar.addSpacing(12)
        self.method=QComboBox();self.method.addItems(METHODS);bar.addWidget(QLabel("Método"));bar.addWidget(self.method)
        self.variant=QComboBox();bar.addWidget(QLabel("Variante"));bar.addWidget(self.variant,1)
        button('Crear protocolo FRAP manualmente',self.new_protocol,'protocol')
        self.variants=catalog(self.variant_folder)
        for p in self.variants:self.variant.addItem(p["name"])
        self.origin_mode=QComboBox();self.origin_mode.addItem("Origin: Excel Connector","connector");self.origin_mode.addItem("Origin: valores Excel","values");self.origin_mode.addItem("Solo Excel","none");bar.addWidget(self.origin_mode)
        self.tabs=QTabWidget();layout.addWidget(self.tabs,1)
        data_page=QWidget();data_layout=QVBoxLayout(data_page)
        self.metrics=QLabel('Una fila = una lectura · Los identificadores se generan automáticamente');self.metrics.setObjectName('metrics');data_layout.addWidget(self.metrics)
        self.raw=RawTable();data_layout.addWidget(self.raw,1);self.tabs.addTab(data_page,"1   Lecturas experimentales")
        self.roles_path=self.variant_folder.parent/'_internal'/'entry_types.json'
        if self.roles_path.exists():
            try:
                for label,kind in json.loads(self.roles_path.read_text(encoding='utf-8')):
                    if (label,kind) not in self.raw.roles:self.raw.add_role(label,kind)
            except (ValueError,TypeError):pass
        self.raw.horizontalHeader().sectionClicked.connect(self.field_popup)
        self.raw.itemChanged.connect(self.raw_changed)
        self.parameters=QTableWidget(0,3);self.parameters.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked|QTableWidget.EditTrigger.EditKeyPressed|QTableWidget.EditTrigger.AnyKeyPressed);self.parameters.setHorizontalHeaderLabels(["Parámetro del ensayo","Valor / selección","Ayuda"])
        self.parameters.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
        self.parameters.setColumnWidth(0,340);self.parameters.setColumnWidth(2,60);self.tabs.addTab(self.parameters,"2   Protocolo y condiciones")
        helptext=QPlainTextEdit();helptext.setReadOnly(True);helptext.setPlainText(
            "Protocolos en transferencia: revisar y validar antes de uso experimental. Un lote de blancos por experimento.\n\n"
            "Cada fila es una lectura. Pegado Ctrl+V: columnas tabuladas, cabecera opcional. Decimal: punto o coma.\n\n"
            "kind: blank, standard, control, sample. record_id único. sample_id + bio_id identifican la unidad; tech_id identifica cada repetición.\n"
            "Patrones: concentration en las unidades y base del protocolo; mismo sample_id por concentración.\n"
            "FRAP Fe: introducir A_initial y A_end. Trolox endpoint: A_end.\n"
            "matrix_blank_delta obligatorio: corrección neta ADICIONAL a blanco reactivo (0 explícito si no aplica).\n"
            "Muestras: dilution (solo dilución previa), extract_mL, mass_g positivos. Control: expected positivo en unidades del eje.\n\n"
            "Guardar crea el libro. Para editar Excel: abrir, guardar y CERRAR antes de actualizar.\n"
            "Actualizar usa los datos guardados EN EXCEL. Si editas esta tabla, usa Guardar para aplicarla y recalcular.\n"
            "Tras abrir un experimento se detectan cambios externos y se impide sobrescribirlos con una tabla antigua.\n"
            "Las variantes se guardan con hash y cada experimento conserva su copia inicial y las revisiones.\n"
            "QC provisional: revisar recuperación, rango, réplicas y residuos, no solo R².\n"
            "ABTS, DPPH, CUPRAC, TPC, TFC: registrados como futuras extensiones, sin cálculo implementado.\n"
            "El refresco es explícito. La sincronización automática y rutas relativas no se dan por verificadas.")
        self.help_dialog=QDialog(self);self.help_dialog.setWindowTitle('Ayuda de PhDexLab');self.help_dialog.resize(800,650)
        help_layout=QVBoxLayout(self.help_dialog);help_layout.addWidget(helptext)
        helptext.setPlainText("PROTOCOLOS\nPulsa el libro con + junto a Variante. Elige una base FRAP, asigna un nombre y edita las condiciones en la pestaña Protocolo. Guarda con el icono de copiar/+ de la barra inferior para añadir la versión al catálogo. No es necesario editar JSON. Solo están implementadas variantes FRAP Fe(II) y Trolox; otro ensayo requiere desarrollar y verificar su módulo de cálculo.\n\nVARIEDADES Y CALIBRACIÓN COMPARTIDA\nEn el icono de tubos de ensayo elige Tres variedades. Carga un único conjunto de blancos, patrones y control, más Variety A, B y C. Cada nombre de muestra genera un resultado separado. B1–B3 identifican unidades biológicas dentro de cada variedad; 1–3 identifican sus lecturas técnicas. Guarda el experimento y actualiza: la figura FRAP results mostrará las tres variedades con media, DE y puntos biológicos. Las medias sintéticas esperadas son 16, 24 y 32 µmol eq Fe(II)/g (DE 1,6; n=3).\n\n"+helptext.toPlainText())
        bottom=QHBoxLayout();layout.addLayout(bottom)
        self.row_count=QSpinBox();self.row_count.setRange(1,10000);self.row_count.setValue(10);self.row_count.setSuffix(' filas');self.row_count.setToolTip('Número de filas vacías que añadir');bottom.addWidget(self.row_count)
        button("Añadir el número de filas indicado",self.add_rows,'rows',bottom)
        button("Añadir lecturas o una media",self.add_sample,'measure',bottom)
        self.demo_button=button("Datos sintéticos: elegir una muestra o tres variedades",lambda:None,'demo',bottom)
        self.demo_menu=QMenu(self.demo_button)
        self.demo_menu.addAction('Una muestra · dos unidades biológicas',lambda:self.guard(self.load_demo))
        self.demo_menu.addAction('Tres variedades · una calibración compartida',lambda:self.guard(lambda:self.load_demo(True)))
        self.demo_button.setMenu(self.demo_menu);self.demo_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button("Guardar protocolo como nueva variante versionada",self.save_variant,'variant',bottom)
        button("Añadir tipo de lectura",self.add_kind,'type',bottom)
        button("Abrir el archivo Excel",self.open_excel,'excel',bottom)
        button("Abrir el proyecto Origin",self.open_origin,'origin',bottom)
        button("Ver gráficas exportadas de Origin",lambda:self.open_location('origin'),'plots',bottom)
        self.log_toggle=button('Mostrar / ocultar registro de actividad',lambda:None,'log',bottom);self.log_toggle.setCheckable(True);self.log_toggle.toggled.connect(self.toggle_log);self.buttons.remove(self.log_toggle)
        self.help_button=button('Abrir ayuda: protocolos, variedades y uso',self.show_help,'help',bottom);self.buttons.remove(self.help_button)
        bottom.addStretch();legend=QLabel('<span style="color:#C73542">*</span> Obligatorio según el tipo de lectura');bottom.addWidget(legend)
        self.progress_panel=QWidget();pl=QHBoxLayout(self.progress_panel);pl.setContentsMargins(0,0,0,0)
        self.progress=QProgressBar();self.progress.setRange(0,100);self.progress.setTextVisible(True);self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter);self.progress.setMinimumHeight(32);pl.addWidget(self.progress,1)
        layout.addWidget(self.progress_panel);self.progress_panel.hide()
        self.progress_timer=QTimer(self);self.progress_timer.setInterval(250);self.progress_timer.timeout.connect(self.poll_progress)
        self.log=ActivityLog();self.log.setReadOnly(True);self.log.setMaximumHeight(110);self.log.hide();layout.addWidget(self.log)
        self.parameters.itemChanged.connect(lambda _:self.mark_dirty())
        self.variant.currentIndexChanged.connect(self.select_variant);self.method.currentTextChanged.connect(self.select_method)
        self.select_variant(0)
    def guard(self,callback):
        try: callback()
        except Exception as e: QMessageBox.critical(self,"Operación no completada",str(e))
    def select_method(self,method):
        if method!="FRAP":
            QMessageBox.information(self,"Pendiente de implementación",f"{method}: arquitectura preparada; piloto disponible: FRAP.")
            self.method.setCurrentText("FRAP")
    def select_variant(self,index):
        if index>=0 and index<len(self.variants):
            self.set_protocol(self.variants[index])
            if self.folder:self.mark_dirty()
    def set_protocol(self,p):
        previous_loading=self.loading;self.loading=True
        self._protocol=copy.deepcopy(p)
        # Hide replaced cell widgets immediately; Qt destroys them later.
        for row in range(self.parameters.rowCount()):
            for column in range(self.parameters.columnCount()):
                old=self.parameters.cellWidget(row,column)
                if old:old.hide()
        self.parameters.clearContents()
        self.parameters.setRowCount(len(p))
        for r,(key,value) in enumerate(p.items()):
            label,helptext=PARAMETERS.get(key,(key,'Parámetro específico del protocolo.'))
            item=QTableWidgetItem(label);item.setData(Qt.ItemDataRole.UserRole,key);item.setToolTip(helptext);item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable);self.parameters.setItem(r,0,item)
            if key in ENUMS:
                editor=QComboBox()
                for val,name in ENUMS[key]:editor.addItem(name,val)
                editor.setCurrentIndex(max(0,editor.findData(value)));editor.currentIndexChanged.connect(lambda _:self.mark_dirty());editor.setToolTip(helptext);self.parameters.setCellWidget(r,1,editor)
            else:
                self.parameters.removeCellWidget(r,1)
                item=QTableWidgetItem('' if value is None else str(value));item.setToolTip(helptext)
                if key in ('method','equivalent','concentration_unit','report_factor','result_unit','id'):
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.parameters.setItem(r,1,item)
            required=key not in ('method','equivalent','concentration_unit','report_factor','result_unit','id','notes') and value is not None
            visible=QLabel(html.escape(label)+(' <span style="color:#C73542">*</span>' if required else ''));visible.setToolTip(helptext);visible.setContentsMargins(10,0,0,0);self.parameters.setCellWidget(r,0,visible)
            self.parameters.setRowHidden(r,key=='id')
            helpbutton=QPushButton();helpbutton.setProperty('iconName','help');helpbutton.setIcon(app_icon('help'));helpbutton.setAccessibleName('Ayuda: '+label);helpbutton.setToolTip(helptext);helpbutton.clicked.connect(lambda checked=False,title=label,text=helptext:QMessageBox.information(self,title,text));self.parameters.setCellWidget(r,2,helpbutton)
            self.parameters.setRowHeight(r,42)
        self.raw.set_protocol(p);self.loading=previous_loading
    def protocol(self):
        p={}
        for r in range(self.parameters.rowCount()):
            key=self.parameters.item(r,0).data(Qt.ItemDataRole.UserRole)
            editor=self.parameters.cellWidget(r,1)
            if isinstance(editor,QComboBox):value=editor.currentData()
            else:
                value=self.parameters.item(r,1).text()
                original=self._protocol[key]
                if isinstance(original,(int,float)) or original is None:
                    from .data_entry import number
                    value=number(value,required=original is not None)
                    if key=='version' and value is not None:value=int(value)
            p[key]=value
        return validate(p)
    def new(self):
        if not self.confirm_discard():return False
        self.clear_experiment();return True
    def clear_experiment(self):
        self.loading=True;self.folder=None;self.open_hash=None;self.raw.load([]);self.select_variant(self.variant.currentIndex());self.pathlabel.setText("Nuevo experimento sin guardar")
        self.loading=False;self.dirty=False;self.update_metrics();self.progress_panel.hide()
    def confirm_discard(self):
        if not self.dirty:return True
        answer=QMessageBox.question(self,'Cambios sin guardar','Hay cambios en la tabla o el protocolo. ¿Descartarlos?',QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)
        return answer==QMessageBox.StandardButton.Discard
    def close_experiment(self):
        if self.confirm_discard():
            self.clear_experiment();self.log.appendPlainText('Experimento cerrado. Los archivos se conservan.')
    def mark_dirty(self):
        if not self.loading:self.dirty=True
    def raw_changed(self,item):
        self.mark_dirty();self.update_metrics()
    def add_rows(self):
        count=self.raw.rowCount()+self.row_count.value()
        if count>10000:raise ValueError('Máximo: 10000 filas')
        self.raw.setRowCount(count)
    def add_sample(self):
        name,ok=QInputDialog.getText(self,'Preparar muestra','Nombre único de muestra o variedad (resultados separados):')
        if not ok or not name.strip():return
        name=name.strip();rows=self.raw.records()
        if any(d['kind']=='sample' and d['sample_id']==name for d in rows):raise ValueError('Ese nombre de muestra ya existe. Edita sus filas o elige otro nombre.')
        bio,ok=QInputDialog.getInt(self,'Réplicas biológicas','Número de unidades biológicas independientes:',3,1,100)
        if not ok:return
        tech,ok=QInputDialog.getInt(self,'Réplicas técnicas','Lecturas por cada unidad biológica:',3,1,100)
        if not ok:return
        if len(rows)+bio*tech>10000:raise ValueError('Máximo: 10000 lecturas')
        for b in range(1,bio+1):
            for t in range(1,tech+1):
                row=dict.fromkeys(COLUMNS,'');row.update(kind='sample',sample_id=name,bio_id=f'B{b}',tech_id=str(t));rows.append(row)
        self.raw.load(rows);self.dirty=True;self.update_metrics();self.raw.setCurrentCell(len(rows)-bio*tech,6);self.raw.scrollToItem(self.raw.item(len(rows)-bio*tech,6))
    def toggle_log(self,checked):
        self.log.setVisible(checked)
    def load_demo(self,multivariety=False):
        if self.new() is False:return
        self.loading=True
        self.variant.setCurrentIndex(0);self.set_protocol(FE);self.raw.load(demo_varieties() if multivariety else demo_rows());self.update_metrics();self.log.appendPlainText("SINTÉTICO: tres variedades, una calibración; medias esperadas 16, 24 y 32; DE 1,6; n biológico=3." if multivariety else "Datos SINTÉTICOS cargados. Ningún resultado experimental real.");self.loading=False;self.dirty=False
    def load_folder(self,path):
        verify(path);layout=migrate_legacy(path);rows,p=read_inputs(layout.master)
        self.loading=True
        self.folder=layout.root;self.raw.load(rows);self.set_protocol(p);self.open_hash=file_hash(layout.master);self.pathlabel.setText(layout.stem);self.update_metrics()
        self.loading=False;self.dirty=False
        status=layout.meta/"status.json"
        if status.exists():
            state=json.loads(status.read_text(encoding='utf-8'))
            label={'complete':'Excel y Origin actualizados','pending':'Pendiente de calcular','excel_ready':'Excel actualizado','partial':'Actualización parcial: revisar incidencias','failed':'Error: revisar informe interno'}.get(state.get('state'),'En proceso')
            self.log.appendPlainText(label)
    def open_experiment(self):
        path=QFileDialog.getExistingDirectory(self,"Seleccionar carpeta del experimento")
        if path and self.confirm_discard():self.load_folder(path)
    def show_help(self):
        self.help_dialog.show();self.help_dialog.raise_();self.help_dialog.activateWindow()
    def new_protocol(self):
        dialog=QDialog(self);dialog.setWindowTitle('Crear protocolo FRAP');dialog.resize(600,300)
        layout=QVBoxLayout(dialog)
        text=QLabel('Crea una variante a partir de una base compatible. Después podrás editar manualmente tiempos, volúmenes, temperatura, respuesta, concentraciones y condiciones en «Protocolo y condiciones». Guarda la variante con el icono de copiar/+ de la barra inferior. Las condiciones no se validan experimentalmente al guardarlas.');text.setWordWrap(True);layout.addWidget(text)
        form=QFormLayout();layout.addLayout(form);name=QLineEdit();name.setPlaceholderText('Ej.: FRAP Fe(II) · extracto de hoja · 8 min');form.addRow('Nombre del protocolo *',name)
        base=QComboBox()
        for variant in self.variants:base.addItem(variant['name'])
        base.setCurrentIndex(max(0,self.variant.currentIndex()));form.addRow('Base de cálculo *',base)
        note=QLabel('Solo FRAP está implementado. ABTS, DPPH, CUPRAC, TPC y TFC requieren un módulo de cálculo específico.');note.setWordWrap(True);layout.addWidget(note)
        actions=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);actions.button(QDialogButtonBox.StandardButton.Ok).setText('Crear y editar');layout.addWidget(actions)
        actions.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False);name.textChanged.connect(lambda value:actions.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(value.strip())))
        actions.accepted.connect(dialog.accept);actions.rejected.connect(dialog.reject)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        self.prepare_protocol(name.text().strip(),base.currentIndex())
    def prepare_protocol(self,name,index):
        if not name.strip():raise ValueError('El protocolo necesita un nombre')
        import uuid
        p=copy.deepcopy(self.variants[index]);p.update(name=name.strip(),id='frap-custom-'+uuid.uuid4().hex,version=0,status='BORRADOR — variante manual pendiente de validar')
        self.variant.setCurrentIndex(-1);self.set_protocol(p);self.tabs.setCurrentWidget(self.parameters);self.mark_dirty()
        self.log.appendPlainText('Protocolo preparado. Edita las condiciones y pulsa Guardar protocolo para añadirlo al catálogo.')
    def save_variant(self):
        p=self.protocol();name,ok=QInputDialog.getText(self,"Nombre variante","Nombre de la nueva variante",text=p["name"])
        if not ok or not name.strip(): return
        p=copy.deepcopy(p);p["name"]=name.strip();p["version"]+=1
        path=save_variant(self.variant_folder,p);self.variants.append(p);self.variant.addItem(p["name"]);self.variant.setCurrentIndex(len(self.variants)-1)
        self.log.appendPlainText(f"Protocolo guardado en catálogo: {p['name']} · versión {p['version']}")
    def save(self):
        p=self.protocol();rows=normalize(self.raw.records(),p)
        if self.folder is None:
            parent=QFileDialog.getExistingDirectory(self,"Carpeta que contendrá el experimento")
            if not parent:return
            name,ok=QInputDialog.getText(self,"Nuevo experimento","Nombre de carpeta nueva")
            if not ok:return
            if not name or name in (".","..") or any(c in name for c in '<>:"/\\|?*'):raise ValueError("Nombre de carpeta inválido")
            path=create_experiment(Path(parent)/name,rows,p);self.load_folder(path)
            self.log.appendPlainText("Excel creado. Actualizar para recalcular y exportar.")
        else:
            # Child process applies edited inputs only if workbook hash still matches.
            from .integration import dump
            payload=Layout(self.folder).meta/".pending-ui.json";dump(payload,dict(rows=rows,protocol=p,expected_hash=self.open_hash))
            self.start("apply",payload)
    def open_excel(self):
        if not self.folder:raise ValueError("Guardar o abrir un experimento primero")
        os.startfile(Layout(self.folder).master)
    def open_origin(self):
        if not self.folder:raise ValueError('Guardar o abrir un experimento primero')
        project=Layout(self.folder).project
        if not project.exists():raise ValueError('El proyecto Origin todavía no existe. Selecciona un modo Origin y pulsa Actualizar y exportar primero.')
        os.startfile(project)
    def update(self):
        if not self.folder:raise ValueError("Guardar o abrir un experimento primero")
        if self.dirty:raise ValueError("Hay cambios en la ventana. Guarda primero para aplicarlos; Actualizar utiliza el Excel guardado.")
        self.start("refresh")
    def start(self,action,payload=None):
        if self.proc: raise RuntimeError("Ya hay una actualización en curso")
        self.proc=QProcess(self);self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self.worker_output)
        self.proc.finished.connect(self.finished)
        self.proc.errorOccurred.connect(self.process_error)
        self.proc.setWorkingDirectory(str(Path(__file__).resolve().parents[1]))
        for b in self.buttons:b.setEnabled(False)
        for widget in (self.tabs,self.method,self.variant,self.origin_mode,self.row_count):widget.setEnabled(False)
        self.started=time.monotonic();self.progress_stage='Preparando actualización';self.progress_panel.show();self.progress.setRange(0,100);self.progress.setValue(0)
        from .integration import dump
        dump(Layout(self.folder).meta/'progress.json',dict(label=self.progress_stage,step=0,total=6,busy=True))
        self.progress_timer.start();self.poll_progress()
        self.log.appendPlainText("Calculando con Excel y actualizando Origin… Guardar y cerrar los libros en Excel antes de continuar.")
        prefix=['--worker'] if getattr(sys,'frozen',False) else ['-m','phdexlab.worker']
        self.proc.start(sys.executable,prefix+[str(self.folder),str(self.origin_mode.currentData()),str(payload) if payload else ""])
    def finished(self,code,status):
        if self.proc:self.proc.deleteLater()
        self.proc=None;self.progress_timer.stop()
        for b in self.buttons:b.setEnabled(True)
        for widget in (self.tabs,self.method,self.variant,self.origin_mode,self.row_count):widget.setEnabled(True)
        self.progress.setRange(0,100);self.progress.setValue(100 if code==0 else self.progress.value())
        self.progress.setFormat(('Actualización finalizada' if code==0 else 'Error de actualización; abre el registro')+f' · {int(time.monotonic()-self.started)} s')
        if code!=0:self.log_toggle.setChecked(True)
        if code==0:
            self.guard(lambda:self.load_folder(self.folder))
            state=json.loads((Layout(self.folder).meta/'status.json').read_text(encoding='utf-8'))
            if state.get('state')=='partial':
                self.progress.setFormat('Actualización parcial · consulta el registro y el informe de Origin');self.log_toggle.setChecked(True)
            self.log.appendPlainText("Resultados disponibles en Documents, Figures y Results.")
        else:self.log.appendPlainText("No se completó la operación. Consultar el error y status.json; se conserva historial.")
    def poll_progress(self):
        if not self.folder:return
        try:
            data=json.loads((Layout(self.folder).meta/'progress.json').read_text(encoding='utf-8'))
            self.progress_stage=f"{data['label']} · etapa {data['step']}/{data['total']}"
            self.progress.setValue(100 if not data.get('busy',True) and data.get('state')!='failed' else max(0,int(100*(data['step']-1)/data['total'])))
        except (OSError,ValueError,KeyError):pass
        elapsed=int(time.monotonic()-self.started);self.progress.setFormat(f'{self.progress_stage} · {elapsed//60:02d}:{elapsed%60:02d}')
    def process_error(self,error):
        self.log.appendPlainText(f"Error proceso: {error}")
        if error==QProcess.ProcessError.FailedToStart and self.proc:
            self.finished(-1,QProcess.ExitStatus.CrashExit)
    def closeEvent(self,event):
        if self.proc:
            QMessageBox.information(self,"Actualización activa","Espera a que termine la actualización antes de cerrar.");event.ignore()
        else:event.accept()
    def worker_output(self):
        text=bytes(self.proc.readAllStandardOutput()).decode('utf-8',errors='replace')
        if 'Traceback' in text or 'Error' in text:self.log.appendPlainText(text[-1800:])
    def field_popup(self,column):
        if 0<=column<len(COLUMNS):
            title,helptext=FIELDS[COLUMNS[column]];QMessageBox.information(self,title.replace('\n',' '),helptext)
    def update_metrics(self):
        counts={k:0 for k in KIND_LABELS};samples=set()
        for r in range(self.raw.rowCount()):
            item=self.raw.item(r,1)
            if item:
                kind=item.data(Qt.ItemDataRole.UserRole) or item.text()
                if kind in counts:counts[kind]+=1
                if kind=='sample' and self.raw.item(r,2):samples.add(self.raw.item(r,2).text().strip())
        self.metrics.setText(f"{sum(counts.values())} lecturas   ·   {counts['blank']} blancos   ·   {counts['standard']} patrones   ·   {counts['control']} controles   ·   {len(samples-{''})} muestras distintas ({counts['sample']} lecturas)   |   Una fila = una lectura")
    def add_kind(self):
        label,ok=QInputDialog.getText(self,'Añadir tipo de lectura','Nombre visible (ej.: Control fortificado)')
        if not ok:return
        category,ok=QInputDialog.getItem(self,'Comportamiento analítico','Se calculará como:',list(KIND_LABELS.values()),0,False)
        if not ok:return
        kind=next(k for k,v in KIND_LABELS.items() if v==category);self.raw.add_role(label,kind)
        self.roles_path.parent.mkdir(parents=True,exist_ok=True)
        self.roles_path.write_text(json.dumps(self.raw.roles,ensure_ascii=False),encoding='utf-8')
        self.log.appendPlainText(f'Tipo disponible: {label} · categoría: {category}. Se conservará al guardar lecturas con este tipo.')
    def open_location(self,which):
        if not self.folder:raise ValueError('Abre o guarda un experimento primero')
        layout=Layout(self.folder);path=layout.documents if which=='documents' else layout.figures/'Origin'
        path.mkdir(parents=True,exist_ok=True);os.startfile(path)

def run():
    app=QApplication.instance() or QApplication(sys.argv)
    configure_font(app)
    from .workspace import Window as ExperimentWindow
    w=ExperimentWindow();w.show()
    from .onboarding import show_on_first_use
    QTimer.singleShot(0,lambda:show_on_first_use(w))
    return app.exec()

def configure_font(app):
    font=Path(os.environ.get("WINDIR","C:/Windows"))/"Fonts"/"segoeui.ttf"
    if font.exists():QFontDatabase.addApplicationFont(str(font))
    app.setFont(QFont("Segoe UI",10))

STYLE='''
QMainWindow, QWidget { background:#F4F8FA; color:#203944; font-family:"Segoe UI"; }
QLabel#hero { font-size:28px; font-weight:700; padding:2px 3px; color:#155D68; }
QLabel#notice { background:#FFF7E6; color:#77561D; border:1px solid #EAD9AE; border-radius:8px; padding:9px; }
QPushButton { background:white; border:1px solid #CADCE1; border-radius:7px; padding:9px 12px; font-weight:600; }
QPushButton:hover { background:#E6F3F4; border-color:#5CA8AD; }
QPushButton:disabled { color:#91A1A9; background:#EDF1F4; }
QPushButton#primary { background:#177E89; color:white; border-color:#177E89; }
QPushButton#primary:hover { background:#106772; }
QPushButton#helpCircle { border-radius:16px; background:#DFF0F2; color:#155D68; padding:0; }
QComboBox { background:white; border:1px solid #CADCE1; border-radius:6px; padding:7px; min-width:85px; }
QComboBox QAbstractItemView { background:white; selection-background-color:#D9EFF1; color:#203944; }
QTabWidget::pane { border:1px solid #D9E6EB; border-radius:8px; background:white; }
QTabBar::tab { background:#E7EFF2; padding:8px 18px; margin-right:5px; border-radius:6px; }
QTabBar::tab:selected { background:#177E89; color:white; font-weight:600; }
QHeaderView::section { background:#E9F2F5; color:#234D5A; border:0; border-right:1px solid #D8E5EB; border-bottom:2px solid #BFD4DC; padding:7px; font-weight:600; }
QTableWidget { background:white; alternate-background-color:#F7FAFC; gridline-color:#E4ECF0; border:1px solid #D9E6EB; selection-background-color:#D8EEF1; selection-color:#123E49; }
QLabel#metrics { background:#E8F3F5; color:#155D68; font-weight:600; padding:6px; border-radius:7px; }
QLabel#fieldHelp { background:#EFF6FA; padding:4px; border-radius:5px; color:#365767; }
QPlainTextEdit { background:white; border:1px solid #D9E6EB; border-radius:7px; padding:7px; }
'''

STYLE += """
QToolButton { background:white; border:1px solid #CADCE1; border-radius:6px; padding:3px; }
QToolButton:hover { background:#DCEFF1; border-color:#5CA8AD; }
QToolButton#primary { background:#C8EAE9; border-color:#177E89; }
QSpinBox { background:white; border:1px solid #CADCE1; border-radius:6px; padding:5px; }
QProgressBar { border:1px solid #B5CDD3; border-radius:6px; background:#EDF4F6; color:#123D47; font-weight:600; min-height:30px; }
QProgressBar::chunk { background:#B9DEDF; border-radius:5px; }
QTableWidget { font-size:14px; }
"""
