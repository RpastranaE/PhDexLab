"""Small workbook-style editor with a live, synthetic Excel preview."""
from PySide6.QtCore import Qt,QSignalBlocker
from PySide6.QtGui import QColor,QFont
from PySide6.QtWidgets import QDialog,QHBoxLayout,QVBoxLayout,QFormLayout,QComboBox,QSpinBox,QCheckBox,QPushButton,QColorDialog,QTableWidget,QTableWidgetItem,QHeaderView,QDialogButtonBox,QLabel,QInputDialog,QTabWidget,QWidget
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
Texto de encabezados|Header text
Texto general|Body text
Fondo|Background
Color de bordes|Border colour
Bordes|Borders
Sin bordes|No borders
Horizontales|Horizontal
Todos|All
Alineación|Alignment
Izquierda|Left
Centro|Centre
Derecha|Right
Tamaño de encabezados|Header font size
Tamaño de secciones|Section font size
Tamaño del título|Title font size
Altura de encabezados|Header height
Anchura de columnas (%)|Column width (%)
Líneas de cuadrícula|Gridlines
Colores|Colours
Distribución|Layout
Aplicar|Apply'''.splitlines():add(*pair.split('|',1))

class ExcelStyleDialog(QDialog):
    def __init__(self,value,parent=None):
        super().__init__(parent);self.selected=selection(value);self.setWindowTitle(t('Estilo del Excel'));self.resize(1060,650)
        root=QVBoxLayout(self);body=QHBoxLayout();root.addLayout(body,1);tabs=QTabWidget();body.addWidget(tabs);tabs.setMaximumWidth(400)
        forms=[]
        for label in ('Colores','Distribución'):
            page=QWidget();layout=QFormLayout(page);tabs.addTab(page,t(label));forms.append(layout)
        form=forms[0]
        self.preset=QComboBox()
        from . import i18n
        for key,p in PRESETS.items():self.preset.addItem(p['name'] if i18n.LANGUAGE=='es' else p['en'],key)
        for item in user_styles():self.preset.addItem(item['name'],item['settings'])
        self.preset.setCurrentIndex(self.preset.findData(self.selected['preset']));form.addRow(t('Plantilla'),self.preset)
        self.colors={}
        for key,label in [('header','Encabezados'),('accent','Color de sección'),('input','Celdas editables'),('input_text','Texto de entradas'),('stripe','Filas alternas'),('header_text','Texto de encabezados'),('text','Texto general'),('background','Fondo'),('border_color','Color de bordes')]:
            button=QPushButton();button.setToolTip(t(label));button.clicked.connect(lambda checked=False,k=key:self.choose_color(k));form.addRow(t(label),button);self.colors[key]=button
        form=forms[1]
        self.controls={}
        self.font=QComboBox();self.font.addItems(['Calibri','Arial','Aptos','Times New Roman']);self.font.setCurrentText(self.selected['font']);form.addRow(t('Fuente tipográfica'),self.font)
        self.size=QSpinBox();self.size.setRange(9,16);self.size.setValue(self.selected['font_size']);form.addRow(t('Tamaño de letra'),self.size)
        self.height=QSpinBox();self.height.setRange(22,48);self.height.setValue(self.selected['row_height']);form.addRow(t('Altura de filas'),self.height)
        self.stripe=QCheckBox(t('Filas alternas'));self.stripe.setChecked(self.selected['striped']);form.addRow(self.stripe)
        for key,label,low,high in [('header_size','Tamaño de encabezados',9,20),('section_size','Tamaño de secciones',10,24),('title_size','Tamaño del título',12,28),('header_height','Altura de encabezados',36,100),('column_scale','Anchura de columnas (%)',75,150)]:
            widget=QSpinBox();widget.setRange(low,high);widget.setValue(self.selected[key]);form.addRow(t(label),widget);self.controls[key]=widget;widget.valueChanged.connect(self.refresh)
        for key,label,options in [('border','Bordes',[('none','Sin bordes'),('horizontal','Horizontales'),('all','Todos')]),('alignment','Alineación',[('left','Izquierda'),('center','Centro'),('right','Derecha')])]:
            widget=QComboBox()
            for code,name in options:widget.addItem(t(name),code)
            widget.setCurrentIndex(widget.findData(self.selected[key]));form.addRow(t(label),widget);self.controls[key]=widget;widget.currentIndexChanged.connect(self.refresh)
        self.grid=QCheckBox(t('Líneas de cuadrícula'));self.grid.setChecked(self.selected['gridlines']);form.addRow(self.grid)
        save=QPushButton(t('Guardar como estilo'));save.setToolTip(t('Guardar como estilo'));save.clicked.connect(self.save_style);form.addRow(save)
        preview=QVBoxLayout();body.addLayout(preview,1);self.preview_title=QLabel(t('Vista previa'));preview.addWidget(self.preview_title);self.section_title=QLabel('Final results');preview.addWidget(self.section_title);self.preview=QTableWidget(7,4);self.preview.setHorizontalHeaderLabels(['Sample','Mean','SD','Unit']);self.preview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive);self.preview.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);preview.addWidget(self.preview)
        for r,values in enumerate([['Variety A','16.00','0.80','µmol/g'],['Variety B','24.0','1.2','µmol/g'],['Variety C','32.0','1.6','µmol/g'],['','','',''],['Dilution','2','',''],['Extract volume','10','','mL'],['Mass','0.25','','g']]):
            for c,value in enumerate(values):self.preview.setItem(r,c,QTableWidgetItem(value))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t('Aplicar'));buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);root.addWidget(buttons)
        self.preset.currentIndexChanged.connect(self.change_preset)
        for widget,signal in [(self.font,self.font.currentTextChanged),(self.size,self.size.valueChanged),(self.height,self.height.valueChanged),(self.stripe,self.stripe.toggled),(self.grid,self.grid.toggled)]:signal.connect(self.refresh)
        self.refresh()
    def choose_color(self,key):
        color=QColorDialog.getColor(QColor(self.selected[key]),self,t('Editar color'))
        if color.isValid():self.selected[key]=color.name();self.refresh()
    def change_preset(self):
        value=self.preset.currentData()
        if isinstance(value,dict):self.selected=selection(value)
        else:self.selected=selection(dict(self.selected,preset=value,**{k:v for k,v in PRESETS[value].items() if k not in ('name','en')}))
        for widget,key in ((self.font,'font'),(self.size,'font_size'),(self.height,'row_height'),(self.stripe,'striped'),(self.grid,'gridlines'),*((w,k) for k,w in self.controls.items())):
            with QSignalBlocker(widget):
                if isinstance(widget,QComboBox):
                    if widget is self.font:widget.setCurrentText(self.selected[key])
                    else:widget.setCurrentIndex(widget.findData(self.selected[key]))
                elif isinstance(widget,QCheckBox):widget.setChecked(self.selected[key])
                else:widget.setValue(self.selected[key])
        self.refresh()
    def save_style(self):
        name,ok=QInputDialog.getText(self,t('Guardar como estilo'),t('Nombre del estilo'))
        if ok and name.strip():
            save_user_style(name,self.selected);self.preset.addItem(name.strip(),dict(self.selected))
    def refresh(self,*args):
        if not hasattr(self,'preview'):return
        self.selected.update({key:widget.currentData() if isinstance(widget,QComboBox) else widget.value() for key,widget in self.controls.items()});self.selected['gridlines']=self.grid.isChecked()
        self.selected.update(font=self.font.currentText(),font_size=self.size.value(),row_height=self.height.value(),striped=self.stripe.isChecked());style=selection(self.selected)
        self.preview_title.setStyleSheet('font-family:"'+style['font']+'";font-weight:700;font-size:'+str(style['title_size'])+'pt;color:'+style['accent'])
        self.section_title.setStyleSheet('font-family:"'+style['font']+'";font-weight:700;font-size:'+str(style['section_size'])+'pt;color:'+style['accent'])
        for key,button in self.colors.items():button.setText(style[key].upper());button.setStyleSheet('background:'+style[key]+';color:'+('#FFFFFF' if QColor(style[key]).lightness()<140 else '#203944'))
        self.preview.setFont(QFont(style['font'],style['font_size']));self.preview.horizontalHeader().setStyleSheet('QHeaderView::section {font-family:"'+style['font']+'";background:'+style['header']+';color:'+style['header_text']+';font-size:'+str(style['header_size'])+'pt;padding:9px;border:0}')
        self.preview.horizontalHeader().setFixedHeight(style['header_height']);self.preview.setShowGrid(style['gridlines'] or style['border']=='all')
        self.preview.setStyleSheet('QTableView {font-family:"'+style['font']+'";font-size:'+str(style['font_size'])+'pt;gridline-color:'+style['border_color']+'}'+(' QTableView::item {border-bottom:1px solid '+style['border_color']+'}' if style['border']=='horizontal' else ''))
        for c in range(self.preview.columnCount()):self.preview.setColumnWidth(c,round(130*style['column_scale']/100))
        for r in range(self.preview.rowCount()):
            self.preview.setRowHeight(r,style['row_height'])
            for c in range(self.preview.columnCount()):
                editable=r>=4 and c==1;cell=self.preview.item(r,c);cell.setBackground(QColor(style['input'] if editable else style['stripe'] if style['striped'] and r%2 else style['background']));cell.setForeground(QColor(style['input_text'] if editable else style['text']));cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter|{'left':Qt.AlignmentFlag.AlignLeft,'center':Qt.AlignmentFlag.AlignHCenter,'right':Qt.AlignmentFlag.AlignRight}[style['alignment']])
    def accept(self):self.selected=selection(self.selected);super().accept()
