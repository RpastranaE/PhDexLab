# Historial de cambios

Para instalar y utilizar PhDexLab, consulta el [manual vigente](docs/MANUAL.md). Esta página explica la evolución; las instrucciones actuales no están repartidas entre versiones.

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
