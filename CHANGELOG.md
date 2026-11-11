# Historial de cambios

Para instalar y utilizar PhDexLab, consulta el [manual vigente](docs/MANUAL.md). Esta página explica la evolución; las instrucciones actuales no están repartidas entre versiones.

## 0.12.2

- Importación: reconoce Patrón, Blanco, Muestra y Control, además de sus nombres completos e ingleses, independientemente del idioma de la app.
- Detecta encabezados con unidades del protocolo, µ/μ/u y ×/x. Origen de la lectura no se asigna automáticamente al modo individual/media, evitando confundir el equipo con el tipo de dato.
- Avisos breves con fila de datos, campo, valor y corrección para tipos desconocidos, números/separadores, comillas, codificación y filas desiguales. No se importan parcialmente archivos con errores.
- La asignación y la vista previa muestran solo los campos aplicables al protocolo: inicial solo en parejas, corrección de muestra solo si está activada y fracción seca solo cuando procede.
- Arrastre también desde las celdas de origen y sobre las listas de destino; indicación más clara. Se conserva la asignación manual por listas.

## 0.12.1

- Entrada de datos tiene su propio espacio a la derecha de las pestañas y abre el menú completo con un clic en cualquier parte. Importar archivo ya no depende de una flecha pequeña junto a las pestañas.
- Ayuda actualizada con las instrucciones de importación y del recorrido de cálculo.

## 0.12.0

- Excel con recorrido de cálculo enlazado, pasos numerados y lecturas identificadas por muestra/unidad/repetición. Referencias locales cuando los datos están en la misma hoja; comentarios de fórmula y resultados destacados.
- Sin paneles fijados. Overview se restaura antes de guardar el recálculo. Los PDF de resumen exportan solo su sección.
- Entrada de datos sustituye al nombre anterior del botón. Nueva importación de textos delimitados: CSV/TXT/TSV/DAT/ASC, separadores, decimal, miles, comillas, codificación, cabeceras y líneas iniciales.
- Asignación interactiva arrastrando encabezados o mediante listas, búsqueda de campos y vista previa del resultado. Se conservan nombres e IDs con ceros iniciales; los números incompatibles se rechazan. Se añaden lecturas sin reemplazar las existentes; se conservan los datos pendientes como borrador.
- Procedencia del archivo, huella y opciones de importación registradas al guardar.
- Origin conserva vista de página completa al reabrir sin cambiar dimensiones de las figuras. Ayuda y manual actualizados.

## 0.11.1

- Estilos Excel ampliados: seis paletas, colores de texto y fondos, bordes horizontales o completos, alineación, tamaños independientes de encabezados/secciones/título, altura de encabezados, anchura de columnas y cuadrícula.
- Editor con pestañas Colores y Distribución y vista previa. Se conservan los estilos personales anteriores; no se redondean valores ni cambian cálculos.
- Superíndices SVG normalizados a texto vectorial editable con tamaño y desplazamiento explícitos. Evita el fallo de fuente que mostraba −1 como !. Se conservan las curvas, símbolos, signos negativos y anotaciones.
- La próxima actualización/exportación regenera las figuras de Origin con la corrección.

## 0.11.0

- Creación de repeticiones con campos comunes y numeración preparada, sin copiar absorbancias. Numeración automática de filas existentes por muestra y unidad.
- Arrastrar el tirador de selección para completar series numéricas o nombres como P0/P1 y E01. Rellenar abajo/derecha con Ctrl+D/R, pegado de un valor en un rango, sugerencias de nombres y deshacer/rehacer con Ctrl+Z/Y.
- Excel compacto: Overview y dos pestañas por ensayo, Data y Analysis. Cálculos, calibraciones y resultados se agrupan por secciones con enlaces. No se duplican fórmulas ni se mantienen hojas de cálculo ocultas.
- Lectura de libros anteriores y migración al guardar/actualizar, conservando historial. Bloques con rangos definidos; conector Excel de Origin actualizado y comprobado con importaciones parciales.
- Estilos de Excel independientes de Origin: cuatro paletas, colores editables, tipografía, densidad, filas alternas, vista previa y estilos personales reutilizables.
- Actualización de ayuda y novedades. El formato agrupado requiere 0.11.0 o posterior.

## 0.10.1

- Resumen visual de lecturas con contadores separados y estado verde Listo para calcular, adaptado a ambos idiomas y temas.
- Ventana de novedades local que aparece una sola vez al abrir una versión posterior; la primera instalación mantiene la ayuda inicial.

- Biblioteca accesible desde el icono de cuadrícula, incluso sin experimento abierto, para buscar y eliminar plantillas de datos y variantes personales con confirmación.
- Los protocolos incluidos pueden ocultarse del catálogo y restaurarse desde el gestor. Las copias utilizadas en experimentos y las condiciones editadas del ensayo actual se conservan.
- La biblioteca de variantes respeta el mismo directorio de datos de usuario que las plantillas y preferencias.
- Acceso directo a la carpeta de figuras desde Resultados finales.
- Terminología genérica: Unidad experimental / extracción, n independiente y DE entre unidades, sin cambiar bio_id, la agrupación ni los cálculos guardados.
- Resultados presenta media ± DE: dos cifras significativas para la desviación y media redondeada a la misma posición decimal. Excel y las ayudas emergentes conservan los valores completos; no se inventa una DE cuando no es estimable.
- Fuente del protocolo opcional para guardar y calcular; las referencias existentes se conservan.
- Limpieza del defecto de sobrelínea en los títulos de exportaciones de Origin. Se conserva el SVG original en trazabilidad y se generan PNG/PDF desde sus vectores corregidos; datos, ajustes, ejes y barras de error se mantienen.
- Ayuda ampliada sobre patrón cero y blanco de reactivos: el ejemplo Zen-Bio representa tres observaciones en dos roles; el blanco se resta una sola vez y no son réplicas independientes adicionales.

## 0.10.0

- Actualizar y exportar guarda primero las entradas y condiciones actuales en el Excel maestro, incluida la celda en edición. Se conserva la protección contra cambios externos del libro.
- Validación previa con aviso por ensayo, fila y campo; los campos obligatorios mantienen su asterisco inicial y solo se resaltan en rojo tras intentar actualizar. Se conserva el borrador. El cálculo parcial requiere una elección explícita.
- Pestaña Resultados finales con valores exactos guardados, unidades, DE/n biológico, calibración y detalle por unidad.
- Previsualizaciones ampliables de exportaciones reales de Origin, incluidas curvas de dosis. Se comprueba su procedencia e integridad y se ocultan resultados obsoletos.
- Ayuda y manual vigente actualizados para el flujo de guardado, validación y consulta de resultados.

## 0.9.3

[Versión y descargas](https://github.com/RpastranaE/PhDexLab/releases/tag/v0.9.3)

- Auditoría dimensional y metodológica de las 15 variantes, con fuentes, adaptaciones y límites explicados en la documentación vigente.
- Excel desglosa la normalización por concentración, dilución, volumen total en litros, masa en gramos y factor de expresión. Cada resultado indica su unidad; recuperación de controles y capacidad por masa se distinguen expresamente.
- Se impide que un control ignore silenciosamente masa, volumen y dilución y devuelva un porcentaje. Las muestras individuales permiten varias diluciones de una misma extracción, corregidas antes de promediar, sin aumentar el n biológico.
- Base TFC corregida a extracto seco según su fuente operativa. Se explicitan la adaptación másica de EC50 DPPH y las bases de concentración de CUPRAC.
- Se impide etiquetar porcentajes gravimétricos/tamizado o EC50 con unidades incompatibles. Pesadas, fracciones y control radical DPPH tienen pasos y encabezados específicos en Excel.
- Catálogo versión 4; los protocolos archivados conservan su información y requieren revisión explícita para cambiar de base.

## 0.9.2

[Versión y descargas](https://github.com/RpastranaE/PhDexLab/releases/tag/v0.9.2)

- Entrada guiada visible con pipeta: varias lecturas o una media, sin duplicarlas ni crear réplicas ficticias.
- n técnico y DE opcionales para medias, conservados en RAW y transformados en Excel cuando corresponde. La precisión desconocida no se inventa.
- Selección explícita de absorbancia única, parejas inicial/final o ΔA ya medido; columnas y ayudas adaptadas al método.
- Corrección de muestra opcional y explicada con un ejemplo; tratamiento explícito de lecturas ya puestas a cero, conservando controles radicales.
- Número de lecturas y valores de entrada por defecto personalizables, mínimo de niveles de calibración configurable y concentración de control indicada una sola vez.
- Revisión de las 15 variantes: TPC adaptado corregido a 760 nm en el catálogo nuevo; se conservan condiciones y limitaciones documentadas. Catálogo versión 3.
- Activación explícita de opciones en experimentos anteriores y compatibilidad de plantillas antiguas. Ayuda y manual actualizados con capturas de ambos modos.

## 0.9.1

[Versión y descargas](https://github.com/RpastranaE/PhDexLab/releases/tag/v0.9.1)

- Borrado de contenido y menú contextual de filas: insertar, eliminar, copiar y pegar; atajos Ctrl+C/X/V y Supr.
- Búsqueda de actualizaciones en segundo plano al iniciar; elección de instalar ahora o al salir y reinicio tras instalar.
- Capturas de ayuda a doble resolución, visor con zoom y sección de créditos/licencias con contacto.
- Elección de calcular/exportar o seguir editando tras guardar un experimento nuevo.
- Opción Sin símbolos independiente para resultados, calibración y curvas de dosis, conservando líneas y errores.
- Escritura del Excel optimizada evitando recorrer repetidamente las celdas ya escritas. Se conservan valores y fórmulas.

## Reorganización de documentación

Se unifican las instrucciones de uso en un manual estable y las de modificación en una guía de desarrollo. Las guías antiguas quedan archivadas e identificadas como históricas. Esta reorganización no cambia el ejecutable ni requiere actualizar la aplicación.

## 0.9.0

[Versión y descargas](https://github.com/RpastranaE/PhDexLab/releases/tag/v0.9.0)

- Inicio y cierre de experimento sin ensayo preseleccionado.
- Ayuda en el primer uso y 24 capturas de la aplicación, repartidas entre español e inglés.
- Edición de celdas con selección por clic, escritura directa y F2/doble clic para editar.
- Iconos diferentes para duplicar ensayo y guardar variante.
- Comprobación de Excel abierto o abriéndose, incluido el bloqueo antes de sustituir el libro calculado.
- Ventana de actualizaciones simplificada; el progreso de descarga queda en esa ventana.

## 0.8.0

[Versión y descargas](https://github.com/RpastranaE/PhDexLab/releases/tag/v0.8.0)

- Instalador único para Windows con accesos directos y desinstalador.
- Corrección del archivo de política TLS ausente en el ejecutable de 0.7.0, manteniendo la verificación de certificados.
- Alternativa de consulta de metadatos públicos cuando GitHub limita su API.
- Previsualización de resultados, calibración y dosis; traducciones y referencias originales de protocolos.
- Correcciones en vaciado de lecturas, carpeta Figures, guardado de variantes y ayudas de botones.

## 0.7.0

[Versión y descargas](https://github.com/RpastranaE/PhDexLab/releases/tag/v0.7.0)

Primera publicación pública de la aplicación autónoma: experimentos con varios ensayos, Excel/Origin, plantillas de datos, personalización de figuras, interfaz español/inglés y modo claro/oscuro. Se distribuía como ZIP portátil.

Su comprobador de actualizaciones podía fallar por un archivo TLS ausente. Si aún utilizas 0.7.0, instala manualmente el instalador de la **versión actual**, disponible en [latest](https://github.com/RpastranaE/PhDexLab/releases/latest); no necesitas instalar 0.8.0 como paso intermedio.

Los textos completos de las guías y notas anteriores están en el [archivo histórico](docs/archive/README.md).
