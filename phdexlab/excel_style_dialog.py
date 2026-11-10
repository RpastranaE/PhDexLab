"""Small workbook-style editor with a live, synthetic Excel preview."""
from PySide6.QtCore import Qt,QSignalBlocker
from PySide6.QtGui import QColor,QFont
from PySide6.QtWidgets import QDialog,QHBoxLayout,QVBoxLayout,QFormLayout,QComboBox,QSpinBox,QCheckBox,QPushButton,QColorDialog,QTableWidget,QTableWidgetItem,QHeaderView,QDialogButtonBox,QLabel,QInputDialog
from .excel_styles import PRESETS,selection,save_user_style,user_styles
from .i18n import t,add
for pair in '''Fuente tipográfica|Font family
Guardar como estilo|Save as style
Nombre del estilo|Style name
Editar color|Edit colour
Estilo del Excel|Excel style
Personalización|Appearance
Gráficas de Origin|Origin graphs
Plantilla|Preset
Encabezados|Headers
Color de sección|Section colour
Celdas editables|Editable cells
Texto de entradas|Input text
Filas alternas|Alternating rows
Altura de filas|Row height
Tamaño de letra|Font size
Vista previa|Preview
Aplicar|Apply'''.splitlines():add(*pair.split('|',1))

class ExcelStyleDialog(QDialog):
    def __init__(self,value,parent=None):
        super().__init__(parent);self.selected=selection(value);self.setWindowTitle(t('Estilo del Excel'));self.resize(930,540)
        root=QVBoxLayout(self);body=QHBoxLayout();root.addLayout(body,1);form=QFormLayout();body.addLayout(form)
        self.preset=QComboBox()
        from . import i18n
        for key,p in PRESETS.items():self.preset.addItem(p['name'] if i18n.LANGUAGE=='es' else p['en'],key)
        for item in user_styles():self.preset.addItem(item['name'],item['settings'])
        self.preset.setCurrentIndex(self.preset.findData(self.selected['preset']));form.addRow(t('Plantilla'),self.preset)
        self.colors={}
        for key,label in [('header','Encabezados'),('accent','Color de sección'),('input','Celdas editables'),('input_text','Texto de entradas'),('stripe','Filas alternas')]:
            button=QPushButton();button.setToolTip(t(label));button.clicked.connect(lambda checked=False,k=key:self.choose_color(k));form.addRow(t(label),button);self.colors[key]=button
        self.font=QComboBox();self.font.addItems(['Calibri','Arial','Aptos','Times New Roman']);self.font.setCurrentText(self.selected['font']);form.addRow(t('Fuente tipográfica'),self.font)
        self.size=QSpinBox();self.size.setRange(9,16);self.size.setValue(self.selected['font_size']);form.addRow(t('Tamaño de letra'),self.size)
        self.height=QSpinBox();self.height.setRange(22,48);self.height.setValue(self.selected['row_height']);form.addRow(t('Altura de filas'),self.height)
        self.stripe=QCheckBox(t('Filas alternas'));self.stripe.setChecked(self.selected['striped']);form.addRow(self.stripe)
        save=QPushButton(t('Guardar como estilo'));save.setToolTip(t('Guardar como estilo'));save.clicked.connect(self.save_style);form.addRow(save)
        preview=QVBoxLayout();body.addLayout(preview,1);self.preview_title=QLabel(t('Vista previa'));preview.addWidget(self.preview_title);self.preview=QTableWidget(7,4);self.preview.setHorizontalHeaderLabels(['Sample','Mean','SD','Unit']);self.preview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);self.preview.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);preview.addWidget(self.preview)
        for r,values in enumerate([['Variety A','16.00','0.80','µmol/g'],['Variety B','24.0','1.2','µmol/g'],['Variety C','32.0','1.6','µmol/g'],['','','',''],['Dilution','2','',''],['Extract volume','10','','mL'],['Mass','0.25','','g']]):
            for c,value in enumerate(values):self.preview.setItem(r,c,QTableWidgetItem(value))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t('Aplicar'));buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);root.addWidget(buttons)
        self.preset.currentIndexChanged.connect(self.change_preset)
        for widget,signal in [(self.font,self.font.currentTextChanged),(self.size,self.size.valueChanged),(self.height,self.height.valueChanged),(self.stripe,self.stripe.toggled)]:signal.connect(self.refresh)
        self.refresh()
    def choose_color(self,key):
        color=QColorDialog.getColor(QColor(self.selected[key]),self,t('Editar color'))
        if color.isValid():self.selected[key]=color.name();self.refresh()
    def change_preset(self):
        value=self.preset.currentData()
        if isinstance(value,dict):
            self.selected=selection(value)
            for widget,key in ((self.font,'font'),(self.size,'font_size'),(self.height,'row_height'),(self.stripe,'striped')):
                with QSignalBlocker(widget):
                    if widget is self.font:widget.setCurrentText(self.selected[key])
                    elif widget is self.stripe:widget.setChecked(self.selected[key])
                    else:widget.setValue(self.selected[key])
        else:self.selected=selection(dict(preset=value,font=self.font.currentText(),font_size=self.size.value(),row_height=self.height.value(),striped=self.stripe.isChecked()))
        self.refresh()
    def save_style(self):
        name,ok=QInputDialog.getText(self,t('Guardar como estilo'),t('Nombre del estilo'))
        if ok and name.strip():
            save_user_style(name,self.selected);self.preset.addItem(name.strip(),dict(self.selected))
    def refresh(self,*args):
        self.selected.update(font=self.font.currentText(),font_size=self.size.value(),row_height=self.height.value(),striped=self.stripe.isChecked());style=selection(self.selected)
        self.preview_title.setStyleSheet('font-weight:700;color:'+style['accent'])
        for key,button in self.colors.items():button.setText(style[key].upper());button.setStyleSheet('background:'+style[key]+';color:'+('#FFFFFF' if QColor(style[key]).lightness()<140 else '#203944'))
        self.preview.setFont(QFont(style['font'],style['font_size']));self.preview.horizontalHeader().setStyleSheet('QHeaderView::section {background:'+style['header']+';color:white;padding:9px;border:0}')
        for r in range(self.preview.rowCount()):
            self.preview.setRowHeight(r,style['row_height'])
            for c in range(self.preview.columnCount()):
                editable=r>=4 and c==1;cell=self.preview.item(r,c);cell.setBackground(QColor(style['input'] if editable else style['stripe'] if style['striped'] and r%2 else '#FFFFFF'));cell.setForeground(QColor(style['input_text'] if editable else '#26373D'))
    def accept(self):self.selected=selection(self.selected);super().accept()
