"""Real application screenshots, captured with synthetic examples in both languages."""
from pathlib import Path
from PySide6.QtCore import QUrl
from . import i18n
FILES=['start','assays','readings','replicates','calibration','conditions','dose','weighing','files','review','templates','styles']
CAPTIONS_EN=['Start with New assay. No method is selected automatically.','Add and select assays in the left column. Each retains its own protocol.','Choose a reading type, select a cell and type. Ctrl+V pastes a table.','Use distinct sample names and identify biological and technical replicates.','Standards and blanks belong to the selected assay.','Review conditions, units and dilution basis before calculating.','The DPPH example retains doses, times and plateau confirmations.','Weighing methods use their own mass-entry columns.','Save inputs, close the workbook, then Update and export.','Review assay states and controls before interpreting a result.','Data templates reuse a design; measurements are omitted by default.','Preview results, calibration and dose curves before applying a style.']
CAPTIONS_ES=['Empieza con Nuevo ensayo. No se selecciona un método automáticamente.','Añade y selecciona ensayos en la columna izquierda. Cada uno conserva su protocolo.','Elige el tipo de lectura, selecciona una celda y escribe. Ctrl+V pega una tabla.','Separa nombres de muestra e identifica réplicas biológicas y técnicas.','Patrones y blancos pertenecen al ensayo seleccionado.','Revisa condiciones, unidades y base de dilución antes de calcular.','El ejemplo DPPH conserva dosis, tiempos y confirmaciones de meseta.','Los métodos de pesadas tienen columnas propias para introducir masas.','Guarda las entradas, cierra el libro y pulsa Actualizar y exportar.','Revisa estados e incidencias antes de interpretar un resultado.','Las plantillas reutilizan un diseño; por defecto no incluyen mediciones.','Previsualiza resultados, calibración y curvas de dosis antes de aplicar un estilo.']

def illustration(index,width):
    if not 0<=index<len(FILES):return ''
    path=Path(__file__).parent/'assets/help'/i18n.LANGUAGE/(FILES[index]+'.png')
    if not path.is_file():return ''
    url=QUrl.fromLocalFile(str(path.resolve())).toString();caption=(CAPTIONS_EN if i18n.LANGUAGE=='en' else CAPTIONS_ES)[index]
    note='Illustrative screen · synthetic examples' if i18n.LANGUAGE=='en' else 'Pantalla ilustrativa · ejemplos sintéticos'
    return f'<p><b>{caption}</b></p><p><img src="{url}" width="{max(420,min(680,width-35))}"></p><p><i>{note}</i></p><hr>'
