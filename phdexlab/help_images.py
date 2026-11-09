"""Real application screenshots, captured with synthetic examples in both languages."""
from pathlib import Path
from PySide6.QtCore import QUrl,Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QScrollArea,QPushButton,QSlider
from . import i18n
FILES=['start','assays','readings','replicates','calibration','conditions','dose','weighing','files','review','templates','styles']
CAPTIONS_EN=['Start with New assay. No method is selected automatically.','Add and select assays in the left column. Each retains its own protocol.','Use the pipette to enter individual readings or a precomputed mean.','Use distinct sample names and identify biological and technical replicates.','Standards and blanks belong to the selected assay.','Review conditions, units and dilution basis before calculating.','The DPPH example retains doses, times and plateau confirmations.','Weighing methods use their own mass-entry columns.','Save inputs, close the workbook, then Update and export.','Review assay states and controls before interpreting a result.','Data templates reuse a design; measurements are omitted by default.','Preview results, calibration and dose curves before applying a style.']
CAPTIONS_ES=['Empieza con Nuevo ensayo. No se selecciona un método automáticamente.','Añade y selecciona ensayos en la columna izquierda. Cada uno conserva su protocolo.','Usa la pipeta para introducir lecturas individuales o una media ya calculada.','Separa nombres de muestra e identifica réplicas biológicas y técnicas.','Patrones y blancos pertenecen al ensayo seleccionado.','Revisa condiciones, unidades y base de dilución antes de calcular.','El ejemplo DPPH conserva dosis, tiempos y confirmaciones de meseta.','Los métodos de pesadas tienen columnas propias para introducir masas.','Guarda las entradas, cierra el libro y pulsa Actualizar y exportar.','Revisa estados e incidencias antes de interpretar un resultado.','Las plantillas reutilizan un diseño; por defecto no incluyen mediciones.','Previsualiza resultados, calibración y curvas de dosis antes de aplicar un estilo.']

def illustration(index,width):
    if not 0<=index<len(FILES):return ''
    path=Path(__file__).parent/'assets/help'/i18n.LANGUAGE/(FILES[index]+'.png')
    if not path.is_file():return ''
    url=QUrl.fromLocalFile(str(path.resolve())).toString();caption=(CAPTIONS_EN if i18n.LANGUAGE=='en' else CAPTIONS_ES)[index]
    note='Illustrative screen · synthetic examples' if i18n.LANGUAGE=='en' else 'Pantalla ilustrativa · ejemplos sintéticos'
    zoom='Click the image to enlarge' if i18n.LANGUAGE=='en' else 'Pulsa la imagen para ampliarla'
    return f'<p><b>{caption}</b></p><p><a href="phdexlab-help:{index}"><img src="{url}" width="{max(200,width-35)}"></a></p><p><i>{note} · {zoom}</i></p><hr>'

class ImageViewer(QDialog):
    """Keep the original raster; resize from it on each zoom, never from a thumbnail."""
    def __init__(self,index,parent=None):
        super().__init__(parent);self.setWindowTitle(CAPTIONS_EN[index] if i18n.LANGUAGE=='en' else CAPTIONS_ES[index]);self.resize(1100,760)
        self.original=QPixmap(str(Path(__file__).parent/'assets/help'/i18n.LANGUAGE/(FILES[index]+'.png')))
        self.original.setDevicePixelRatio(1)
        layout=QVBoxLayout(self);self.scroll=QScrollArea();self.label=QLabel();self.label.setAlignment(Qt.AlignmentFlag.AlignCenter);self.scroll.setWidget(self.label);layout.addWidget(self.scroll,1)
        controls=QHBoxLayout();layout.addLayout(controls)
        fit=QPushButton('Fit to window' if i18n.LANGUAGE=='en' else 'Ajustar a ventana');actual=QPushButton('100%');self.zoom=QSlider(Qt.Orientation.Horizontal);self.zoom.setRange(20,200)
        for widget in (fit,actual,self.zoom):controls.addWidget(widget)
        self.zoom.valueChanged.connect(self.render);fit.clicked.connect(self.fit);actual.clicked.connect(lambda:self.zoom.setValue(100))
        self.zoom.setValue(50)
    def fit(self):
        self.zoom.setValue(max(20,min(200,int(100*min((self.scroll.viewport().width()-12)/self.original.width(),(self.scroll.viewport().height()-12)/self.original.height())))))
    def render(self,value):
        size=self.original.size()*float(value/100);self.label.setPixmap(self.original.scaled(size,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));self.label.adjustSize()
