"""Experiment workspace: assay navigator + reusable data/protocol editor."""
import copy,html,json,os
from pathlib import Path
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QSplitter,QListWidget,QListWidgetItem,QLabel,QDialog,QFormLayout,QLineEdit,QComboBox,QDialogButtonBox,QInputDialog,QMessageBox,QFileDialog,QTextBrowser,QTableWidgetItem,QSizePolicy,QStackedWidget,QPushButton)
from .interface import Window as SingleAssayWindow
from .protocols import FE,digest,save_variant
from .method_catalog import ALL,METHOD_NAMES
from .assay_engine import engine,state,NUMERIC_PARAMS,validate_protocol
from .data_entry import demo_rows,demo_varieties,number
from .experiments import new_id
from . import experiments
from .integration import file_hash
from .paths import Layout
from .help_center import HelpDialog
from .ui_fields import PARAMETERS,ENUMS,FIELDS
from .demonstrations import multi_demo
from .workspace_features import WorkspaceFeatures
from .i18n import t,localize
from .graph_styles import DEFAULT,read_presentation,save_presentation,presentation_hash
from .protocol_texts import display_value,input_value,VALUE_ROLE

class Window(WorkspaceFeatures,SingleAssayWindow):
    def closeEvent(self,event):
        if self.proc:return super().closeEvent(event)
        updates=getattr(self,'updates',None)
        if updates and updates.worker and updates.worker.isRunning():updates.prepare_close();event.ignore();return
        if not self.confirm_discard():event.ignore();return
        if updates and not updates.prepare_close():event.ignore();return
        event.accept()

    def __init__(self):
        self._workspace_ready=False;self.assays=[];self.active_id=None;self.saved_states={};self.next_assay_number=1
        super().__init__()
        self.variants=copy.deepcopy(ALL)
        if self.variant_folder.exists():
            for path in self.variant_folder.glob('*.json'):
                try:
                    p=json.loads(path.read_text(encoding='utf-8'));validate_protocol(p);self.variants.append(p)
                except (ValueError,KeyError):pass
        layout=self.centralWidget().layout();layout.removeWidget(self.tabs)
        self.splitter=QSplitter();left=QWidget();left_layout=QVBoxLayout(left);left_layout.setContentsMargins(0,0,6,0)
        caption=QLabel('ENSAYOS DEL EXPERIMENTO');caption.setStyleSheet('font-weight:700;color:#176E78;padding:8px 0');left_layout.addWidget(caption)
        actions=QHBoxLayout();left_layout.addLayout(actions)
        self.add_assay_button=self.make_button('Añadir un ensayo al experimento',self.add_assay,'sample',actions)
        self.make_button('Duplicar el ensayo seleccionado',self.duplicate_assay,'variant',actions)
        self.make_button('Retirar el ensayo seleccionado',self.remove_assay,'close',actions);actions.addStretch()
        self.assay_list=QListWidget();self.assay_list.setWordWrap(True);self.assay_list.setMinimumWidth(210);self.assay_list.setStyleSheet('QListWidget{background:white;border:1px solid #D9E6EB;border-radius:7px} QListWidget::item{padding:12px 6px;border-bottom:1px solid #E7EFF1} QListWidget::item:selected{background:#D8EEF1;color:#123E49}')
        left_layout.addWidget(self.assay_list,1);self.assay_list.currentRowChanged.connect(self.switch_assay);self.assay_list.itemDoubleClicked.connect(lambda _:self.rename_assay())
        self.assay_pages=QStackedWidget();self.assay_pages.addWidget(self.tabs)
        self.empty_page=QWidget();empty_layout=QVBoxLayout(self.empty_page);empty_layout.addStretch()
        title=QLabel('Empieza añadiendo un ensayo');title.setAlignment(Qt.AlignmentFlag.AlignCenter);title.setStyleSheet('font-size:24px;font-weight:600;padding:16px');empty_layout.addWidget(title)
        hint=QLabel('Elige el método y su protocolo para empezar a introducir datos.');hint.setAlignment(Qt.AlignmentFlag.AlignCenter);empty_layout.addWidget(hint)
        row=QHBoxLayout();row.addStretch();self.first_assay_button=QPushButton('Nuevo ensayo');self.first_assay_button.setProperty('iconName','sample');self.first_assay_button.setIcon(self.add_assay_button.icon());self.first_assay_button.setToolTip('Añadir un ensayo al experimento');self.first_assay_button.clicked.connect(lambda:self.guard(self.add_assay));row.addWidget(self.first_assay_button);row.addStretch();empty_layout.addLayout(row);empty_layout.addStretch();self.assay_pages.addWidget(self.empty_page)
        self.splitter.addWidget(left);self.splitter.addWidget(self.assay_pages);self.splitter.setStretchFactor(0,0);self.splitter.setStretchFactor(1,1);self.splitter.setSizes([235,1200]);layout.insertWidget(2,self.splitter,1)
        bar=layout.itemAt(1).layout()
        self.method.hide()
        for i in range(bar.count()):
            w=bar.itemAt(i).widget()
            if isinstance(w,QLabel) and w.text()=='Método':w.hide()
        for button in list(self.buttons):
            if 'Crear protocolo FRAP' in button.toolTip():
                button.setToolTip('Editar las condiciones del protocolo de este ensayo');button.setAccessibleName(button.toolTip())
            if button.property('iconName')=='variant' and button.toolTip()=='Guardar protocolo como nueva variante versionada':
                # One visible save action, next to Variant. The old bottom duplicate is retired.
                bottom=layout.itemAt(3).layout();bottom.removeWidget(button);button.setParent(None);self.buttons.remove(button);button.deleteLater()
            if button.toolTip()=='Guardar / generar Excel':button.setToolTip('Guardar las entradas de todos los ensayos en el Excel maestro')
        self.save_variant_button=self.make_button('Guardar protocolo como nueva variante versionada',self.save_variant,'protocol-save',bar)
        bar.removeWidget(self.save_variant_button);bar.insertWidget(bar.count()-1,self.save_variant_button)
        self.method_guide=QTextBrowser();self.method_guide.setOpenExternalLinks(True);self.tabs.addTab(self.method_guide,'3   Metodología')
        self.help_dialog.close();self.help_dialog.deleteLater();self.help_dialog=HelpDialog(self)
        self.demo_menu.clear()
        self.demo_menu.addAction('FRAP · una muestra',lambda:self.guard(self.load_demo))
        self.demo_menu.addAction('FRAP · tres variedades y un calibrado',lambda:self.guard(lambda:self.load_demo(True)))
        self.demo_menu.addAction('Experimento con cinco métodos y tres variedades',lambda:self.guard(lambda:self.load_multi_demo(False)))
        self.demo_menu.addAction('Demo extendida: DPPH, pesadas y tamizado',lambda:self.guard(lambda:self.load_multi_demo(True)))
        self.status_timer=QTimer(self);self.status_timer.setInterval(300);self.status_timer.setSingleShot(True);self.status_timer.timeout.connect(self.update_current_state)
        self.metrics.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed);self.metrics.setMinimumWidth(0)
        self._workspace_ready=True
        self.set_assays([])
        self.dirty=False
        self.setup_features();self.sync_assay_controls()
    def mark_dirty(self):
        super().mark_dirty()
        if self._workspace_ready and not self.loading:self.status_timer.start()
    def raw_changed(self,item):
        if self.loading:return
        self.mark_dirty();super().update_metrics()
    def protocol(self):
        if not self._workspace_ready:return super().protocol()
        p={}
        for r in range(self.parameters.rowCount()):
            key=self.parameters.item(r,0).data(Qt.ItemDataRole.UserRole);editor=self.parameters.cellWidget(r,1)
            value=editor.currentData() if isinstance(editor,QComboBox) else input_value(self.parameters.item(r,1))
            if key in NUMERIC_PARAMS:
                try:value=number(value)
                except (ValueError,TypeError):pass  # Preserve incomplete/invalid draft entry for correction.
                if key=='version' and isinstance(value,(int,float)):value=int(value)
            p[key]=value
        if p.get('method')=='TFC':
            p['result_unit']='mg RE/g' if p['equivalent']=='Rutin' else 'mg QE/g'
            if p['equivalent']=='Rutin' and not any(s in str(p.get('notes','')) for s in ('Variante manual con rutina','Manual rutin variant')):p['notes']=str(p.get('notes',''))+' Manual rutin variant: the reference uses quercetin; do not attribute this modification to the original article.'
            for r in range(self.parameters.rowCount()):
                if self.parameters.item(r,0).data(Qt.ItemDataRole.UserRole)=='result_unit' and self.parameters.item(r,1).text()!=p['result_unit']:
                    self.parameters.blockSignals(True);self.parameters.item(r,1).setText(p['result_unit']);self.parameters.blockSignals(False)
        return p
    def set_protocol(self,p):
        if self._workspace_ready and not p:
            self.show_empty_workspace();return
        super().set_protocol(p)
        if not self._workspace_ready:return
        previous_loading=self.loading;self.loading=True
        locked={'method','id','engine','quantity','concentration_unit','report_factor','result_unit','blocked_reason'}
        if p.get('method')!='TFC':locked.add('equivalent')
        mandatory={'name','source'}
        if engine(p) in ('colorimetric','inhibition'):mandatory|={'aliquot_uL','reagent_uL','water_uL','time_min','wavelength_nm','calibration_basis'}
        if p.get('blocked_reason'):mandatory|={'operational_confirmed','standard_reference','endpoint_note','temperature_C'}
        for r in range(self.parameters.rowCount()):
            key=self.parameters.item(r,0).data(Qt.ItemDataRole.UserRole)
            item=self.parameters.item(r,1)
            if item and not self.parameters.cellWidget(r,1):
                raw=p[key];shown=display_value(key,raw);shown='' if shown is None else str(shown)
                item.setText(shown);item.setData(VALUE_ROLE,[raw,shown])
            label=PARAMETERS.get(key,(key,''))[0];widget=self.parameters.cellWidget(r,0)
            if isinstance(widget,QLabel):widget.setText(html.escape(label)+(' <span style="color:#C73542">*</span>' if key in mandatory and key not in locked else ''))
            hidden={'id','engine','quantity'}
            if engine(p) in ('gravimetric','sieve'):hidden|={'response','equivalent','concentration_unit','calibration_basis','wavelength_nm','aliquot_uL','reagent_uL','water_uL','reaction_total_uL','report_factor','standard_range','r2_min','cv_max_percent','recovery_min_percent','recovery_max_percent','reagents'}
            if not p.get('blocked_reason'):hidden|={'blocked_reason','operational_confirmed','standard_reference'}
            self.parameters.setRowHidden(r,key in hidden)
            if key=='response' and engine(p) in ('inhibition','ec50'):
                widget=self.parameters.cellWidget(r,1)
                if isinstance(widget,QComboBox):widget.setEnabled(False)
            if key in locked and self.parameters.item(r,1):self.parameters.item(r,1).setFlags(self.parameters.item(r,1).flags() & ~Qt.ItemFlag.ItemIsEditable)
            if key=='equivalent' and p.get('method')=='TFC':
                editor=QComboBox();editor.addItem(t('Quercetina (QE)'),'Quercetin');editor.addItem(t('Rutina (RE) · variante manual'),'Rutin');editor.setCurrentIndex(max(0,editor.findData(p['equivalent'])));editor.currentIndexChanged.connect(lambda _:self.mark_dirty());self.parameters.setCellWidget(r,1,editor)
            from .ui_icons import icon
            help_button=self.parameters.cellWidget(r,2);help_button.clicked.disconnect();help_button.setIcon(icon('link' if key=='source' else 'help'));help_button.setProperty('iconName','link' if key=='source' else 'help')
            if key=='source':
                help_button.setToolTip(t('Abrir artículo original / fuente'));help_button.clicked.connect(lambda checked=False,row=r:self.guard(lambda:self.open_reference(row)))
            else:
                help_button.setToolTip(t('Ayuda')+': '+t(label));help_button.clicked.connect(lambda checked=False,k=key:self.parameter_help(k))
            help_button.setAccessibleName(help_button.toolTip())
        self.loading=previous_loading;localize(self.parameters);self.update_guide(p)
    def parameter_help(self,key):
        label,explanation=PARAMETERS.get(key,(key,'Parámetro específico del protocolo.'));QMessageBox.information(self,t(label),t(explanation))
    def open_reference(self,row):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        value=self.parameters.item(row,1).text().strip()
        if not value.startswith(('https://','http://')):raise ValueError(t('Introduce un enlace web para la fuente.'))
        QDesktopServices.openUrl(QUrl(value))
    def update_guide(self,p):
        if not hasattr(self,'method_guide'):return
        source=html.escape(str(p.get('source','')));e=engine(p)
        equations={'colorimetric':'Respuesta corregida → calibración OLS → concentración equivalente → dilución previa × volumen de extracto / masa. La concentración final de reacción se convierte a alícuota una sola vez.',
            'inhibition':'Inhibición (%) = 100 × (A_control radical − A_muestra corregida) / A_control radical. Calibrar con Trolox. No restar de nuevo el control como blanco.',
            'ec50':'Mesetas confirmadas por el operador → media técnica por dosis y unidad → interpolación local alrededor de 50% → media y DE biológica de EC50. Sin extrapolación ni meseta automática.',
            'gravimetric':'Humedad = 100(m1−m2)/(m1−m0). Materia seca = 100(m2−m0)/(m1−m0). Cenizas = 100(m2−m0)/masa neta inicial; la base seca exige la fracción seca correspondiente.',
            'sieve':'Retenido (%) = 100 × masa de fracción / masa cargada. Recuperación = 100 × suma de fracciones / masa cargada. No se normaliza al 100%.'}
        value=lambda key:html.escape(str(display_value(key,p.get(key,''))))
        self.method_guide.setHtml('<h2>'+value('name')+'</h2><h3>'+t('Qué se calcula')+'</h3><p>'+t(equations[e])+'</p><h3>'+t('Condiciones y reactivos')+'</h3><p>'+value('reagents')+'<br>'+value('notes')+'</p><h3>'+t('Estado')+'</h3><p>'+value('status')+'<br>'+value('blocked_reason')+'</p><h3>'+t('Referencia bibliográfica')+'</h3><p><a href="'+source+'">'+source+'</a></p>')
    def commit_active(self):
        if not self._workspace_ready or self.active_id is None:return
        a=next((a for a in self.assays if a['id']==self.active_id),None)
        if a is None:return
        was=self.loading;self.loading=True
        try:a['protocol']=self.protocol();a['rows']=self.raw.records()
        finally:self.loading=was
    def set_assays(self,assays,active=0):
        self.status_timer.stop();self.loading=True;self.assays=copy.deepcopy(assays);self.next_assay_number=max(self.next_assay_number,max([int(a['id'].split('_')[0][1:]) for a in assays]+[0])+1);self.active_id=None
        self.assay_list.blockSignals(True);self.assay_list.clear()
        for a in self.assays:self.assay_list.addItem(self.item_text(a))
        self.assay_list.setCurrentRow(active);self.assay_list.blockSignals(False);self.loading=False;self.switch_assay(active)
        if not self.assays:self.show_empty_workspace()
        self.sync_assay_controls()
    def show_empty_workspace(self):
        self.loading=True;self.active_id=None;self._protocol={};self.parameters.clearContents();self.parameters.setRowCount(0)
        self.raw.protocol=None;self.raw.clearContents();self.raw.setRowCount(0);self.variant.blockSignals(True);self.variant.clear();self.variant.blockSignals(False)
        self.method_guide.clear();self.metrics.clear();self.loading=False;self.assay_pages.setCurrentWidget(self.empty_page)
    def sync_assay_controls(self):
        active=bool(self.active_id);busy=bool(self.proc)
        for button in self.buttons:
            icon=button.property('iconName')
            needs=icon in ('save','refresh','rows','type','excel','origin','plots','protocol','protocol-save','template','variant','close') or (icon=='sample' and button is not self.add_assay_button)
            if needs:button.setEnabled(active and not busy)
        self.variant.setEnabled(active and not busy);self.origin_mode.setEnabled(active and not busy);self.row_count.setEnabled(active and not busy)
        if hasattr(self,'templates_button'):self.templates_button.setEnabled(active and not busy)
    def item_text(self,a):
        status,issue,_=state(a);label='Listo para calcular' if status=='ready' else 'Borrador'
        cached=self.saved_states.get(a['id'],{}) if not self.dirty else {}
        label={'calculated':'Calculado · revisar QC','needs_review':'Revisar resultados','invalid':'Resultado inválido','draft':'Borrador'}.get(cached.get('state'),label)
        return a['label']+'\n'+t(label)+' · '+a['id']
    def switch_assay(self,index):
        if not self._workspace_ready or not 0<=index<len(self.assays):return
        self.assay_pages.setCurrentWidget(self.tabs);self.commit_active();self.loading=True;a=self.assays[index];self.active_id=a['id'];p=a['protocol'];self.set_protocol(p);self.raw.load(a.get('rows',[]));self.populate_variants(p);self.loading=False;super().update_metrics();self.update_current_state()
    def populate_variants(self,p):
        if not p:return
        self.variant.blockSignals(True);self.variant.clear();selected=-1
        for idx,v in enumerate(self.variants):
            if v['method']==p['method']:
                self.variant.addItem(display_value('name',v['name'])+' · v'+str(v['version']),idx)
                if v==p:selected=self.variant.count()-1
        if selected<0:self.variant.addItem(display_value('name',p['name'])+t(' · en este ensayo'),None);selected=self.variant.count()-1
        self.variant.setCurrentIndex(selected);self.variant.blockSignals(False)
    def select_variant(self,index):
        if not self._workspace_ready:return super().select_variant(index)
        global_index=self.variant.itemData(index)
        if global_index is None or self.loading or not self.active_id:return
        self.commit_active();self.loading=True;self.set_protocol(copy.deepcopy(self.variants[global_index]));self.loading=False;self.mark_dirty();self.update_current_state()
    def select_method(self,method):
        if not self._workspace_ready:return super().select_method(method)
    def update_current_state(self):
        if not self._workspace_ready or self.loading or self.proc:return
        self.commit_active();index=self.assay_list.currentRow()
        if 0<=index<len(self.assays):
            a=self.assays[index];self.update_guide(a['protocol']);status,issue,_=state(a);item=self.assay_list.item(index);item.setText(self.item_text(a));item.setToolTip(t(issue or 'Entradas completas. Guardar y actualizar para calcular.'))
            super().update_metrics();self.metrics.setText(a['id']+' · '+self.metrics.text()+('   |   '+issue if issue else '   |   Listo para calcular'))
            self.metrics.setToolTip(issue)
            localize(self) if hasattr(self,'language_selector') else None
    def field_popup(self,column):
        if 0<=column<len(self.raw.columns):
            title,text=FIELDS[self.raw.columns[column]];QMessageBox.information(self,title.replace('\n',' '),text)
    def add_assay(self):
        self.commit_active();dialog=QDialog(self);dialog.setWindowTitle('Añadir ensayo al experimento');layout=QVBoxLayout(dialog);form=QFormLayout();layout.addLayout(form)
        method=QComboBox()
        for key,name in METHOD_NAMES.items():method.addItem(t(name),key)
        variant=QComboBox();name=QLineEdit();form.addRow('Método',method);form.addRow('Protocolo / variante',variant);form.addRow('Nombre del ensayo',name)
        def fill():
            variant.clear()
            for index,p in enumerate(self.variants):
                if p['method']==method.currentData():variant.addItem(display_value('name',p['name']),index)
            name.setText(t(METHOD_NAMES[method.currentData()]))
        method.currentIndexChanged.connect(fill);fill();note=QLabel('Cada ensayo conserva sus datos y calibración. Puedes añadir otro ensayo del mismo método para una variante o lote distinto.');note.setWordWrap(True);layout.addWidget(note)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Añadir ensayo');buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons);dialog.resize(680,240)
        if dialog.exec()==QDialog.DialogCode.Accepted:self.append_assay(self.variants[variant.currentData()],name.text().strip() or METHOD_NAMES[method.currentData()])
    def append_assay(self,p,label,rows=None):
        self.commit_active();a=dict(id=new_id(self.assays,p['method'],self.next_assay_number),label=label,protocol=copy.deepcopy(p),rows=copy.deepcopy(rows or []));self.next_assay_number=int(a['id'].split('_')[0][1:])+1;self.assays.append(a);self.set_assays(self.assays,len(self.assays)-1);self.dirty=True;return a['id']
    def duplicate_assay(self):
        self.commit_active();a=next(a for a in self.assays if a['id']==self.active_id);self.append_assay(a['protocol'],a['label']+' · copia',a['rows'])
    def remove_assay(self):
        if len(self.assays)==1:raise ValueError('El experimento debe conservar al menos un ensayo')
        if QMessageBox.question(self,'Retirar ensayo','¿Retirar este ensayo de las entradas actuales? Se conservará el historial al guardar.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        self.assays=[a for a in self.assays if a['id']!=self.active_id];self.active_id=None;self.set_assays(self.assays);self.dirty=True
    def rename_assay(self):
        self.commit_active();a=next(a for a in self.assays if a['id']==self.active_id);name,ok=QInputDialog.getText(self,'Nombre del ensayo','Nombre visible',text=a['label'])
        if ok and name.strip():a['label']=name.strip();self.dirty=True;self.update_current_state()
    def clear_experiment(self):
        if not self._workspace_ready:return super().clear_experiment()
        self._excel_launch=None
        if hasattr(self,'_excel_launch_timer'):self._excel_launch_timer.stop()
        self.graph_style=DEFAULT;self.next_assay_number=1;self.saved_states={};self.folder=None;self.open_hash=None;self.active_id=None;self.set_assays([]);self.pathlabel.setText(t('Nuevo experimento sin guardar'));self.dirty=False;self.progress_panel.hide()
    def load_demo(self,multivariety=False):
        if not self.confirm_discard():return
        self.next_assay_number=1;self.saved_states={};self.folder=None;self.open_hash=None;self.active_id=None;self.set_assays([dict(id='A01_FRAP',label='FRAP · SINTÉTICO',protocol=copy.deepcopy(FE),rows=demo_varieties() if multivariety else demo_rows())]);self.pathlabel.setText(t('Demostración sin guardar'));self.dirty=False;self.log.appendPlainText('Datos sintéticos FRAP cargados; no son resultados experimentales.')
    def load_multi_demo(self,extended=False):
        if not self.confirm_discard():return
        self.next_assay_number=1;self.saved_states={};self.folder=None;self.open_hash=None;self.active_id=None;self.set_assays(multi_demo(extended));self.pathlabel.setText(t('Experimento multimétodo · SINTÉTICO'));self.dirty=False;self.log.appendPlainText('Demostración sintética con varios ensayos y las mismas tres variedades. Un Excel y un Origin; cada ensayo mantiene su propia calibración y unidad.')
    def load_folder(self,path):
        from .graph_styles import selection
        self.graph_style=selection(read_presentation(path))
        assays=experiments.read(path);self.next_assay_number=json.loads((Layout(path).meta/'experiment.json').read_text(encoding='utf-8')).get('next_assay_number',1);self.saved_states={};self.dirty=False
        report_path=Layout(path).meta/'status.json'
        if report_path.exists():self.saved_states=json.loads(report_path.read_text(encoding='utf-8')).get('assays',{})
        self.folder=Layout(path).root;self.open_hash=file_hash(Layout(path).master);self.active_id=None;self.set_assays(assays);self.pathlabel.setText(Layout(path).stem);self.dirty=False
        status=Layout(path).meta/'status.json'
        if status.exists():
            report=json.loads(status.read_text(encoding='utf-8'));self.log.appendPlainText({'complete':'Todos los ensayos calculados. Revisar QC.','partial':'Actualización parcial: revisar estados de cada ensayo.','draft':'Borradores guardados; faltan datos.','pending':'Entradas guardadas; cálculo pendiente.','failed':'No se completó la actualización.'}.get(report['state'],report['state']))
            for i,a in enumerate(self.assays):
                s=report.get('assays',{}).get(a['id'],{});self.assay_list.item(i).setToolTip(t(s.get('issue','')))
    def save(self):
        if not self.assays:raise ValueError(t('Añade un ensayo antes de guardar.'))
        self.commit_active()
        if self.folder is None:
            parent=QFileDialog.getExistingDirectory(self,'Carpeta que contendrá el experimento')
            if not parent:return
            name,ok=QInputDialog.getText(self,'Nuevo experimento','Nombre de carpeta nueva')
            if not ok:return
            if not name or name in ('.','..') or any(c in name for c in '<>:"/\\|?*'):raise ValueError('Nombre de carpeta inválido')
            path=experiments.create(Path(parent)/name,self.assays);save_presentation(path,self.graph_style);self.load_folder(path)
        else:experiments.save(self.folder,self.assays,self.open_hash);save_presentation(self.folder,self.graph_style);self.load_folder(self.folder)
        self.log.appendPlainText('Guardadas las entradas de todos los ensayos. Actualizar para calcular y exportar los completos.')
    def new_protocol(self):
        self.tabs.setCurrentWidget(self.parameters)
        self.log.appendPlainText(t('Edita las condiciones de este ensayo. Guarda una variante solo si quieres reutilizarla en otros ensayos.'))
    def prepare_protocol(self,name,index):
        import uuid
        p=copy.deepcopy(self.variants[index]);p.update(name=name,id='custom-'+uuid.uuid4().hex,version=0,status='Custom protocol');self.loading=True;self.set_protocol(p);self.populate_variants(p);self.loading=False;self.tabs.setCurrentWidget(self.parameters);self.mark_dirty()
        self.log.appendPlainText('Edita las condiciones y guarda la variante con copiar/+ para añadirla al catálogo.')
    def save_variant(self):
        p=self.protocol();validate_protocol(p);name,ok=QInputDialog.getText(self,'Guardar variante','Nombre de la nueva variante',text=p['name'])
        if not ok or not name.strip():return
        p=copy.deepcopy(p);p.update(name=name.strip(),version=int(p.get('version') or 0)+1);save_variant(self.variant_folder,p);self.variants.append(p);self.loading=True;self.set_protocol(p);self.populate_variants(p);self.loading=False;self.mark_dirty();self.log.appendPlainText('Variante guardada sin modificar versiones anteriores.')
    def open_excel(self):
        if self.proc:raise RuntimeError(t('Ya hay una actualización en curso'))
        if not self.folder:raise ValueError(t('Guardar o abrir un experimento primero'))
        from .excel_launch import launching
        launching(self,Layout(self.folder).master)
        try:super().open_excel()
        except Exception:
            self._excel_launch=None;self._excel_launch_timer.stop();raise
    def start(self,action,payload=None):
        if self.folder:
            from .excel_launch import check
            check(self)
        return super().start(action,payload)
    def open_origin(self):
        if not self.folder:raise ValueError('Guardar o abrir un experimento primero')
        report=json.loads((Layout(self.folder).meta/'status.json').read_text(encoding='utf-8'))
        origin=report.get('origin',{})
        if origin.get('master_path') is not None and origin['master_path']!=str(Layout(self.folder).master):raise ValueError(t('Actualizar y exportar en un modo Origin antes de abrir el proyecto: todavía no está confirmado para el Excel actual.'))
        if (Layout(self.folder).meta/'presentation.json').exists() and report.get('presentation_hash')!=presentation_hash(self.folder):raise ValueError(t('La personalización se guardará con el experimento. Actualiza para regenerar las figuras.'))
        if report.get('state') in ('pending','draft','failed') or not origin.get('project_saved') or origin.get('errors') or report.get('excel_sha256')!=file_hash(Layout(self.folder).master):raise ValueError('Actualizar y exportar en un modo Origin antes de abrir el proyecto: todavía no está confirmado para el Excel actual.')
        super().open_origin()
    def open_location(self,which):
        if not self.folder:raise ValueError('Guardar o abrir un experimento primero')
        path=Layout(self.folder).figures
        if len(self.assays)==1:
            candidate=path/self.assays[0]['id']
            if candidate.exists() and any(p.is_file() and p.suffix.lower() in ('.png','.svg','.pdf') for p in candidate.rglob('*')):path=candidate
        path.mkdir(parents=True,exist_ok=True);os.startfile(path)
    def poll_progress(self):
        super().poll_progress()
        self.progress.setFormat(t(self.progress.format()))
    def guard(self,callback):
        try:callback()
        except Exception as error:QMessageBox.critical(self,t('Operación no completada'),t(str(error)))
    def finished(self,code,status):
        super().finished(code,status)
        if code==0 and self.folder:
            report=json.loads((Layout(self.folder).meta/'status.json').read_text(encoding='utf-8'))
            if report['state']=='draft':self.progress.setFormat('Borradores guardados · completar los datos antes de calcular')
            if report.get('reused'):self.progress.setFormat(t('Sin cambios: Excel, Origin y exportaciones verificados'));self.log.appendPlainText(t('Sin cambios: Excel, Origin y exportaciones verificados'))
        if code!=0 and self.folder:
            from .file_access import EXCEL_IN_USE
            path=Layout(self.folder).meta/'status.json'
            try:error=json.loads(path.read_text(encoding='utf-8')).get('error','')
            except (OSError,ValueError):error=''
            try:label=json.loads((Layout(self.folder).meta/'progress.json').read_text(encoding='utf-8')).get('label','')
            except (OSError,ValueError):label=''
            if EXCEL_IN_USE in error or label==EXCEL_IN_USE:self.progress.setFormat(t(EXCEL_IN_USE));self.log.appendPlainText(t(EXCEL_IN_USE))
        self.update_current_state();self.sync_assay_controls()
