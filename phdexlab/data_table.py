import uuid
from PySide6.QtCore import Qt,QTimer,QSignalBlocker,Signal
from PySide6.QtGui import QColor,QKeySequence
from PySide6.QtWidgets import QTableWidget,QTableWidgetItem,QStyledItemDelegate,QComboBox,QHeaderView,QAbstractItemView,QApplication,QStyleOptionComboBox,QStyle,QMenu,QInputDialog,QMessageBox
from .data_entry import COLUMNS
from .ui_fields import FIELDS,KIND_LABELS
from .i18n import t
from .i18n import add
for pair in '''Copiar|Copy
Cortar|Cut
Pegar|Paste
Borrar contenido|Clear contents
Insertar filas…|Insert rows…
Eliminar filas seleccionadas|Delete selected rows
Copiar filas|Copy rows
Pegar como filas nuevas|Paste as new rows
Número de filas|Number of rows'''.splitlines():add(*pair.split('|',1))

def required_fields(kind,protocol):
    if protocol:
        from .assay_engine import required
        return required(kind,protocol)
    return {'kind','sample_id','bio_id','tech_id','A_end','matrix_blank_delta'}

class RequiredHeader(QHeaderView):
    def paintSection(self,painter,rect,index):
        painter.save();super().paintSection(painter,rect,index);painter.restore()
        table=self.parent();row=max(0,table.currentRow());item=table.item(row,1)
        kind=item.data(Qt.ItemDataRole.UserRole) if item else None
        if table.columns[index] in required_fields(kind,table.protocol):
            painter.save();painter.setPen(QColor('#C73542'));font=painter.font();font.setBold(True);font.setPointSize(13);painter.setFont(font)
            painter.drawText(rect.adjusted(0,4,-6,0),Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTop,'*');painter.restore()

class RequiredDelegate(QStyledItemDelegate):
    def paint(self,painter,option,index):
        super().paint(painter,option,index)
        table=self.parent();item=table.item(index.row(),1);kind=item.data(Qt.ItemDataRole.UserRole) if item else None
        if kind and not index.data() and table.columns[index.column()] in required_fields(kind,table.protocol):
            painter.save();painter.setPen(QColor('#C73542'));painter.drawText(option.rect.adjusted(8,0,-8,0),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,'*');painter.restore()

class KindDelegate(QStyledItemDelegate):
    def __init__(self,table):super().__init__(table);self.table=table
    def createEditor(self,parent,option,index):
        editor=QComboBox(parent);editor.addItem(t('Elegir tipo…'),None)
        for label,kind in self.table.available_roles():
            editor.addItem(t(label),kind);editor.setItemData(editor.count()-1,label,Qt.ItemDataRole.UserRole+1)
        QTimer.singleShot(0,editor.showPopup)
        editor.activated.connect(lambda:self.commitData.emit(editor))
        return editor
    def paint(self,painter,option,index):
        combo=QStyleOptionComboBox();combo.rect=option.rect.adjusted(2,2,-2,-2);combo.currentText=t(index.data() or 'Elegir tipo…');combo.state=option.state;combo.palette=option.palette
        painter.save();style=option.widget.style()
        style.drawComplexControl(QStyle.ComplexControl.CC_ComboBox,combo,painter,option.widget)
        style.drawControl(QStyle.ControlElement.CE_ComboBoxLabel,combo,painter,option.widget);painter.restore()
    def setEditorData(self,editor,index):
        text=index.data(Qt.ItemDataRole.DisplayRole) or ''
        editor.setCurrentIndex(max(0,editor.findText(t(text))))
    def setModelData(self,editor,model,index):
        if editor.currentData() is None:
            # Choosing the placeholder explicitly clears the entire reading, including its ID.
            # A half-filled orphan reading must never silently participate in calculations.
            for column in range(self.table.columnCount()):self.table.setItem(index.row(),column,QTableWidgetItem(''))
            self.table.update_row(index.row());return
        display=editor.currentData(Qt.ItemDataRole.UserRole+1);model.setData(index,display)
        model.setData(index,editor.currentData(),Qt.ItemDataRole.UserRole)
        label='' if display==self.table.kind_names[editor.currentData()] else display
        self.table.setItem(index.row(),self.table.columns.index('kind_label'),QTableWidgetItem(label))
        self.table.update_row(index.row())

class YesNoDelegate(QStyledItemDelegate):
    def createEditor(self,parent,option,index):
        editor=QComboBox(parent);editor.addItem(t('No'),'No');editor.addItem(t('Sí'),'Sí');return editor
    def setEditorData(self,editor,index):
        from .assay_engine import yes
        editor.setCurrentIndex(1 if yes(index.data()) else 0)
    def setModelData(self,editor,model,index):model.setData(index,editor.currentData())
    def displayText(self,value,locale):return t(value)

class RawTable(QTableWidget):
    rows_edited=Signal()
    def __init__(self):
        self.columns=list(COLUMNS);self.kind_names=dict(KIND_LABELS)
        super().__init__(24,len(self.columns))
        self.protocol=None
        self.setHorizontalHeader(RequiredHeader(Qt.Orientation.Horizontal,self))
        self.setItemDelegate(RequiredDelegate(self))
        self.currentCellChanged.connect(lambda *args:self.horizontalHeader().viewport().update())
        self.roles=[(label,kind) for kind,label in self.kind_names.items()]
        self.setHorizontalHeaderLabels([t(FIELDS[k][0])+'  (?)' for k in self.columns])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setMinimumSectionSize(115);self.horizontalHeader().setFixedHeight(72)
        for c,key in enumerate(self.columns):
            self.horizontalHeaderItem(c).setToolTip(FIELDS[key][1])
            self.setColumnWidth(c,180 if key not in ('kind','sample_id','notes','matrix_blank_delta','bio_id') else 220)
        self.setColumnHidden(0,True);self.setColumnHidden(self.columns.index('kind_label'),True)
        self.setItemDelegateForColumn(self.columns.index('kind'),KindDelegate(self))
        self.setAlternatingRowColors(True);self.verticalHeader().setDefaultSectionSize(50)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked|QAbstractItemView.EditTrigger.EditKeyPressed|QAbstractItemView.EditTrigger.AnyKeyPressed)
        self.itemChanged.connect(lambda item:self.update_row(item.row()))
        self.cellClicked.connect(self.edit_kind)
        self.protocol=None
    def edit_kind(self,row,col):
        if col==1:
            if self.item(row,col) is None:self.setItem(row,col,QTableWidgetItem(''))
            self.editItem(self.item(row,col))
    def add_role(self,label,kind):
        if not label.strip() or kind not in self.kind_names:raise ValueError('Nombre o categoría no válidos')
        if any(s.casefold()==label.strip().casefold() for s,k in self.roles):raise ValueError('Ya existe ese nombre de tipo')
        self.roles.append((label.strip(),kind))
    def available_roles(self):
        from .assay_engine import engine
        e=engine(self.protocol or {})
        allowed={'sample'} if e in ('gravimetric','sieve') else {'blank','sample'} if e=='ec50' else set(KIND_LABELS)
        return [(label,kind) for label,kind in self.roles if kind in allowed]
    def set_protocol(self,p):
        from .assay_engine import columns,engine
        self.protocol=p;schema=list(columns(p));old_names=dict(self.kind_names);self.kind_names=dict(KIND_LABELS)
        if engine(p) in ('inhibition','ec50'):self.kind_names['blank']='Control radical sin antioxidante'
        custom=[(label,kind) for label,kind in self.roles if label not in old_names.values()]
        self.roles=[(label,kind) for kind,label in self.kind_names.items()]+custom
        if schema!=self.columns:
            self.blockSignals(True);self.columns=schema;self.clearContents();self.setColumnCount(len(schema))
            self.setItemDelegateForColumn(1,KindDelegate(self));self.blockSignals(False)
        self.setHorizontalHeaderLabels([t(FIELDS[k][0])+'  (?)' for k in self.columns])
        for c,key in enumerate(self.columns):
            self.setColumnHidden(c,key in ('record_id','kind_label'));self.setColumnWidth(c,205 if key in ('kind','sample_id','bio_id','notes') else 180);self.horizontalHeaderItem(c).setToolTip(t(FIELDS[key][1]))
        if 'concentration' in self.columns:self.horizontalHeaderItem(self.columns.index('concentration')).setText(t('Concentración\ndel patrón')+'\n'+p['concentration_unit'].replace('umol','µmol')+'  (?)')
        if 'expected' in self.columns:self.horizontalHeaderItem(self.columns.index('expected')).setText(t('Esperado del control')+'\n'+p['concentration_unit'].replace('umol','µmol')+'  (?)')
        if 'plateau' in self.columns:self.setItemDelegateForColumn(self.columns.index('plateau'),YesNoDelegate(self))
        self.horizontalHeader().viewport().update()
        for r in range(self.rowCount()):self.update_row(r)
    def keyPressEvent(self,event):
        if event.matches(QKeySequence.StandardKey.Copy):self.copy_cells();return
        if event.matches(QKeySequence.StandardKey.Cut):self.copy_cells();self.clear_cells();return
        if event.matches(QKeySequence.StandardKey.Paste):
            self.run_action(lambda:self.paste(QApplication.clipboard().text()));return
        if event.key()==Qt.Key.Key_Delete:self.clear_cells();return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() in (Qt.Key.Key_Plus,Qt.Key.Key_Equal):self.run_action(self.insert_rows);return
            if event.key()==Qt.Key.Key_Minus:self.delete_rows();return
        super().keyPressEvent(event)
    def copy_cells(self,whole_rows=False):
        indexes=self.selectedIndexes()
        if not indexes:return
        rows=sorted({i.row() for i in indexes});cols=([c for c in range(self.columnCount()) if not self.isColumnHidden(c)] if whole_rows else sorted({i.column() for i in indexes if not self.isColumnHidden(i.column())}))
        selected={(i.row(),i.column()) for i in indexes}
        def value(r,c):
            item=self.item(r,c)
            if not item or (not whole_rows and (r,c) not in selected):return ''
            if self.columns[c]=='kind':return item.data(Qt.ItemDataRole.UserRole) or item.text()
            return item.text()
        QApplication.clipboard().setText('\n'.join('\t'.join(value(r,c) for c in cols) for r in rows))
    def clear_cells(self):
        indexes=list(self.selectedIndexes());rows={i.row() for i in indexes}
        with QSignalBlocker(self):
            for index in indexes:
                if self.isColumnHidden(index.column()):continue
                item=self.item(index.row(),index.column())
                if item:
                    item.setText('')
                    if self.columns[index.column()]=='kind':item.setData(Qt.ItemDataRole.UserRole,None)
            for row in rows:
                if any(i.row()==row and self.columns[i.column()]=='kind' for i in indexes):
                    self.setItem(row,self.columns.index('kind_label'),QTableWidgetItem(''))
                self.update_row(row)
        if indexes:self.rows_edited.emit()
    def insert_rows(self,count=None):
        if count is None:
            count,ok=QInputDialog.getInt(self,t('Insertar filas…'),t('Número de filas'),1,1,10000)
            if not ok:return
        row=max(0,self.currentRow())
        if self.rowCount()+count>10000:raise ValueError('Maximum: 10000 rows')
        for _ in range(count):self.insertRow(row)
        self.clearSelection()
        self.setCurrentCell(row,1)
        self.rows_edited.emit()
    def delete_rows(self):
        for row in sorted({i.row() for i in self.selectedIndexes()},reverse=True):self.removeRow(row)
        # Row removal has no itemChanged signal; notify the workspace explicitly.
        self.rows_edited.emit()
    def paste_rows(self):
        text=QApplication.clipboard().text();count=len(text.splitlines())
        if not count:return
        row=max(0,self.currentRow());self.insert_rows(count);self.setCurrentCell(row,1);self.paste(text)
    def contextMenuEvent(self,event):
        index=self.indexAt(event.pos())
        if index.isValid() and not self.selectionModel().isSelected(index):self.setCurrentCell(index.row(),index.column())
        menu=QMenu(self)
        for label,callback,shortcut in [('Copiar',self.copy_cells,'Ctrl+C'),('Cortar',lambda:(self.copy_cells(),self.clear_cells()),'Ctrl+X'),('Pegar',lambda:self.paste(QApplication.clipboard().text()),'Ctrl+V'),('Borrar contenido',self.clear_cells,'Del')]:
            action=menu.addAction(t(label));action.setShortcut(shortcut);action.triggered.connect(lambda checked=False,f=callback:self.run_action(f))
        menu.addSeparator()
        for label,callback in [('Insertar filas…',self.insert_rows),('Eliminar filas seleccionadas',self.delete_rows),('Copiar filas',lambda:self.copy_cells(True)),('Pegar como filas nuevas',self.paste_rows)]:
            menu.addAction(t(label)).triggered.connect(lambda checked=False,f=callback:self.run_action(f))
        menu.exec(event.globalPos())
    def run_action(self,callback):
        try:callback()
        except (ValueError,TypeError) as error:QMessageBox.warning(self,t('Datos'),str(error))
    def paste(self,text):
        matrix=[line.split('\t') for line in text.splitlines()] if text else [['']]
        if not matrix:return
        start=max(0,self.currentRow());col=max(1,self.currentColumn());keys=None
        if matrix[0] in (self.columns,self.columns[:14]):keys=matrix.pop(0)
        elif matrix[0]==[FIELDS[k][0].replace('\n',' ') for k in self.columns[1:14]]:matrix.pop(0);col=1
        if start+len(matrix)>10000:raise ValueError('Maximum: 10000 rows')
        visible=[c for c in range(col,len(self.columns)) if not self.isColumnHidden(c)]
        changes=[]
        for r,line in enumerate(matrix,start):
            for offset,val in enumerate(line):
                c=self.columns.index(keys[offset]) if keys and offset<len(keys) else (visible[offset] if offset<len(visible) else len(self.columns))
                if c>=len(self.columns):break
                if self.columns[c] in ('record_id','kind_label'):continue
                item=QTableWidgetItem(val)
                if self.columns[c]=='kind' and val.strip():
                    kind=val if val in self.kind_names else next((k for label,k in self.roles if val in (label,t(label))),None)
                    if kind is None:raise ValueError(f'Unknown reading type: {val}')
                    item.setText(self.kind_names[kind] if val in self.kind_names else val);item.setData(Qt.ItemDataRole.UserRole,kind)
                changes.append((r,c,item))
        # Validate first, then commit once: no partial paste and no repeated whole-table scans.
        with QSignalBlocker(self):
            self.setRowCount(max(self.rowCount(),start+len(matrix)))
            for r,c,item in changes:
                self.setItem(r,c,item)
                if self.columns[c]=='kind':
                    kind=item.data(Qt.ItemDataRole.UserRole);label=item.text() if kind and item.text()!=self.kind_names.get(kind) else ''
                    self.setItem(r,self.columns.index('kind_label'),QTableWidgetItem(label))
            for r in range(start,start+len(matrix)):self.update_row(r)
        if changes:self.rows_edited.emit()
    def load(self,rows):
        self.blockSignals(True);self.clearContents();self.setRowCount(max(24,len(rows)+5))
        for r,d in enumerate(rows):
            for c,key in enumerate(self.columns):
                value=d.get(key,'');item=QTableWidgetItem('' if value is None else str(value))
                if key=='plateau':
                    from .assay_engine import yes
                    item.setText('Sí' if yes(value) else 'No')
                if key=='kind':
                    display=d.get('kind_label') or self.kind_names.get(value,value)
                    if display and (display,value) not in self.roles:self.roles.append((display,value))
                    item.setText(display);item.setData(Qt.ItemDataRole.UserRole,value)
                item.setToolTip(t(FIELDS[key][1]));self.setItem(r,c,item)
        self.blockSignals(False)
        for r in range(len(rows)):self.update_row(r)
    def records(self):
        records=[]
        for r in range(self.rowCount()):
            d={k:self.item(r,c).text() if self.item(r,c) else '' for c,k in enumerate(self.columns)}
            if not any(d[k].strip() for k in self.columns if k not in ('record_id','kind_label')):continue
            item=self.item(r,1)
            d['kind']=(item.data(Qt.ItemDataRole.UserRole) if item else None) or next((k for label,k in self.roles if label==d['kind']),d['kind'])
            if not d['record_id']:
                d['record_id']=uuid.uuid4().hex
                self.setItem(r,0,QTableWidgetItem(d['record_id']))
            if item and item.text()!=self.kind_names.get(d['kind']):d['kind_label']=item.text()
            records.append(d)
        return records
    def update_row(self,row):
        if row>=self.rowCount():return
        was_blocked=self.blockSignals(True)
        item=self.item(row,1);kind=item.data(Qt.ItemDataRole.UserRole) if item else None
        if not kind and item:kind=next((k for label,k in self.roles if label==item.text()),item.text())
        tint={'sample':'#E9F6F2','standard':'#EDF3FE','blank':'#F0F2F5','control':'#FFF3DF'}.get(kind,'#FFFFFF')
        irrelevant=set()
        if kind in ('blank','sample'):irrelevant|={'concentration'}
        if kind!='sample':irrelevant|={'dilution','extract_mL','mass_g'}
        if kind!='control':irrelevant|={'expected'}
        if self.protocol and self.protocol['response']=='endpoint':irrelevant|={'A_initial'}
        for c,key in enumerate(self.columns):
            cell=self.item(row,c)
            if cell:
                dark=getattr(self,'dark',False)
                dark_tint={'sample':'#24463F','standard':'#2A3F5C','blank':'#34404D','control':'#51452B'}.get(kind,'#20313D')
                cell.setBackground(QColor((dark_tint if dark else tint) if key=='kind' else (('#293A46' if dark else '#F2F4F7') if key in irrelevant else ('#20313D' if dark else '#FFFFFF'))))
                cell.setForeground(QColor(('#8295A2' if dark else '#87939D') if key in irrelevant else ('#E2EAF0' if dark else '#203944')))
                cell.setToolTip(t(FIELDS[key][1])+ ('\n\n'+t('No se utiliza en esta categoría/protocolo.') if key in irrelevant else ''))
        self.blockSignals(was_blocked)
