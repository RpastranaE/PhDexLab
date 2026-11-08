"""Human-facing labels, units, requirements and examples; internal keys stay hidden."""
FIELDS={
 'record_id':('Identificador interno','Se genera automáticamente y permanece estable al volver a abrir el experimento.'),
 'kind':('Tipo de lectura','Elegir una categoría: blanco de reactivos, patrón de calibración, control de calidad o muestra. Los tipos personalizados se vinculan a una de estas categorías para definir su cálculo.'),
 'sample_id':('Muestra / patrón','Nombre que reconocerás en resultados y gráficas. Obligatorio. Ej.: EXP-024, Patrón 100, Control 500. Usa el mismo nombre en las repeticiones de una muestra o de un nivel de calibración.'),
 'bio_id':('Unidad biológica\no extracción','Identifica una preparación independiente. Obligatorio. Ej.: Extracción 1, Extracción 2. Las lecturas con el mismo nombre y unidad se consideran repeticiones técnicas. Para patrones/blancos puedes usar Lote 1. El programa no determina si una réplica es realmente independiente.'),
 'tech_id':('Repetición\nde lectura','Número o nombre de la lectura técnica dentro de cada unidad. Obligatorio y único dentro de esa unidad. Ej.: 1, 2, 3. No incrementa el número de réplicas biológicas.'),
 'concentration':('Concentración\ndel patrón','Obligatoria para patrones y controles; no se usa para muestras/blancos. Número ≥0. Las unidades y si la concentración es antes o después de mezclar se indican en el protocolo. Ej. Fe(II): 100 µmol/L antes de reacción. No introducir aquí la absorbancia.'),
 'A_end':('Absorbancia\nfinal · AU','Lectura original al final de la incubación. Obligatoria; número finito. Unidad de absorbancia, AU, adimensional. Ej.: 0,430. Se aceptan punto o coma decimal. Los valores negativos se conservan para su revisión, no se convierten en cero.'),
 'A_initial':('Absorbancia\ninicial · AU','Lectura original previa a la reacción. Obligatoria en el protocolo de incremento (Fe(II)); no se utiliza en el protocolo endpoint de Trolox. Ej.: 0,020. La respuesta delta se calcula como final − inicial.'),
 'matrix_blank_delta':('Corrección neta\nde matriz · AU','Número finito obligatorio. Es la corrección ADICIONAL por absorbancia propia de la matriz, ya corregida por su propio blanco/lectura inicial. Introducir 0 explícito si no se aplica. NO volver a introducir el blanco de reactivos: el programa ya lo resta una vez. La idoneidad de esta corrección debe validarse.'),
 'dilution':('Factor de dilución\nprevia · ×','Obligatorio para muestras. Número positivo: 1 = extracto sin diluir; 2 = una parte de extracto llevada a dos partes de volumen total (p. ej., 1 mL + 1 mL de disolvente); 10 = una parte llevada a diez. No es el volumen de disolvente ni el porcentaje. Para diluciones sucesivas usa el producto de factores. No incluye la dilución al mezclar con reactivo FRAP.'),
 'extract_mL':('Volumen total\nde extracto · mL','Obligatorio para muestras; número >0. Volumen total de la extracción al que se refiere la masa, NO el volumen pipeteado en la cubeta. Ej.: 10 mL. El programa convierte mL a L una sola vez.'),
 'mass_g':('Masa de\nreferencia · g','Obligatoria para muestras; número >0, en gramos. Ej.: 0,5 g. Debe corresponder a la base de masa del protocolo: hoja seca, extracto seco, etc. No intercambiar bases. La base se documenta en los resultados.'),
 'expected':('Valor esperado\ndel control','Solo obligatorio para controles; número >0. Concentración equivalente esperada, en las unidades y base del eje de calibración. Ej.: 500 µmol/L antes de reacción. Recuperación = concentración interpolada / esperada ×100. No introducir 100 para indicar 100%.'),
 'notes':('Observaciones','Texto libre: lote, disolvente, preparación, incidencias, turbidez o cualquier información útil para la trazabilidad. Opcional; no interviene en las ecuaciones.'),
 'kind_label':('Nombre de tipo interno','Etiqueta del tipo personalizado; su categoría analítica se conserva por separado.'),
}
KIND_LABELS={'blank':'Blanco de reactivos','standard':'Patrón de calibración','control':'Control de calidad','sample':'Muestra'}
PARAMETERS={
 'method':('Método','Ensayo implementado: FRAP. Los demás métodos están pendientes de desarrollo.'),
 'id':('Identificador interno','Identificador de la variante; se conserva internamente.'),
 'name':('Nombre de la variante','Nombre reconocible para elegir este protocolo.'),
 'version':('Versión del protocolo','Entero positivo. Guardar una variante crea una nueva versión inmutable.'),
 'status':('Estado de validación','Los protocolos suministrados son borradores; no constituyen un método validado para tu matriz.'),
 'calibration_basis':('Base de la concentración','Antes de reacción: la concentración del vial pipeteado. Mezcla final: la concentración después de añadir reactivo; el programa recupera la de alícuota con el cociente de volúmenes.'),
 'concentration_unit':('Unidad de concentración','Fe(II): µmol/L. Trolox: mg/L. Debe ser coherente con la variante elegida.'),
 'equivalent':('Patrón de referencia','Fe(II) o Trolox. Sus equivalentes no son intercambiables mediante una simple conversión de unidades.'),
 'response':('Modo de lectura','Incremento: absorbancia final − inicial. Lectura final: usa solo la absorbancia al terminar la incubación.'),
 'wavelength_nm':('Longitud de onda · nm','Número positivo en nanómetros. La fuente FRAP indica 593 nm.'),
 'temperature_C':('Temperatura · °C','Temperatura efectiva en grados Celsius. Dejar vacío si no está fijada numéricamente; en la variante Trolox la fuente indica ambiente. Registrar la temperatura real del ensayo.'),
 'time_min':('Tiempo de incubación · min','Número positivo en minutos. Los tiempos de 4 y 30 min corresponden a variantes distintas y no deben mezclarse.'),
 'aliquot_uL':('Alícuota de muestra / patrón · µL','Volumen de muestra o patrón añadido a la reacción, en microlitros. Número positivo. No es el volumen total de extracto.'),
 'reagent_uL':('Volumen de reactivo · µL','Volumen de reactivo FRAP en cada reacción; número positivo en microlitros.'),
 'water_uL':('Agua adicional · µL','Volumen adicional de agua en la reacción; número ≥0. La suma alícuota + reactivo + agua determina el volumen final.'),
 'report_factor':('Factor de expresión del resultado','1 para µmol/g de Fe(II); 100 para expresar Trolox en mg/100 g. Seleccionar la variante adecuada, no modificar aisladamente las unidades.'),
 'result_unit':('Unidad del resultado','Unidad y equivalente químico del resultado. Se mantiene coherente con el calibrante.'),
 'mass_basis':('Base de masa','Especificar hoja seca, extracto seco, biomasa fresca, etc. Es la masa introducida en la tabla; no convierte entre bases.'),
 'r2_min':('R² mínimo · criterio provisional','Número entre 0 y 1. Umbral de control orientativo y editable; no acredita por sí solo la validez del método.'),
 'cv_max_percent':('CV técnico máximo · %','Número positivo. Límite provisional del coeficiente de variación entre lecturas técnicas de una misma unidad.'),
 'recovery_min_percent':('Recuperación mínima · %','Límite inferior provisional de recuperación de controles. Debe ser menor que el superior.'),
 'recovery_max_percent':('Recuperación máxima · %','Límite superior provisional de recuperación de controles. No implica validación experimental.'),
 'qc_policy':('Interpretación de los controles','Describe el carácter provisional de los criterios de control de calidad.'),
 'reagents':('Preparación de reactivos','Concentraciones, composición y procedencia de la receta. Texto editable y trazable; no sustituye el protocolo experimental.'),
 'notes':('Notas del protocolo','Condiciones particulares, oscuridad, disolvente y observaciones.'),
 'source':('Fuente del protocolo','Enlace a la metodología consultada. Se conserva en cada experimento.'),
 'source_updated':('Fecha de la fuente','Fecha documentada de actualización de la fuente, no fecha de validación.'),
 'standard_range':('Intervalo de calibración de la fuente','Intervalo descrito en la fuente. El rango de interpolación efectivo se obtiene de los patrones introducidos; no se generan concentraciones automáticamente.'),
}
ENUMS={
 'response':[('delta','Incremento: final − inicial'),('endpoint','Lectura final (endpoint)')],
 'calibration_basis':[('before','Antes de reacción'),('final','En la mezcla final')],
}
def axis_labels(p):
    concentration='µmol L⁻¹' if p['concentration_unit']=='umol/L' else 'mg L⁻¹'
    basis='before reaction' if p['calibration_basis']=='before' else 'final reaction mixture'
    x=f"{p['equivalent']} concentration ({concentration}; {basis})"
    wavelength=f"{p['wavelength_nm']:g}".translate(str.maketrans('0123456789.','₀₁₂₃₄₅₆₇₈₉.'))
    y=f'Blank-corrected ΔA{wavelength} (AU)' if p['response']=='delta' else f'Blank-corrected A{wavelength} (AU)'
    result='FRAP (µmol Fe(II) eq g⁻¹)' if p['equivalent']=='Fe(II)' else 'FRAP (mg TE 100 g⁻¹)'
    return x,y,result


FIELDS.update({
 'tare_g':('Tara del recipiente · g','Masa del recipiente vacío, m0, en gramos. Obligatoria y ≥0. No introducir la masa neta de muestra.'),
 'initial_g':('Recipiente + muestra\ninicial · g','Masa total inicial m1, en gramos. Debe superar la tara. La masa neta inicial es m1−m0.'),
 'final_g':('Recipiente + residuo\nfinal · g','Masa total final m2 tras secado o incineración. m0≤m2≤m1. Registrar el criterio de punto final y las condiciones reales.'),
 'dry_fraction':('Fracción seca · 0–1','Solo para cenizas expresadas en base seca si la masa inicial no es ya seca. Ej.: 0,9 para 90% de materia seca. No introducir 90 ni corregir dos veces.'),
 'lower_um':('Límite inferior\nretenido · µm','Abertura inferior del intervalo. Ej.: 100 para la fracción de 100 a 300 µm. Fondo colector: 0. Obligatorio y ≥0.'),
 'upper_um':('Límite superior\npasante · µm','Abertura superior del intervalo, mayor que el límite inferior. Dejar vacío solo para la fracción superior abierta. Usar aberturas reales, no solo mesh.'),
 'retained_g':('Masa retenida\nen fracción · g','Masa neta de esta fracción. Incluir el fondo colector. Una fila por fracción y unidad de tamizado; un nuevo tamizado independiente utiliza otra unidad biológica.'),
 'loaded_g':('Masa cargada\nal tamizado · g','Masa inicial total cargada en esta unidad. Repetir el mismo valor en todas sus fracciones. Los porcentajes se refieren a esta masa, sin renormalizar al 100%.'),
 'dose_mg_mL':('Dosis de extracto\nmg/mL FINAL','DPPH EC50: concentración de extracto seco en la mezcla FINAL, no en la alícuota. En 0,1+3,9 mL, dividir la concentración de alícuota por 40. Cada variedad/unidad necesita una serie de dosis.'),
 'time_min':('Tiempo de lectura\nmin','Tiempo real desde la mezcla, en minutos. Obligatorio en DPPH. Debe existir un control radical al mismo tiempo. Se conservan todas las lecturas cinéticas.'),
 'plateau':('Meseta confirmada','Sí únicamente en la lectura final de cada serie dosis/réplica, tras comprobar meseta. La app no la detecta automáticamente. Las demás lecturas se guardan con No. EC50 usa medias técnicas a cada dosis confirmada.'),
})
PARAMETERS.update({
 'engine':('Cálculo del ensayo','Motor matemático asociado a la metodología. No cambiarlo manualmente por otro ensayo.'),
 'reaction_total_uL':('Volumen final documentado · µL','Si consta, debe coincidir con alícuota + reactivos + agua. CUPRAC: 4100 µL, fijar x y agua. No es volumen de extracto.'),
 'quantity':('Magnitud gravimétrica','Humedad, materia seca o cenizas, según el protocolo. Sus ecuaciones son distintas.'),
 'ash_basis':('Base de expresión de cenizas','Masa inicial: residuo/masa neta ensayada. Base seca: dividir además por la fracción seca correspondiente. No corregir dos veces si la masa inicial ya es seca.'),
 'endpoint_note':('Criterio de punto final / constancia','Documentar los ciclos, criterio de constancia de masa y condiciones reales. No se asigna una tolerancia que no aparece en la fuente.'),
 'blocked_reason':('Información metodológica pendiente','Explica por qué una adaptación documental todavía no debe calcularse como procedimiento completo.'),
 'operational_confirmed':('Condiciones operativas completadas','Para adaptaciones TAPPI incompletas: confirmar solo después de identificar norma y registrar condiciones. No equivale a validación experimental.'),
 'standard_reference':('Norma / referencia operativa confirmada','Identificar código y edición de la norma, o la referencia que completa esta adaptación. Obligatorio para desbloquear los borradores TAPPI.'),
 'sieve_amplitude':('Amplitud y condiciones de tamizado','Registrar amplitud, equipo, carga y preparación. No se inventan los valores ausentes de las fuentes.'),
 'mass_recovery_min':('Recuperación másica mínima · %','Umbral provisional editable para balance de tamizado. No normaliza las fracciones.'),
 'mass_recovery_max':('Recuperación másica máxima · %','Umbral provisional editable para balance de tamizado; revisar pérdidas, doble contabilización y pesadas.'),
})
ENUMS.update({'ash_basis':[('initial','Masa inicial ensayada'),('dry','Base seca: aplicar fracción seca')],
 'operational_confirmed':[(False,'No: faltan condiciones'),(True,'Sí: condiciones documentadas')]})
PARAMETERS['method']=('Método','Familia analítica del ensayo seleccionado. Cada ensayo conserva su protocolo, datos y cálculo independiente.')
PARAMETERS['reagent_uL']=('Reactivos y disolventes · µL','Volumen total añadido distinto de alícuota y agua. La receta desglosada se documenta en Preparación de reactivos.')
PARAMETERS['concentration_unit']=('Unidad de concentración','Unidad de los patrones de ESTA variante. Mantener coherentes patrón, curva y unidad de resultado; no mezclar mg/L y µmol/L.')

ENUMS['response'].append(('inhibition','Inhibición en cada tiempo (DPPH)'))
PARAMETERS['time_min']=('Tiempo de reacción / lectura · min','Tiempo de la variante. Para DPPH se registran los tiempos reales por fila y se confirma la meseta; no se impone un tiempo fijo. En secado a masa constante puede quedar vacío si el punto final se documenta por criterio.')
PARAMETERS['source_retrieved']=('Fecha de consulta de la fuente','Día en que se consultó Notion o la referencia publicada para preparar este catálogo. No equivale a la fecha de edición de la fuente ni a la validación del método.')
