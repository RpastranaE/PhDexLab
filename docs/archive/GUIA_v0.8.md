> **Archivo histórico.** Este texto describe una versión concreta y puede contener instrucciones superadas. Para descargar y utilizar la aplicación actual, consulta el [manual vigente](../MANUAL.md). El [historial de cambios](../../CHANGELOG.md) explica la evolución.

# PhDexLab 0.8 — instalación y cambios

Descarga y ejecuta **PhDexLab-Setup-0.8.0.exe**. Instala el programa con todos sus componentes, crea acceso directo y registra un desinstalador. La primera ejecución utiliza inglés; puedes cambiar a Español en el selector. Si ya había una preferencia guardada, se conserva. No necesitas mover archivos junto al ejecutable.

**Si utilizas 0.7.0:** instala esta versión una vez manualmente. El comprobador de 0.7.0 tenía un archivo de certificados ausente; esta versión lo incluye y comprueba la conexión desde el ejecutable. Los experimentos permanecen en sus carpetas. Abre tus experimentos existentes desde la nueva aplicación.

- Los ajustes de estilo muestran resultados, calibración y curvas de dosis, con símbolos, líneas, colores, errores y tipografía. La vista previa es ilustrativa y utiliza datos sintéticos. Actualiza el experimento para regenerar sus figuras.
- Los protocolos de referencia muestran nombres, notas, reactivos y condiciones en el idioma elegido. Los textos personalizados se conservan. Los nombres y el estado de los protocolos incluidos ya no dicen BORRADOR; las condiciones incompletas siguen impidiendo un cálculo inapropiado.
- La columna Source y su icono de enlace abren la publicación original correspondiente; la pestaña Methodology distingue las adaptaciones. Las referencias no equivalen a validar el método para tu matriz.
- Para vaciar una lectura, abre Reading type y vuelve a Choose type. Se vacían todos los valores de esa fila.
- Figures abre la raíz mientras no existan exportaciones. Si hay un solo ensayo y figuras generadas, abre su carpeta. Con varios ensayos abre Figures.
- La única acción Save variant está junto al selector Variant. El otro botón abre Protocol and conditions para editar; guardar conserva una variante versionada.
- Mantén el ratón sobre los botones para ver sus acciones.

El instalador no incluye Microsoft Excel ni OriginPro: el flujo completo requiere esas aplicaciones instaladas y con licencia. La sincronización se realiza mediante Update and export results; no se afirma una sincronización automática al editar Excel.

Consulta también la [guía de uso general](GUIA_v0.7.md), [validación](../VALIDATION.md) y [diseño de actualizaciones](../UPDATES.md).
