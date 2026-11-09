"""Actionable pre-export issues, in the current interface language."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QTableWidget,QTableWidgetItem,QHeaderView,QDialogButtonBox,QAbstractItemView
from .i18n import t
from .input_validation import field_label,readable

class ValidationDialog(QDialog):
    def __init__(self,parent,issues,locate,ready_count=0):
        super().__init__(parent);self.setWindowTitle(t('Revisar entradas'));self.resize(920,480)
        self.issues=issues;self.locate=locate;self.proceed_partial=False;layout=QVBoxLayout(self)
        for text in ('Se han guardado las entradas. No se ha iniciado el cálculo ni la exportación.',
                     'Corrige los campos indicados y vuelve a actualizar. Doble clic en un problema para localizarlo.'):
            label=QLabel(t(text));label.setWordWrap(True);layout.addWidget(label)
        self.table=QTableWidget(min(200,len(issues)),4);self.table.setHorizontalHeaderLabels([t('Ensayo'),t('Fila'),t('Campo'),t('Problema')])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True);self.table.verticalHeader().hide();self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch)
        for r,issue in enumerate(issues[:200]):
            for c,value in enumerate((issue['label']+' · '+issue['assay_id'],issue.get('display_row',issue['row']) or '—',field_label(issue['field']),readable(issue['message']))):
                cell=QTableWidgetItem(str(value));cell.setToolTip(str(value));self.table.setItem(r,c,cell)
        self.table.resizeRowsToContents();layout.addWidget(self.table)
        if len(issues)>200:layout.addWidget(QLabel(t('Se muestran los primeros 200 problemas.')))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close);layout.addWidget(buttons);buttons.rejected.connect(self.reject)
        close=buttons.button(QDialogButtonBox.StandardButton.Close);close.setToolTip(t('Cerrar'));close.setDefault(True)
        first=buttons.addButton(t('Ir al primer problema'),QDialogButtonBox.ButtonRole.ActionRole);first.setToolTip(t('Ir al primer problema'));first.clicked.connect(lambda:self.go(0))
        first.setAutoDefault(False)
        if ready_count:
            partial=buttons.addButton(t('Calcular solo ensayos completos')+f' ({ready_count})',QDialogButtonBox.ButtonRole.ActionRole)
            partial.setToolTip(t('Los ensayos incompletos se mantienen como borrador; solo se calculan los demás.'))
            partial.setAutoDefault(False)
            partial.clicked.connect(self.continue_partial)
        self.table.cellDoubleClicked.connect(lambda row,col:self.go(row))
    def continue_partial(self):self.proceed_partial=True;self.accept()
    def go(self,row):self.locate(self.issues[row]);self.accept()
