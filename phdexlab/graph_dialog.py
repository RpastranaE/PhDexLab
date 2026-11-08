"""Live plot editor. Presentation stays independent of chemistry and UI theme."""
import json
from pathlib import Path
from PySide6.QtCore import Qt,QPointF
from PySide6.QtGui import QPainter,QPixmap,QColor,QPen,QPolygonF,QFont
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QLabel,QHBoxLayout,QComboBox,QDialogButtonBox,
 QTabWidget,QWidget,QFormLayout,QPushButton,QColorDialog,QCheckBox,QDoubleSpinBox,QInputDialog,QFileDialog,QMessageBox,QScrollArea)
from .graph_styles import STYLES,PALETTES,MARKERS,selection,resolved,save_user_style,user_styles
from .i18n import t,add

for pair in '''Plantilla base|Base preset
Mis estilos|My styles
Resultados|Results
Calibración|Calibration
Curvas de dosis|Dose curves
Tipografía|Typography
Paleta|Palette
Símbolo|Marker
Símbolos abiertos|Open markers
Tamaño del símbolo (pt)|Marker size (pt)
Color de barras|Bar colour
Un color por muestra|One colour per sample
Barras de error|Error bars
Tipo de línea|Line type
Grosor de línea (pt)|Line width (pt)
Fuente|Font
Títulos de ejes (pt)|Axis titles (pt)
Etiquetas de ejes (pt)|Tick labels (pt)
Guardar como estilo|Save as style
Importar estilo|Import style
Exportar estilo|Export style
Nombre del estilo|Style name
Estilo personalizado|Custom style
Patrones · Ajuste OLS|Standards · OLS fit
Aplicar paleta|Apply palette
Añadir color|Add colour
Quitar último color|Remove last colour
Vista previa ilustrativa · datos sintéticos|Illustrative preview · synthetic data
Los colores siguen el orden de muestras. La calibración tiene colores independientes para patrones y ajuste. Actualiza el experimento para aplicar los cambios.|Colours follow sample order. Calibration has independent colours for standards and fit. Update the experiment to apply changes.
El estilo no es válido.|The style is not valid.'''.splitlines():add(*pair.split('|',1))

def draw_marker(p,x,y,s,color):
    r=s['size'];p.setPen(QPen(QColor(color),1.2));p.setBrush(QColor('white') if s['open'] else QColor(color));marker=s['marker']
    if marker=='o':p.drawEllipse(QPointF(x,y),r,r)
    elif marker=='s':p.drawRect(int(x-r),int(y-r),int(2*r),int(2*r))
    else:
        coords=[(0,-r),(r,0),(0,r),(-r,0)] if marker=='D' else [(-r,r),(0,-r),(r,r)] if marker=='^' else [(-r,-r),(0,r),(r,-r)]
        p.drawPolygon(QPolygonF([QPointF(x+dx,y+dy) for dx,dy in coords]))

def preview(style,width=420,height=180,role='results'):
    if role not in style:style=resolved(next((k for k,v in STYLES.items() if v==style),'classic'))
    s=style[role];pix=QPixmap(width,height);pix.fill(QColor('white'));p=QPainter(pix);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setFont(QFont(style.get('typography',{}).get('font','Arial'),8))
    left,bottom,right,top=45,height-35,width-16,25;p.setPen(QPen(QColor('#30343B'),1.2));p.drawLine(left,top,left,bottom);p.drawLine(left,bottom,right,bottom)
    p.drawText(9,18,'FRAP' if role=='results' else 'Response');p.drawText(width//2-20,height-8,'Sample' if role=='results' else 'Concentration')
    if role=='results':
        for i,value in enumerate((.4,.65,.82)):
            x=left+(right-left)*(i+.5)/3;y=bottom-value*(bottom-top-10);color=s['colors'][i%len(s['colors'])] if s['per_sample'] else s['colors'][0]
            p.setPen(QPen(QColor(color),1));p.setBrush(QColor(color if s['per_sample'] else s['fill']));p.drawRect(int(x-23),int(y),46,int(bottom-y))
            p.setPen(QPen(QColor(s['error']),1.2));p.drawLine(QPointF(x,y-10),QPointF(x,y+10));p.drawLine(QPointF(x-5,y-10),QPointF(x+5,y-10));p.drawLine(QPointF(x-5,y+10),QPointF(x+5,y+10))
            for dx,dy in ((-10,5),(0,0),(10,-5)):draw_marker(p,x+dx,y+dy,s,color)
            p.setPen(QColor('#30343B'));p.drawText(int(x-16),bottom+17,chr(65+i))
    else:
        p.setPen(QPen(QColor(s['colors'][1]),s['width'],{'-':Qt.PenStyle.SolidLine,'--':Qt.PenStyle.DashLine,':':Qt.PenStyle.DotLine,'-.':Qt.PenStyle.DashDotLine}[s['line']]))
        p.drawLine(QPointF(left+18,bottom-10),QPointF(right-15,top+10))
        for i in range(5):
            x=left+18+i*(right-left-33)/4;y=bottom-10-i*(bottom-top-20)/4+(-2 if i%2 else 2)
            p.setPen(QPen(QColor(s['error']),1));p.drawLine(QPointF(x,y-5),QPointF(x,y+5));draw_marker(p,x,y,s,s['colors'][0])
    p.end();return pix

class GraphDialog(QDialog):
    def __init__(self,key='classic',parent=None):
        super().__init__(parent);self.setWindowTitle(t('Personalizar gráficas'));self.selected=selection(key);self.resize(1000,790);self.loading=False
        layout=QVBoxLayout(self);top=QHBoxLayout();layout.addLayout(top);self.presets=QComboBox();top.addWidget(QLabel(t('Plantilla base')));top.addWidget(self.presets,1)
        from . import i18n
        for id,s in STYLES.items():self.presets.addItem(s['en'] if i18n.LANGUAGE=='en' else s['name'],id)
        self.presets.setCurrentIndex(self.presets.findData(self.selected['style']));self.presets.activated.connect(self.load_preset)
        self.personal=QComboBox();top.addWidget(QLabel(t('Mis estilos')));top.addWidget(self.personal,1);self.reload_personal();self.personal.activated.connect(self.load_personal)
        previews=QHBoxLayout();layout.addLayout(previews);self.result_preview=QLabel();self.cal_preview=QLabel();previews.addWidget(self.result_preview);previews.addWidget(self.cal_preview)
        note=QLabel(t('Vista previa ilustrativa · datos sintéticos'));note.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.addWidget(note)
        self.tabs=QTabWidget();layout.addWidget(self.tabs,1);self.forms={};self.controls={};self.color_buttons={};self.palette_rows={}
        for role,label in [('results','Resultados'),('calibration','Calibración'),('dose','Curvas de dosis'),('typography','Tipografía')]:
            widget=QWidget();form=QFormLayout(widget);form.setSpacing(9);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(widget);self.tabs.addTab(scroll,t(label));self.forms[role]=form
            if role=='typography':
                font=QComboBox();font.addItems(['Arial','Calibri','Times New Roman','DejaVu Sans']);self.bind(role,'font',font,'Fuente')
                for field,label in [('label_size','Títulos de ejes (pt)'),('tick_size','Etiquetas de ejes (pt)')]:
                    spin=QDoubleSpinBox();spin.setRange(7,14);spin.setSingleStep(.5);self.bind(role,field,spin,label)
                continue
            row=QHBoxLayout();palette=QComboBox();palette.addItems(PALETTES);row.addWidget(palette);apply=QPushButton(t('Aplicar paleta'));apply.clicked.connect(lambda checked=False,r=role,c=palette:self.set_palette(r,PALETTES[c.currentText()]));row.addWidget(apply);form.addRow(t('Paleta'),row)
            palette_widget=QWidget();self.palette_rows[role]=QHBoxLayout(palette_widget);self.palette_rows[role].setContentsMargins(0,0,0,0);form.addRow(t('Patrones · Ajuste OLS') if role=='calibration' else '',palette_widget)
            if role!='calibration':
                row=QHBoxLayout();plus=QPushButton(t('Añadir color'));minus=QPushButton(t('Quitar último color'));row.addWidget(plus);row.addWidget(minus);plus.clicked.connect(lambda checked=False,r=role:self.resize_palette(r,1));minus.clicked.connect(lambda checked=False,r=role:self.resize_palette(r,-1));form.addRow('',row)
            shape=QComboBox()
            for text,marker in [('●  Circle','o'),('■  Square','s'),('▲  Triangle up','^'),('▼  Triangle down','v'),('◆  Diamond','D')]:shape.addItem(text,marker)
            self.bind(role,'marker',shape,'Símbolo');self.bind(role,'open',QCheckBox(),'Símbolos abiertos');size=QDoubleSpinBox();size.setRange(2,12);size.setSingleStep(.5);self.bind(role,'size',size,'Tamaño del símbolo (pt)');self.color_control(role,'error','Barras de error')
            if role=='results':self.color_control(role,'fill','Color de barras');self.bind(role,'per_sample',QCheckBox(),'Un color por muestra')
            else:
                line=QComboBox()
                for value in ('-','--',':','-.'):line.addItem({'-':'━━━━','--':'┄┄┄┄',':':'······','-.':'━·━·'}[value],value)
                self.bind(role,'line',line,'Tipo de línea');width=QDoubleSpinBox();width.setRange(.5,3);width.setSingleStep(.1);self.bind(role,'width',width,'Grosor de línea (pt)')
        note=QLabel(t('Los colores siguen el orden de muestras. La calibración tiene colores independientes para patrones y ajuste. Actualiza el experimento para aplicar los cambios.'));note.setWordWrap(True);layout.addWidget(note)
        actions=QHBoxLayout();layout.addLayout(actions)
        for label,callback in [('Guardar como estilo',self.save_style),('Importar estilo',self.import_style),('Exportar estilo',self.export_style)]:
            button=QPushButton(t(label));button.clicked.connect(callback);actions.addWidget(button)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t('Aplicar estilo'));buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons);self.populate()
    def bind(self,role,field,control,label):
        self.controls[role,field]=control;self.forms[role].addRow(t(label),control);signal=control.currentIndexChanged if isinstance(control,QComboBox) else control.toggled if isinstance(control,QCheckBox) else control.valueChanged;signal.connect(lambda *args,r=role,f=field,c=control:self.changed(r,f,c))
    def changed(self,role,field,control):
        if self.loading:return
        value=control.currentData() if isinstance(control,QComboBox) and field!='font' else control.currentText() if isinstance(control,QComboBox) else control.isChecked() if isinstance(control,QCheckBox) else control.value()
        self.selected['settings'][role][field]=value;self.redraw()
    def color_control(self,role,field,label):
        button=QPushButton();button.clicked.connect(lambda checked=False:self.choose_color(role,field));self.color_buttons[role,field]=button;self.forms[role].addRow(t(label),button)
    def choose_color(self,role,field,index=None):
        settings=self.selected['settings'][role];old=settings[field][index] if index is not None else settings[field];color=QColorDialog.getColor(QColor(old),self,t('Paleta'))
        if not color.isValid():return
        if index is None:settings[field]=color.name().upper()
        else:settings[field][index]=color.name().upper()
        self.populate()
    def set_palette(self,role,colors):self.selected['settings'][role]['colors']=list(colors[:2] if role=='calibration' else colors);self.populate()
    def resize_palette(self,role,amount):
        colors=self.selected['settings'][role]['colors']
        if amount>0 and len(colors)<12:colors.append('#4477AA')
        elif amount<0 and len(colors)>2:colors.pop()
        self.populate()
    @staticmethod
    def paint_color(button,color,number=None):
        ink='#FFFFFF' if QColor(color).lightness()<140 else '#172A30';button.setStyleSheet(f'background:{color};color:{ink};border:1px solid #75848A;border-radius:4px;padding:4px;');button.setText(str(number) if number else color);button.setToolTip(color)
    def populate(self):
        self.loading=True
        for (role,field),control in self.controls.items():
            value=self.selected['settings'][role][field]
            if isinstance(control,QComboBox):control.setCurrentIndex(control.findText(value) if field=='font' else control.findData(value))
            elif isinstance(control,QCheckBox):control.setChecked(value)
            else:control.setValue(value)
        for (role,field),button in self.color_buttons.items():self.paint_color(button,self.selected['settings'][role][field])
        for role,row in self.palette_rows.items():
            while row.count():row.takeAt(0).widget().deleteLater()
            for i,color in enumerate(self.selected['settings'][role]['colors']):
                button=QPushButton(str(i+1));button.setMinimumHeight(29);self.paint_color(button,color,i+1);button.clicked.connect(lambda checked=False,r=role,index=i:self.choose_color(r,'colors',index));row.addWidget(button)
        self.loading=False;self.redraw()
    def redraw(self):
        style=resolved(self.selected);self.result_preview.setPixmap(preview(style));self.cal_preview.setPixmap(preview(style,role='calibration'))
    def load_preset(self,index):self.selected=selection(self.presets.itemData(index));self.populate()
    def reload_personal(self):
        self.personal.clear();self.personal.addItem('—',None)
        for s in user_styles():self.personal.addItem(s['name'],s)
    def load_personal(self,index):
        value=self.personal.itemData(index)
        if value:self.selected=selection(value);self.populate()
    def save_style(self):
        name,ok=QInputDialog.getText(self,t('Guardar como estilo'),t('Nombre del estilo'))
        if ok and name.strip():save_user_style(name,self.selected);self.reload_personal();self.personal.setCurrentIndex(self.personal.findText(name.strip()))
    def import_style(self):
        path,_=QFileDialog.getOpenFileName(self,t('Importar estilo'),'','JSON (*.json)')
        if not path:return
        try:
            if Path(path).stat().st_size>100000:raise ValueError('File too large')
            self.selected=selection(json.loads(Path(path).read_text(encoding='utf-8')));self.populate()
        except (ValueError,OSError,KeyError,TypeError) as error:QMessageBox.warning(self,t('Importar estilo'),t('El estilo no es válido.')+'\n'+str(error))
    def export_style(self):
        path,_=QFileDialog.getSaveFileName(self,t('Exportar estilo'),'PhDexLab-style.json','JSON (*.json)')
        if path:Path(path).write_text(json.dumps(dict(schema=1,name=t('Estilo personalizado'),**selection(self.selected)),indent=2,ensure_ascii=False),encoding='utf-8')
