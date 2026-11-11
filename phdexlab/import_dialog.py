"""Interactive source-column drag/drop mapping with an exact import preview."""
import csv
from pathlib import Path
from PySide6.QtCore import Qt,QMimeData,QPoint
from PySide6.QtGui import QDrag,QColor
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QSpinBox,QCheckBox,QLineEdit,
 QLabel,QTableWidget,QTableWidgetItem,QHeaderView,QSplitter,QWidget,QDialogButtonBox,QTabWidget)
from . import delimited_import as parser
from .assay_engine import columns,engine
from .reading_design import signal,matrix_mode,field_help
from .ui_fields import FIELDS,KIND_LABELS
from .i18n import t,add

for pair in '''Entrada de datos|Data entry
Preparación 1|Preparation 1
Nueva muestra o patrón|New sample or standard
Archivos de texto delimitado (*.csv *.txt *.tsv *.dat *.asc);;Todos los archivos (*)|Delimited text files (*.csv *.txt *.tsv *.dat *.asc);;All files (*)
Importar archivo…|Import file…
Importar datos|Import data
Formato del archivo|File format
Separador|Separator
Automático|Automatic
Punto y coma|Semicolon
Coma|Comma
Tabulación|Tab
Espacio|Space
Otro|Other
Separador decimal|Decimal separator
Punto|Point
Separador de miles|Thousands separator
Ninguno|None
Comillas|Quotes
Codificación|Encoding
Omitir líneas iniciales|Skip initial lines
Primera fila con encabezados|First row contains headers
Tipo si no está en el archivo|Type if absent from file
Unidad si no está en el archivo|Unit if absent from file
Columnas del archivo|File columns
Vista en PhDexLab|PhDexLab preview
Campo en PhDexLab|PhDexLab field
Columna del archivo|File column
Sin asignar|Unassigned
Buscar campo…|Find field…
Arrastra un encabezado hasta su campo de PhDexLab o elígelo en la lista.|Drag a header onto its PhDexLab field or choose it from the list.
Se añadirán las filas al ensayo actual. Puedes completar los datos pendientes después.|Rows will be added to the current assay. Missing inputs can be completed afterwards.
Elige al menos una columna para importar.|Choose at least one column to import.
Filas|Rows
Importar|Import
Cancelar|Cancel'''.splitlines():add(*pair.split('|',1))

MIME='application/x-phdexlab-source-column'


class SourceHeader(QHeaderView):
    def mousePressEvent(self,event):
        self.start=event.position().toPoint();super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if event.buttons() & Qt.MouseButton.LeftButton and (event.position().toPoint()-getattr(self,'start',QPoint())).manhattanLength()>8:
            col=self.logicalIndexAt(self.start)
            if col>=0:
                drag=QDrag(self);mime=QMimeData();mime.setData(MIME,str(col).encode());drag.setMimeData(mime);drag.exec(Qt.DropAction.CopyAction);return
        super().mouseMoveEvent(event)


class MappingTable(QTableWidget):
    def __init__(self,dialog):
        super().__init__(0,2);self.dialog=dialog;self.setAcceptDrops(True);self.viewport().setAcceptDrops(True)
    def dragEnterEvent(self,event):
        if event.mimeData().hasFormat(MIME):event.acceptProposedAction()
    def dragMoveEvent(self,event):
        if event.mimeData().hasFormat(MIME):
            row=self.rowAt(event.position().toPoint().y())
            if row>=0:self.setCurrentCell(row,0)
            event.acceptProposedAction()
    def dropEvent(self,event):
        row=self.rowAt(event.position().toPoint().y())
        if row>=0 and event.mimeData().hasFormat(MIME):
            try:column=int(bytes(event.mimeData().data(MIME)))
            except ValueError:return
            if self.dialog.assign(self.dialog.fields[row],column):event.acceptProposedAction()


class ImportDialog(QDialog):
    def __init__(self,path,protocol,existing=(),parent=None):
        super().__init__(parent)
        from .i18n_fields import register
        register();self.path=Path(path);self.protocol=protocol;self.existing=existing;self.mapping={};self.titles=[];self.data=[];self.result_rows=[];self.loading=False
        self.fields=[key for key in columns(protocol) if key not in ('record_id','kind_label')]
        self.setWindowTitle(t('Importar datos'));self.resize(1220,790);root=QVBoxLayout(self)
        file=QLabel(self.path.name);file.setToolTip(str(self.path));file.setStyleSheet('font-weight:700');root.addWidget(file)
        settings=QHBoxLayout();root.addLayout(settings);self.options={}
        groups=[QFormLayout() for _ in range(3)]
        for form in groups:settings.addLayout(form)
        def combo(key,label,values,form):
            box=QComboBox()
            for name,value in values:box.addItem(t(name),value)
            form.addRow(t(label),box);self.options[key]=box;box.currentIndexChanged.connect(self.reload);return box
        combo('delimiter','Separador',[('Automático','auto'),('Punto y coma',';'),('Coma',','),('Tabulación','\t'),('|','|'),('Espacio',' '),('Otro','custom')],groups[0])
        self.custom=QLineEdit();self.custom.setMaxLength(1);self.custom.setPlaceholderText(t('Separador'));groups[0].addRow('',self.custom);self.custom.textChanged.connect(self.reload)
        combo('decimal','Separador decimal',[('Punto','.'),('Coma',',')],groups[0])
        combo('thousands','Separador de miles',[('Ninguno',''),('Coma',','),('Punto','.'),('Espacio',' ')],groups[1])
        combo('encoding','Codificación',[('Automático','auto'),('UTF-8','utf-8-sig'),('UTF-16','utf-16'),('Windows-1252','cp1252'),('Latin-1','latin-1')],groups[1])
        combo('quote','Comillas',[('"','"'),("'","'"),('Ninguno','')],groups[1])
        self.skip=QSpinBox();self.skip.setRange(0,10000);groups[2].addRow(t('Omitir líneas iniciales'),self.skip);self.skip.valueChanged.connect(self.reload)
        self.header=QCheckBox(t('Primera fila con encabezados'));self.header.setChecked(True);groups[2].addRow(self.header);self.header.toggled.connect(self.reload)
        allowed=('sample',) if engine(protocol) in ('gravimetric','sieve') else ('sample','blank') if engine(protocol)=='ec50' else tuple(KIND_LABELS)
        self.kind=combo('kind','Tipo si no está en el archivo',[(KIND_LABELS[k],k) for k in allowed],groups[2]);self.kind.setCurrentIndex(self.kind.findData('sample'))
        self.unit=QLineEdit(t('Preparación 1'));groups[2].addRow(t('Unidad si no está en el archivo'),self.unit);self.unit.textChanged.connect(self.update_preview)
        root.addWidget(QLabel(t('Arrastra un encabezado hasta su campo de PhDexLab o elígelo en la lista.')))
        splitter=QSplitter();root.addWidget(splitter,1);self.tabs=QTabWidget();splitter.addWidget(self.tabs)
        self.source=QTableWidget();self.source.setHorizontalHeader(SourceHeader(Qt.Orientation.Horizontal,self.source));self.source.horizontalHeader().viewport().setCursor(Qt.CursorShape.OpenHandCursor);self.source.horizontalHeader().setToolTip(t('Arrastra un encabezado hasta su campo de PhDexLab o elígelo en la lista.'));self.source.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.tabs.addTab(self.source,t('Columnas del archivo'))
        self.preview=QTableWidget();self.preview.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.tabs.addTab(self.preview,t('Vista en PhDexLab'))
        right=QWidget();layout=QVBoxLayout(right);self.search=QLineEdit();self.search.setPlaceholderText(t('Buscar campo…'));layout.addWidget(self.search);self.search.textChanged.connect(self.filter_fields)
        self.targets=MappingTable(self);self.targets.setHorizontalHeaderLabels([t('Campo en PhDexLab'),t('Columna del archivo')]);self.targets.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);self.targets.verticalHeader().hide();self.targets.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);layout.addWidget(self.targets);splitter.addWidget(right);splitter.setSizes([700,480])
        self.status=QLabel();self.status.setWordWrap(True);root.addWidget(self.status)
        root.addWidget(QLabel(t('Se añadirán las filas al ensayo actual. Puedes completar los datos pendientes después.')))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);self.import_button=buttons.button(QDialogButtonBox.StandardButton.Ok);self.import_button.setText(t('Importar'));buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t('Cancelar'));buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);root.addWidget(buttons);self.reload()
    def field_label(self,key):
        label=FIELDS[key][0]
        if key=='A_end':label='Incremento ΔA · AU' if signal(self.protocol)=='delta' else 'Absorbancia final · AU' if signal(self.protocol)=='paired' else 'Absorbancia · AU'
        return t(label).replace('\n',' ')
    def provenance(self):
        import hashlib
        return dict(source_name=self.path.name,source_sha256=hashlib.sha256(self.path.read_bytes()).hexdigest(),source_columns=self.titles,mapping=self.mapping,delimiter=self.effective_delimiter,encoding=self.options['encoding'].currentData(),quote=self.options['quote'].currentData(),skip_lines=self.skip.value(),header=self.header.isChecked(),**self.kwargs)
    def filter_fields(self,text):
        for row,key in enumerate(self.fields):self.targets.setRowHidden(row,parser.normal(text) not in parser.normal(t(FIELDS[key][0])))
    def assign(self,field,column):
        if not 0<=column<len(self.titles):return False
        self.combos[field].setCurrentIndex(column+1);return True
    def reload(self,*args):
        if not hasattr(self,'targets') or self.loading:return
        try:
            delimiter=self.options['delimiter'].currentData();self.custom.setEnabled(delimiter=='custom');self.custom.setVisible(delimiter=='custom')
            text=parser.read_text(self.path,self.options['encoding'].currentData())
            titles,data,detected=parser.parse(text,self.custom.text() if delimiter=='custom' else delimiter,self.skip.value(),self.header.isChecked(),self.options['quote'].currentData())
            changed=titles!=self.titles;self.titles=titles;self.data=data;self.effective_delimiter=detected
            self.source.setColumnCount(len(titles));self.source.setHorizontalHeaderLabels(titles);self.source.setRowCount(min(100,len(data)))
            for r,row in enumerate(data[:100]):
                for c,value in enumerate(row):self.source.setItem(r,c,QTableWidgetItem(value))
            self.source.resizeColumnsToContents()
            if changed or not hasattr(self,'combos'):
                self.mapping=parser.guess(titles,self.fields);self.loading=True;self.combos={};self.targets.setRowCount(len(self.fields))
                for r,key in enumerate(self.fields):
                    label=self.field_label(key);item=QTableWidgetItem(label);item.setToolTip(t(field_help(key,self.protocol)));self.targets.setItem(r,0,item)
                    box=QComboBox();box.addItem(t('Sin asignar'),None)
                    for i,title in enumerate(titles):box.addItem(str(i+1)+': '+title,i)
                    box.setCurrentIndex(self.mapping.get(key,-1)+1);self.targets.setCellWidget(r,1,box);self.combos[key]=box;box.currentIndexChanged.connect(self.update_preview);self.targets.setRowHeight(r,38)
                self.loading=False;self.filter_fields(self.search.text())
            self.update_preview()
        except (ValueError,OSError,UnicodeError,csv.Error) as error:
            self.loading=False;self.status.setText(str(error));self.status.setStyleSheet('color:#BE3345');self.import_button.setEnabled(False)
    def update_preview(self,*args):
        if self.loading or not hasattr(self,'combos'):return
        try:
            self.mapping={key:box.currentData() for key,box in self.combos.items() if box.currentData() is not None}
            if not self.mapping:raise ValueError(t('Elige al menos una columna para importar.'))
            kwargs=dict(decimal=self.options['decimal'].currentData(),thousands=self.options['thousands'].currentData(),default_kind=self.kind.currentData(),default_unit=self.unit.text())
            preview=parser.records(self.data[:100],self.mapping,self.protocol,self.existing,**kwargs)
            self.preview.setColumnCount(len(self.fields));self.preview.setHorizontalHeaderLabels([self.field_label(k) for k in self.fields]);self.preview.setRowCount(len(preview))
            for r,row in enumerate(preview):
                for c,key in enumerate(self.fields):self.preview.setItem(r,c,QTableWidgetItem(str(row.get(key,''))))
            self.preview.resizeColumnsToContents()
            for c in range(len(self.titles)):
                self.source.horizontalHeaderItem(c).setText(('✓ ' if c in self.mapping.values() else '')+self.titles[c])
                self.source.horizontalHeaderItem(c).setBackground(QColor('#D8EFE5' if c in self.mapping.values() else '#E8F0F4'))
            self.status.setText(t('Filas')+': '+str(len(self.data)));self.status.setStyleSheet('color:#26734F');self.import_button.setEnabled(bool(self.data));self.kwargs=kwargs
        except ValueError as error:self.status.setText(str(error));self.status.setStyleSheet('color:#BE3345');self.import_button.setEnabled(False)
    def accept(self):
        try:self.result_rows=parser.records(self.data,self.mapping,self.protocol,self.existing,**self.kwargs)
        except ValueError as error:self.status.setText(str(error));self.status.setStyleSheet('color:#BE3345');return
        super().accept()
