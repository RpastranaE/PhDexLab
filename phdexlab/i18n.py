"""Small explicit ES/EN catalogue. Internal IDs, protocol data and scientific figures do not translate."""
import re
LANGUAGE='es'
CATALOG={}
def add(source,target):CATALOG[source]=target
def set_language(language):
    global LANGUAGE
    LANGUAGE=language if language in ('es','en') else 'es'

PAIRS='''Nuevo experimento|New experiment
Abrir experimento|Open experiment
Cerrar experimento|Close experiment
Nuevo experimento sin guardar|New unsaved experiment
Guardar / generar Excel|Save / create Excel
Guardar las entradas de todos los ensayos en el Excel maestro|Save all assay inputs to the master workbook
Actualizar y exportar resultados|Update and export results
Regenerar todos los archivos|Rebuild all files
Método|Method
Variante|Variant
ENSAYOS DEL EXPERIMENTO|EXPERIMENT ASSAYS
Añadir un ensayo al experimento|Add an assay to the experiment
Duplicar el ensayo seleccionado|Duplicate selected assay
Retirar el ensayo seleccionado|Remove selected assay
Crear una variante manual del protocolo de este ensayo|Create a manual protocol variant for this assay
1   Lecturas experimentales|1   Experimental readings
2   Protocolo y condiciones|2   Protocol and conditions
3   Metodología|3   Methodology
Parámetro del ensayo|Assay parameter
Valor / selección|Value / selection
Ayuda|Help
Origin: valores Excel|Origin: Excel values
Solo Excel|Excel only
Número de filas vacías que añadir|Number of empty rows to add
Añadir el número de filas indicado|Add the selected number of rows
Preparar una muestra y sus réplicas|Prepare a sample and its replicates
Datos sintéticos: elegir una muestra o tres variedades|Synthetic data: choose a demonstration
Guardar protocolo como nueva variante versionada|Save protocol as a new versioned variant
Añadir tipo de lectura|Add a reading type
Abrir el archivo Excel|Open the Excel workbook
Abrir el proyecto Origin|Open the Origin project
Ver gráficas exportadas de Origin|Open exported figures
Mostrar / ocultar registro de actividad|Show / hide activity log
Abrir ayuda: protocolos, variedades y uso|Open help: protocols, varieties and workflow
Obligatorio según el tipo de lectura|Required for this reading type
FRAP · una muestra|FRAP · one sample
FRAP · tres variedades y un calibrado|FRAP · three varieties and one calibration
Experimento con cinco métodos y tres variedades|Five methods and three varieties
Demo extendida: DPPH, pesadas y tamizado|Extended demo: DPPH, weighing and sieving
Listo para calcular|Ready to calculate
Borrador|Draft
Calculado · revisar QC|Calculated · review QC
Revisar resultados|Review results
Resultado inválido|Invalid result
Entradas completas. Guardar y actualizar para calcular.|Complete inputs. Save and update to calculate.
Añadir ensayo al experimento|Add assay to experiment
Protocolo / variante|Protocol / variant
Nombre del ensayo|Assay name
Añadir ensayo|Add assay
Cada ensayo conserva sus datos y calibración. Puedes añadir otro ensayo del mismo método para una variante o lote distinto.|Each assay keeps its own data and calibration. Add another assay of the same method for a different variant or batch.
Retirar ensayo|Remove assay
¿Retirar este ensayo de las entradas actuales? Se conservará el historial al guardar.|Remove this assay from the current inputs? History will be retained when you save.
Nombre visible|Display name
Cambios sin guardar|Unsaved changes
Hay cambios en la tabla o el protocolo. ¿Descartarlos?|There are unsaved table or protocol changes. Discard them?
Preparar muestra|Prepare sample
Nombre único de muestra o variedad (resultados separados):|Unique sample or variety name (separate results):
Réplicas biológicas|Biological replicates
Número de unidades biológicas independientes:|Number of independent biological units:
Réplicas técnicas|Technical replicates
Lecturas por cada unidad biológica:|Readings per biological unit:
Carpeta que contendrá el experimento|Folder that will contain the experiment
Nombre de carpeta nueva|New folder name
Seleccionar carpeta del experimento|Select experiment folder
Guardar o abrir un experimento primero|Save or open an experiment first
Hay cambios en la ventana. Guarda primero para aplicarlos; Actualizar utiliza el Excel guardado.|There are unsaved changes. Save first; Update uses the saved workbook.
Operación no completada|Operation could not be completed
El experimento debe conservar al menos un ensayo|The experiment must contain at least one assay
Nombre de carpeta inválido|Invalid folder name
Nueva variante del protocolo|New protocol variant
Guardar variante|Save variant
Nombre de la nueva variante|New variant name
Quercetina (QE)|Quercetin (QE)
Rutina (RE) · variante manual|Rutin (RE) · manual variant
Antes de reacción|Before reaction
En la mezcla final|In final mixture
Incremento: final − inicial|Change: final − initial
Lectura final (endpoint)|Final reading (endpoint)
Inhibición en cada tiempo (DPPH)|Inhibition at each time (DPPH)
Masa inicial ensayada|Initial tested mass
Base seca: aplicar fracción seca|Dry basis: apply dry fraction
No: faltan condiciones|No: conditions missing
Sí: condiciones documentadas|Yes: documented conditions
Blanco de reactivos|Reagent blank
Patrón de calibración|Calibration standard
Control de calidad|Quality control
Muestra|Sample
Control radical sin antioxidante|Radical control without antioxidant
Elegir tipo…|Choose type…
Sí|Yes
No|No
Comportamiento analítico|Analytical behaviour
Se calculará como:|Calculate as:
Nombre visible (ej.: Control fortificado)|Display name (e.g. Spiked control)
Plantillas de datos|Data templates
Guardar plantilla de datos|Save data template
Cargar plantilla de datos|Load data template
Nombre de la plantilla|Template name
Conservar también lecturas experimentales|Also retain experimental readings
Por defecto se guardan muestras, réplicas, dosis, tiempos y concentraciones; se vacían las mediciones y la confirmación de meseta.|By default, samples, replicates, doses, times and concentrations are retained; measurements and plateau confirmations are cleared.
Guardar plantilla|Save template
No hay plantillas compatibles con este método.|No compatible templates for this method.
Aplicar plantilla|Apply template
Sustituir las filas del ensayo|Replace assay rows
Añadir al final|Append rows
La plantilla contiene lecturas. Revísalas antes de reutilizarlas; no representan un experimento nuevo.|This template contains readings. Review them before reuse; they do not represent a new experiment.
Estructura sin mediciones|Structure without measurements
Incluye mediciones|Includes measurements
Personalizar gráficas|Customise figures
Selecciona una plantilla visual. Se aplicará a las gráficas gestionadas de Origin y Publication al actualizar; no cambia los cálculos.|Choose a visual preset. It will be applied to managed Origin and Publication figures on update; calculations are unchanged.
Aplicar estilo|Apply style
Español|Español
English|English
Cambiar a modo oscuro|Switch to dark mode
Cambiar a modo claro|Switch to light mode
Idioma de la interfaz|Interface language
La personalización se guardará con el experimento. Actualiza para regenerar las figuras.|The style will be saved with the experiment. Update to regenerate figures.
Preparando actualización|Preparing update
Actualización finalizada|Update complete
Error de actualización; abre el registro|Update failed; open the log
Actualización activa|Update in progress
Espera a que termine la actualización antes de cerrar.|Wait for the update to finish before closing.
Borradores guardados · completar los datos antes de calcular|Drafts saved · complete inputs before calculating
Actualización parcial · consulta el registro y el informe de Origin|Partial update · check the log and Origin report
Todos los ensayos calculados. Revisar QC.|All assays calculated. Review QC.
Actualización parcial: revisar estados de cada ensayo.|Partial update: review assay states.
Borradores guardados; faltan datos.|Drafts saved; data missing.
Entradas guardadas; cálculo pendiente.|Inputs saved; calculation pending.
No se completó la actualización.|Update was not completed.
Experimento cerrado. Los archivos se conservan.|Experiment closed. Files are retained.
Resultados disponibles en Documents, Figures y Results.|Results are available in Documents, Figures and Results.
Guardadas las entradas de todos los ensayos. Actualizar para calcular y exportar los completos.|All assay inputs saved. Update to calculate and export complete assays.
Demostración sin guardar|Unsaved demonstration
Experimento multimétodo · SINTÉTICO|Multi-method experiment · SYNTHETIC
Datos sintéticos FRAP cargados; no son resultados experimentales.|Synthetic FRAP data loaded; these are not experimental results.
Calculando con Excel y actualizando Origin… Guardar y cerrar los libros en Excel antes de continuar.|Calculating with Excel and updating Origin… Save and close Excel workbooks first.
Verificando ensayos y trazabilidad|Checking assays and traceability
Preparando el Excel maestro y calculando los ensayos completos|Preparing the master workbook and calculating complete assays
Comprobando resultados y separando exportaciones por ensayo|Checking results and organising exports by assay
Actualizando el proyecto Origin por carpetas de ensayo|Updating Origin project folders by assay
Exportando figuras científicas por metodología|Exporting scientific figures by method
Archivando el experimento y sus revisiones|Archiving experiment and revisions
Sin cambios: Excel, Origin y exportaciones verificados|No changes: Excel, Origin and exports verified
Qué se calcula|Calculation
Condiciones y reactivos|Conditions and reagents
Estado|Status
Fuente|Source
Ayuda de PhDexLab|PhDexLab help
Aceptar|OK
Cancelar|Cancel
Guardar|Save
Descartar|Discard
Cerrar|Close
Humedad|Moisture
Materia seca|Dry matter
Cenizas|Ash
Granulometría|Particle size distribution'''
for line in PAIRS.splitlines():
    source,target=line.split('|',1);add(source,target)

MORE='''Esperado del control|Expected control
No se utiliza en esta categoría/protocolo.|Not used for this category/protocol.
Sin lecturas|No readings
Método no implementado|Method not implemented
Motor de cálculo desconocido|Unknown calculation engine
Nombre y fuente del protocolo obligatorios|Protocol name and source are required
Completar norma, temperatura y criterio final para esta adaptación|Complete the standard reference, temperature and endpoint criterion for this adaptation
Registrar duración de incineración|Record ashing duration
ABTS usa absorbancia final y calcula la inhibición frente al control radical|ABTS uses final absorbance and calculates inhibition against the radical control
Completar agua adicional (0 si no se añade)|Enter additional water (0 if none)
Alícuota + reactivos + agua no coincide con el volumen final documentado|Aliquot + reagents + water does not match the documented final volume
Base de concentración inválida|Invalid concentration basis
Patrón, unidades o factor de expresión incompatibles|Incompatible reference, units or expression factor
Criterios QC inválidos|Invalid QC criteria
Magnitud gravimétrica no soportada|Unsupported gravimetric quantity
El control radical corregido debe ser positivo|Corrected radical control must be positive
Falta blanco o control radical sin antioxidante|Missing reagent blank or radical control without antioxidant
Se necesitan tres niveles distintos de calibración|At least three distinct calibration levels are required
Cada concentración debe tener un único nivel de patrón|Each concentration must have a unique standard-level identifier
Identificador de lectura duplicado|Duplicate reading identifier
DPPH EC50 utiliza control radical y muestras, no calibración Trolox|DPPH EC50 uses radical controls and samples, not Trolox calibration
En pesadas y tamizado todas las filas son muestras|All weighing and sieving rows must be samples
Dosis positiva y tiempo no negativo obligatorios|Positive dose and non-negative time are required
Revisar taras y masas: m0≤m2≤m1, m1>m0|Check tare and masses: m0≤m2≤m1, m1>m0
Fracción seca requerida: 0<f≤1|Dry fraction required: 0<f≤1
Intervalos o masas de tamizado inválidos|Invalid sieving intervals or masses
Lectura duplicada dentro de la misma unidad|Duplicate reading within the same unit
Falta control radical al tiempo de una lectura DPPH|Missing radical control at a DPPH reading time
Marcar una sola meseta por dosis y réplica técnica|Confirm one plateau per dose and technical replicate
Cada unidad necesita mesetas confirmadas en al menos dos dosis para EC50|Each unit needs confirmed plateaus at two or more doses for EC50
Hay series cinéticas sin meseta confirmada|Some kinetic series lack a confirmed plateau
La masa cargada debe coincidir en todas las fracciones de una unidad|Loaded mass must match across all fractions of one unit
Una masa por fracción y unidad; otro tamizado utiliza otra unidad biológica|One mass per fraction and unit; an independent sieving run needs another biological unit
Intervalos granulométricos solapados|Overlapping particle-size intervals
Máximo 10000 lecturas por ensayo|Maximum 10000 readings per assay
Máximo: 10000 lecturas|Maximum: 10000 readings
Máximo: 10000 filas|Maximum: 10000 rows
Respuesta corregida → calibración OLS → concentración equivalente → dilución previa × volumen de extracto / masa. La concentración final de reacción se convierte a alícuota una sola vez.|Corrected response → OLS calibration → equivalent concentration → previous dilution × extract volume / mass. Final-mixture concentration is converted to aliquot concentration once.
Inhibición (%) = 100 × (A_control radical − A_muestra corregida) / A_control radical. Calibrar con Trolox. No restar de nuevo el control como blanco.|Inhibition (%) = 100 × (radical control A − corrected sample A) / radical control A. Calibrate with Trolox. Do not subtract the control again as a blank.
Mesetas confirmadas por el operador → media técnica por dosis y unidad → interpolación local alrededor de 50% → media y DE biológica de EC50. Sin extrapolación ni meseta automática.|Operator-confirmed plateaus → technical mean by dose and unit → local interpolation around 50% → biological mean and SD of EC50. No extrapolation or automatic plateau detection.
Humedad = 100(m1−m2)/(m1−m0). Materia seca = 100(m2−m0)/(m1−m0). Cenizas = 100(m2−m0)/masa neta inicial; la base seca exige la fracción seca correspondiente.|Moisture = 100(m1−m2)/(m1−m0). Dry matter = 100(m2−m0)/(m1−m0). Ash = 100(m2−m0)/initial net mass; a dry basis requires the corresponding dry fraction.
Retenido (%) = 100 × masa de fracción / masa cargada. Recuperación = 100 × suma de fracciones / masa cargada. No se normaliza al 100%.|Retained (%) = 100 × fraction mass / loaded mass. Recovery = 100 × sum of fractions / loaded mass. No renormalisation to 100%.'''
for line in MORE.splitlines():
    source,target=line.split('|',1);add(source,target)

FRAGMENTS={' lecturas':' readings',' blancos':' blanks',' patrones':' standards',' controles':' controls',' muestras distintas':' distinct samples',
 'Una fila = una lectura':'One row = one reading',' · etapa ':' · stage ',' · en este ensayo':' · in this assay',' importando ':' importing ',
 ' gráfica ':' figure ',' filas':' rows',' · copia':' · copy','Nombre para una variante manual de ':'Name for a manual variant of ',
 'Consulta la ayuda general para el flujo de trabajo y las unidades. Las condiciones editadas se conservan por ensayo y versión.':'See Help for workflow and units. Edited conditions are retained per assay and version.',
 'Revisar parámetro numérico: ':'Check numeric parameter: ','Completar parámetro positivo: ':'Enter positive parameter: '}
add('La información del protocolo se conserva en el idioma de la fuente.','Protocol information is retained in the source language.')

def t(text):
    text=str(text)
    if LANGUAGE=='es':return text
    if text in CATALOG:return CATALOG[text]
    # HTML labels and dynamic status/progress strings; only known UI fragments translate.
    pieces=re.split('(<[^>]+>)',text)
    for i,piece in enumerate(pieces):
        if piece.startswith('<'):continue
        if piece in CATALOG:pieces[i]=CATALOG[piece];continue
        for source,target in FRAGMENTS.items():piece=piece.replace(source,target)
        for source in sorted(CATALOG,key=len,reverse=True):
            if len(source)>14:piece=piece.replace(source,CATALOG[source])
        pieces[i]=piece
    return ''.join(pieces)

def localize(root):
    """Translate widget chrome, never table values, user labels or stored protocol content."""
    from PySide6.QtWidgets import QWidget,QLabel,QAbstractButton,QComboBox,QTabWidget,QTableWidget,QLineEdit,QProgressBar,QMessageBox
    def prop(obj,key,getter,setter):
        current=getter();cache=getattr(obj,'_translations',{});source,last=cache.get(key,(current,None))
        if current!=last:source=current
        result=t(source);cache[key]=(source,result);obj._translations=cache
        if result!=current:setter(result)
    for widget in [root]+root.findChildren(QWidget):
        prop(widget,'tooltip',widget.toolTip,widget.setToolTip)
        prop(widget,'title',widget.windowTitle,widget.setWindowTitle)
        if isinstance(widget,(QLabel,QAbstractButton)) and not widget.property('userData'):
            prop(widget,'text',widget.text,widget.setText)
        if isinstance(widget,QMessageBox):
            prop(widget,'text',widget.text,widget.setText);prop(widget,'informative',widget.informativeText,widget.setInformativeText)
        if isinstance(widget,QLineEdit):prop(widget,'placeholder',widget.placeholderText,widget.setPlaceholderText)
        if isinstance(widget,QProgressBar):prop(widget,'format',widget.format,widget.setFormat)
        if isinstance(widget,QComboBox):
            widget.blockSignals(True)
            for i in range(widget.count()):prop(widget,'item'+str(i),lambda i=i:widget.itemText(i),lambda v,i=i:widget.setItemText(i,v))
            widget.blockSignals(False)
        if isinstance(widget,QTabWidget):
            for i in range(widget.count()):prop(widget,'tab'+str(i),lambda i=i:widget.tabText(i),lambda v,i=i:widget.setTabText(i,v))
        if isinstance(widget,QTableWidget):
            for i in range(widget.columnCount()):
                item=widget.horizontalHeaderItem(i)
                if item:prop(item,'header',item.text,item.setText)
    for action in root.actions():prop(action,'text',action.text,action.setText)

from PySide6.QtWidgets import QPlainTextEdit
class ActivityLog(QPlainTextEdit):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.source_lines=[]
    def appendPlainText(self,text):self.source_lines.append(str(text));super().appendPlainText(t(text))
    def retranslate(self):self.setPlainText('\n'.join(t(text) for text in self.source_lines))

for pair in """Experimento guardado|Experiment saved
¿Quieres calcular y exportar los resultados ahora o seguir editando?|Would you like to calculate and export results now or continue editing?
Actualizar y exportar ahora|Update and export now
Seguir editando|Continue editing""".splitlines():add(*pair.split("|",1))
