"""A small spreadsheet for one sample/standard/control and experimental unit."""
import uuid
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence,QColor
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QFormLayout,QHBoxLayout,QLabel,QLineEdit,QComboBox,
 QSpinBox,QTableWidget,QTableWidgetItem,QHeaderView,QDialogButtonBox,QStackedWidget,QWidget,QCheckBox,QMessageBox,QApplication,QAbstractItemView)
from .i18n import t,add
from .reading_design import configure,signal,enabled,prepare_row,OPTICAL,PARAMETERS
from .assay_engine import engine,columns
from .data_entry import number
from .ui_fields import FIELDS,KIND_LABELS
from .spreadsheet_fill import SpreadsheetFill

for pair in '''Muestra / patrón|Sample / standard
Unidad experimental / extracción|Experimental unit / extraction
Número de lecturas|Number of readings
Tipo de lectura|Reading type
Concentración del patrón|Standard concentration
Esperado del control|Expected control
Dosis final · mg/mL|Final dose · mg/mL
Tiempo de lectura · min|Reading time · min
Meseta confirmada|Plateau confirmed
Media|Mean
DE conocida (opcional)|Known SD (optional)
n conocido (opcional)|Known n (optional)
Añadir a la tabla|Add to table
Opcional|Optional
Nombre y unidad experimental son obligatorios.|Name and experimental unit are required.
Introduce los datos disponibles. Las celdas pendientes se conservan como borrador.|Enter the available data. Missing values are kept as a draft.
Las masas inicial/final son pesadas del procedimiento, no lecturas de absorbancia. No se sustituyen por una media del porcentaje final.|Initial/final masses are procedural weighings, not absorbance readings. A mean of final percentages cannot replace them.
Una fila por fracción. Otro tamizado independiente debe usar otra unidad experimental.|One row per fraction. Use another experimental unit for an independent sieving run.
Nueva entrada|New entry'''.splitlines():add(*pair.split('|',1))

class EntryGrid(SpreadsheetFill,QTableWidget):
    def __init__(self):
        super().__init__();self.init_fill();self.required_columns=set();self.setHorizontalHeader(EntryHeader(Qt.Orientation.Horizontal,self));self.setAlternatingRowColors(True);self.verticalHeader().setDefaultSectionSize(42)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked|QAbstractItemView.EditTrigger.EditKeyPressed|QAbstractItemView.EditTrigger.AnyKeyPressed)
    def keyPressEvent(self,event):
        if event.matches(QKeySequence.StandardKey.Undo):self.undo_cells();return
        if event.matches(QKeySequence.StandardKey.Redo):self.redo_cells();return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key()==Qt.Key.Key_D:self.fill_down();return
            if event.key()==Qt.Key.Key_R:self.fill_right();return
        if event.matches(QKeySequence.StandardKey.Paste):
            rows=QApplication.clipboard().text().splitlines();r=max(0,self.currentRow());c=max(0,self.currentColumn())
            if r+len(rows)>100:QMessageBox.warning(self,'PhDexLab','Maximum: 100 rows');return
            self.setRowCount(max(self.rowCount(),r+len(rows)))
            visible=[i for i in range(c,self.columnCount()) if not self.isColumnHidden(i)]
            for i,line in enumerate(rows,r):
                for col,value in zip(visible,line.split('\t')):self.setItem(i,col,QTableWidgetItem(value))
            return
        if event.matches(QKeySequence.StandardKey.Copy):
            indexes=self.selectedIndexes()
            if indexes:
                rs=sorted({i.row() for i in indexes});cs=sorted({i.column() for i in indexes})
                QApplication.clipboard().setText('\n'.join('\t'.join(self.item(r,c).text() if self.item(r,c) else '' for c in cs) for r in rs))
            return
        if event.key()==Qt.Key.Key_Delete:
            for i in self.selectedIndexes():self.setItem(i.row(),i.column(),QTableWidgetItem(''))
            return
        super().keyPressEvent(event)

class EntryHeader(QHeaderView):
    def paintSection(self,painter,rect,index):
        painter.save();super().paintSection(painter,rect,index);painter.restore()
        if index in self.parent().required_columns:
            painter.save();painter.setPen(QColor('#C73542'));painter.drawText(rect.adjusted(0,2,-8,0),Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTop,'*');painter.restore()

class MeasurementDialog(QDialog):
    def __init__(self,protocol,parent=None,existing_rows=None,roles=None):
        super().__init__(parent);self.protocol=configure(protocol,legacy=not enabled(protocol));self.e=engine(self.protocol)
        self.existing_rows=existing_rows or []
        self.setWindowTitle(t('Nueva muestra o patrón'));self.resize(980,740);layout=QVBoxLayout(self);form=QFormLayout();layout.addLayout(form)
        self.kind=QComboBox();allowed=('sample',) if self.e in ('gravimetric','sieve') else ('sample','blank') if self.e=='ec50' else ('sample','standard','blank','control')
        for kind in allowed:
            label='Control radical sin antioxidante' if kind=='blank' and self.e in ('inhibition','ec50') else KIND_LABELS[kind]
            self.kind.addItem(t(label),kind)
        for label,kind in roles or []:
            if kind in allowed and label not in KIND_LABELS.values() and label!='Control radical sin antioxidante':
                self.kind.addItem(label,kind);self.kind.setItemData(self.kind.count()-1,label,Qt.ItemDataRole.UserRole+1)
        self.name=QLineEdit();self.bio=QLineEdit('B1');self.mode=QComboBox();self.mode.addItem(t('Lecturas individuales'),'individual')
        if self.e in OPTICAL:self.mode.addItem(t('Media ya calculada'),'mean')
        self.mode.setCurrentIndex(max(0,self.mode.findData(self.protocol.get('default_entry_mode','individual'))))
        self.signal=QComboBox()
        for value,label in [('endpoint','Lectura única de absorbancia'),('delta','Incremento ΔA ya medido'),('paired','Pareja inicial/final (ΔA)')]:self.signal.addItem(t(label),value)
        self.signal.setCurrentIndex(self.signal.findData(signal(self.protocol)));self.signal.setEnabled(self.e=='colorimetric')
        self.count=QSpinBox();self.count.setRange(1,100);self.count.setValue(int(self.protocol.get('default_replicates',3)))
        for title,widget in [('Tipo de lectura',self.kind),('Muestra / patrón',self.name),('Unidad experimental / extracción',self.bio)]:form.addRow(QLabel(t(title)+' <span style="color:#C73542">*</span>'),widget)
        if self.e in OPTICAL:form.addRow(t('Señal introducida'),self.signal);form.addRow(t('Origen de la lectura'),self.mode)
        self.count_label=QLabel(t('Número de fracciones' if self.e=='sieve' else 'Número de pesadas' if self.e=='gravimetric' else 'Número de lecturas'));form.addRow(self.count_label,self.count)
        self.common={};self.common_labels={}
        keys=(['dose_mg_mL','time_min'] if self.e=='ec50' else ['concentration','expected','dilution','extract_mL','mass_g'] if self.e in OPTICAL else ['loaded_g'] if self.e=='sieve' else [])
        for key in keys:
            value=self.protocol.get({'dilution':'default_dilution','extract_mL':'default_extract_mL','mass_g':'default_mass_g'}.get(key,''),'')
            edit=QLineEdit('' if value is None else str(value));label=QLabel(t(FIELDS[key][0]).replace('\n',' ')+' <span style="color:#C73542">*</span>');edit.setToolTip(t(FIELDS[key][1]));form.addRow(label,edit);self.common[key]=edit;self.common_labels[key]=label
        self.plateau=QCheckBox(t('Meseta confirmada'))
        if self.e=='ec50':form.addRow('',self.plateau)
        note=QLabel(t('No se inventan lecturas ni una DE a partir de una media. n técnico no es n independiente.') if self.e in OPTICAL else t('Una fila por fracción. Otro tamizado independiente debe usar otra unidad experimental.') if self.e=='sieve' else t('Las masas inicial/final son pesadas del procedimiento, no lecturas de absorbancia. No se sustituyen por una media del porcentaje final.'))
        note.setWordWrap(True);layout.addWidget(note)
        self.stack=QStackedWidget();layout.addWidget(self.stack,1);self.grid=EntryGrid();self.grid.setRowCount(self.count.value());self.stack.addWidget(self.grid)
        self.keys=['A_end','A_initial'] if self.e in OPTICAL else ['lower_um','upper_um','retained_g'] if self.e=='sieve' else ['tare_g','initial_g','final_g']+(['dry_fraction'] if self.protocol.get('quantity')=='ash' and self.protocol.get('ash_basis')=='dry' else [])
        if self.e in OPTICAL and self.protocol.get('matrix_mode')=='net':self.keys.append('matrix_blank_delta')
        self.grid.setColumnCount(len(self.keys));self.grid.setHorizontalHeaderLabels([t(FIELDS[key][0]).replace('\n',' ') for key in self.keys])
        mean_widget=QWidget();mean_layout=QFormLayout(mean_widget);self.mean_inputs={}
        for key in self.keys:
            edit=QLineEdit();label=QLabel(t(FIELDS[key][0]).replace('\n',' '));mean_layout.addRow(label,edit);self.mean_inputs[key]=(edit,label)
        self.n=QLineEdit();self.sd=QLineEdit();self.n.setPlaceholderText(t('Opcional'));self.sd.setPlaceholderText(t('Opcional'))
        mean_layout.addRow(t('n conocido (opcional)'),self.n);mean_layout.addRow(t('DE conocida (opcional)'),self.sd)
        sd_note=QLabel(t(FIELDS['technical_sd'][1]));sd_note.setWordWrap(True);mean_layout.addRow(sd_note);self.stack.addWidget(mean_widget)
        self.signal_note=QLabel(t(PARAMETERS['reading_signal'][1]));self.signal_note.setWordWrap(True)
        if self.e=='colorimetric':layout.addWidget(self.signal_note)
        pending=QLabel(t('Introduce los datos disponibles. Las celdas pendientes se conservan como borrador.'));pending.setWordWrap(True);layout.addWidget(pending)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t('Añadir a la tabla'));buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
        self.count.valueChanged.connect(self.grid.setRowCount);self.mode.currentIndexChanged.connect(self.sync);self.signal.currentIndexChanged.connect(self.sync);self.kind.currentIndexChanged.connect(self.sync);self.sync();self.grid.reset_history()
        self.grid.model().rowsInserted.connect(lambda *args:self.count.setValue(self.grid.rowCount()))
        self.grid.model().rowsRemoved.connect(lambda *args:self.count.setValue(self.grid.rowCount()))
    def sync(self):
        mode=self.mode.currentData();kind=self.kind.currentData();self.stack.setCurrentIndex(1 if mode=='mean' else 0);self.count.setVisible(mode!='mean');self.count_label.setVisible(mode!='mean')
        for key,edit in self.common.items():
            used=(key in ('dose_mg_mL','time_min','loaded_g') and (key!='dose_mg_mL' or kind=='sample') or key=='concentration' and kind=='standard' or key=='expected' and kind=='control' or key in ('dilution','extract_mL','mass_g') and kind=='sample')
            edit.setVisible(used);self.common_labels[key].setVisible(used)
        paired=self.signal.currentData()=='paired' and self.e=='colorimetric'
        from .assay_engine import required
        p=dict(self.protocol,reading_signal=self.signal.currentData());needed=required(kind,p)
        self.grid.required_columns={c for c,key in enumerate(self.keys) if key in needed};self.grid.horizontalHeader().viewport().update()
        for key,(edit,label_widget) in self.mean_inputs.items():
            label_widget.setText(t(FIELDS[key][0]).replace('\n',' ')+(' <span style="color:#C73542">*</span>' if key in needed else ''))
        if self.e in OPTICAL:
            self.grid.setColumnHidden(self.keys.index('A_initial'),not paired)
            if 'matrix_blank_delta' in self.keys:
                used=not (self.e=='colorimetric' and kind=='blank')
                self.grid.setColumnHidden(self.keys.index('matrix_blank_delta'),not used)
                for widget in self.mean_inputs['matrix_blank_delta']:widget.setVisible(used)
            label=t('Absorbancia final · AU' if paired else 'Incremento ΔA · AU' if self.signal.currentData()=='delta' else 'Absorbancia · AU')
            self.grid.horizontalHeaderItem(0).setText(label);self.mean_inputs['A_end'][1].setText(t('Media')+' · '+label+' <span style="color:#C73542">*</span>')
            for widget in self.mean_inputs['A_initial']:widget.setVisible(paired)
    def data(self):
        p=configure(self.protocol,legacy=False)
        if self.e=='colorimetric':p['reading_signal']=self.signal.currentData();p['response']='endpoint' if p['reading_signal']=='endpoint' else 'delta'
        if not self.name.text().strip() or not self.bio.text().strip():raise ValueError(t('Nombre y unidad experimental son obligatorios.'))
        kind=self.kind.currentData();is_mean=self.mode.currentData()=='mean';rows=[]
        indices=list(range(1 if is_mean else self.grid.rowCount()))
        if not is_mean:
            filled=[i for i in indices if any(self.grid.item(i,c) and self.grid.item(i,c).text().strip() for c in range(self.grid.columnCount()) if not self.grid.isColumnHidden(c))]
            if filled:indices=filled  # Unused slots are not missing measurements; partial pairs remain drafts.
        for i in indices:
            row=dict.fromkeys(columns(p),'');row.update(record_id=uuid.uuid4().hex,kind=kind,sample_id=self.name.text().strip(),bio_id=self.bio.text().strip(),tech_id='mean' if is_mean else str(i+1))
            row['kind_label']=self.kind.currentData(Qt.ItemDataRole.UserRole+1) or ''
            for key,edit in self.common.items():
                if not edit.isHidden():row[key]=number(edit.text())
            for c,key in enumerate(self.keys):
                if self.grid.isColumnHidden(c):continue
                if key=='A_initial' and (self.e!='colorimetric' or p['reading_signal']!='paired'):continue
                text=self.mean_inputs[key][0].text() if is_mean else (self.grid.item(i,c).text() if self.grid.item(i,c) else '')
                row[key]=number(text)
            if self.e in OPTICAL:
                row.update(reading_basis='mean' if is_mean else 'individual',technical_n=number(self.n.text()) if is_mean else None,technical_sd=number(self.sd.text()) if is_mean else None)
                row=prepare_row(row,p)
            if self.e=='ec50':row['plateau']=self.plateau.isChecked()
            rows.append(row)
        return p,rows
    def accept(self):
        try:
            self.result_protocol,self.result_rows=self.data()
            from .reading_design import validate_groups
            validate_groups(self.existing_rows+self.result_rows,self.result_protocol)
        except (ValueError,TypeError) as error:QMessageBox.warning(self,'PhDexLab',str(error));return
        super().accept()
