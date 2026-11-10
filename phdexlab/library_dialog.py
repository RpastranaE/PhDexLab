"""A searchable library manager with explicit removal and experiment preservation."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QTableWidget,QTableWidgetItem,
    QHeaderView,QAbstractItemView,QPushButton,QDialogButtonBox,QMessageBox)
from . import libraries
from .i18n import add,t
from .protocol_texts import display_value
from .ui_icons import icon

for pair in '''Biblioteca de plantillas y protocolos|Template and protocol library
Gestionar plantillas de datos|Manage data templates
Gestionar variantes de protocolo|Manage protocol variants
Buscar por nombre o método…|Search by name or method…
Nombre|Name
Versión|Version
Procedencia|Library source
Incluido|Included
Personal|Custom
Oculto|Hidden
Eliminar de la biblioteca|Delete from library
Restaurar protocolo incluido|Restore included protocol
La eliminación afecta solo a la biblioteca. Los datos y protocolos de los experimentos permanecen intactos.|Removal affects only the library. Experiment data and protocol snapshots remain intact.
Los protocolos incluidos se ocultan del catálogo y pueden restaurarse aquí.|Included protocols are hidden from the catalogue and can be restored here.
Las plantillas y variantes personales se eliminan de la biblioteca tras confirmar.|Custom templates and variants are deleted from the library after confirmation.
¿Eliminar esta entrada de la biblioteca?|Delete this library entry?
Los experimentos existentes conservarán su copia. El archivo personal se eliminará.|Existing experiments will retain their copy. The personal library file will be deleted.
Este protocolo incluido se ocultará del catálogo. Podrás restaurarlo aquí.|This included protocol will be hidden from the catalogue. You can restore it here.
No hay entradas que coincidan.|No matching entries.
La entrada ya no existe. Actualiza la biblioteca.|The entry no longer exists. Refresh the library.
La entrada ha cambiado. Actualiza la biblioteca antes de eliminarla.|The entry has changed. Refresh the library before deleting it.
Actualizar biblioteca|Refresh library
No hay variantes visibles para este método. Restaura una desde la biblioteca.|No visible variants for this method. Restore one from the library.'''.splitlines():add(*pair.split('|',1))

class LibraryDialog(QDialog):
    def __init__(self,kind,parent=None,folder=None):
        super().__init__(parent);self.kind=kind;self.folder=folder;self.changed=False;self.items=[]
        self.setWindowTitle(t('Gestionar plantillas de datos' if kind=='data' else 'Gestionar variantes de protocolo'));self.resize(900,530)
        layout=QVBoxLayout(self)
        for text in ('La eliminación afecta solo a la biblioteca. Los datos y protocolos de los experimentos permanecen intactos.',
                     'Los protocolos incluidos se ocultan del catálogo y pueden restaurarse aquí.' if kind=='protocol' else 'Las plantillas y variantes personales se eliminan de la biblioteca tras confirmar.'):
            label=QLabel(t(text));label.setWordWrap(True);layout.addWidget(label)
        self.search=QLineEdit();self.search.setPlaceholderText(t('Buscar por nombre o método…'));layout.addWidget(self.search)
        self.table=QTableWidget(0,4);self.table.setHorizontalHeaderLabels([t(x) for x in ('Nombre','Método','Versión','Procedencia')])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);self.table.setAlternatingRowColors(True);self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        for column in (1,2,3):self.table.horizontalHeader().setSectionResizeMode(column,QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table);self.empty=QLabel(t('No hay entradas que coincidan.'));layout.addWidget(self.empty)
        row=QHBoxLayout();layout.addLayout(row)
        self.delete=QPushButton(t('Eliminar de la biblioteca'));self.delete.setIcon(icon('close'));self.delete.setToolTip(self.delete.text());self.delete.clicked.connect(self.remove_selected);row.addWidget(self.delete)
        self.restore=QPushButton(t('Restaurar protocolo incluido'));self.restore.setIcon(icon('refresh'));self.restore.setToolTip(self.restore.text());self.restore.clicked.connect(self.restore_selected);row.addWidget(self.restore);self.restore.setVisible(kind=='protocol')
        refresh=QPushButton(t('Actualizar biblioteca'));refresh.setIcon(icon('refresh'));refresh.setToolTip(refresh.text());refresh.clicked.connect(self.reload);row.addWidget(refresh);row.addStretch()
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
        buttons.button(QDialogButtonBox.StandardButton.Close).setToolTip(t('Cerrar'))
        for button in (self.delete,self.restore,refresh):button.setAutoDefault(False)
        self.search.textChanged.connect(self.filter);self.table.itemSelectionChanged.connect(self.selection_changed);self.reload()
    def reload(self):
        self.items=libraries.entries(self.kind,self.folder,True);self.filter()
    def filter(self,*args):
        query=self.search.text().strip().casefold();self.visible=[entry for entry in self.items if query in (str(entry['payload']['name'])+' '+entry['payload']['method']).casefold()]
        self.table.setRowCount(len(self.visible))
        for row,entry in enumerate(self.visible):
            from .method_catalog import METHOD_NAMES
            p=entry['payload'];values=(display_value('name',p['name']) if self.kind=='protocol' else p['name'],t(METHOD_NAMES.get(p['method'],p['method'])),p.get('version','—'),t('Oculto' if entry['hidden'] else 'Incluido' if entry['included'] else 'Personal'))
            for col,value in enumerate(values):
                item=QTableWidgetItem(str(value));item.setToolTip(str(value));self.table.setItem(row,col,item)
        self.empty.setVisible(not self.visible)
        if self.visible:self.table.selectRow(0)
        self.selection_changed()
    def selected(self):
        row=self.table.currentRow();return self.visible[row] if 0<=row<len(self.visible) else None
    def selection_changed(self):
        entry=self.selected();self.delete.setEnabled(bool(entry and not entry['hidden']));self.restore.setEnabled(bool(entry and entry['included'] and entry['hidden']))
    def remove_selected(self):
        entry=self.selected()
        if not entry or entry['hidden']:return
        dialog=QMessageBox(self);dialog.setWindowTitle(t('Eliminar de la biblioteca'));dialog.setText(t('¿Eliminar esta entrada de la biblioteca?'))
        dialog.setInformativeText(str(entry['payload']['name'])+'\n\n'+t('Este protocolo incluido se ocultará del catálogo. Podrás restaurarlo aquí.' if entry['included'] else 'Los experimentos existentes conservarán su copia. El archivo personal se eliminará.'))
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No);dialog.setDefaultButton(QMessageBox.StandardButton.No)
        if dialog.exec()!=QMessageBox.StandardButton.Yes:return
        try:libraries.remove(self.kind,entry,self.folder);self.changed=True;self.reload()
        except (OSError,ValueError) as error:QMessageBox.warning(self,t('Eliminar de la biblioteca'),t(str(error)));self.reload()
    def restore_selected(self):
        entry=self.selected()
        if entry and entry['included'] and entry['hidden']:libraries.restore(entry);self.changed=True;self.reload()
