# PhDexLab 0.7

Proyecto personal de RpastranaE, desarrollado con asistencia de IA. Aplicación autónoma para Windows; todavía no modifica ni se integra directamente en PhDex.

## Instalar y abrir

Descarga `PhDexLab-Windows-x64.zip` desde las [releases oficiales](https://github.com/RpastranaE/PhDexLab/releases). Descomprime en una carpeta con permiso de escritura; abre `Application/PhDexLab.exe`. Conserva la carpeta `_internal` junto al ejecutable. No lo ejecutes dentro del ZIP. No requiere instalar Python.

Requisitos de cálculo: Windows de 64 bits, Microsoft Excel de escritorio y OriginPro 2024 instalados y con licencia. Solo Excel permite calcular sin Origin. El ejecutable incluye bibliotecas Python, no licencias de Excel/Origin. El binario no tiene firma Authenticode.

## Primer experimento

1. Usa la demostración de varios métodos del icono de tubo de ensayo. Todo su contenido es sintético.
2. Selecciona un ensayo en la columna izquierda. Añade otro con el matraz/+.
3. Introduce lecturas y condiciones. Distintos nombres de muestra producen resultados separados con la calibración del mismo ensayo. Réplicas técnicas y unidades biológicas tienen campos separados.
4. Guarda: un Excel, con pestañas por ensayo. Los borradores se conservan.
5. Cierra los documentos de Excel y Origin y pulsa Actualizar y exportar: calcula los ensayos completos y genera un único proyecto de Origin, organizado por ensayo.

`Documents` contiene los documentos principales, con el nombre del experimento. `Figures/<ensayo>/Origin` y `Figures/<ensayo>/Publication` contienen exportaciones. `Results` contiene tablas; `_internal` conserva trazabilidad e historial. Conserva toda la carpeta del experimento.

Después de cambiar Excel manualmente, usa el refresco explícito de la app. No se afirma sincronización automática de Excel/Origin. La conexión y los formatos dependen de la instalación local; la exportación Publication aporta una alternativa de figuras vectoriales.

## Editor de estilos

El icono de paleta abre diez bases y cuatro pestañas:

- **Resultados:** paleta, un color por muestra opcional, color uniforme de barras, símbolo, relleno abierto/sólido, tamaño y color de error.
- **Calibración:** dos colores separados para patrones y ajuste OLS; símbolo, error, tamaño, tipo y grosor de línea.
- **Curvas de dosis:** paleta, símbolo, error y líneas. Las unidades biológicas se representan por separado.
- **Tipografía:** familia y tamaños de ejes, entre 7 y 14 pt.

Pulsa cada muestra de color para editarla. Las paletas de resultados/dosis admiten 2–12 colores; si hay más series, los colores se repiten. La vista previa es ilustrativa. Los datos del experimento siguen siendo la fuente de las figuras exportadas, siempre en inglés científico.

Guardar como estilo crea una plantilla personal. Importar/exportar intercambia JSON de apariencia sin datos experimentales. La configuración completa queda también en el experimento; no depende de que otra persona tenga tu plantilla personal.

Aplicar y actualizar regenera el formato de las gráficas gestionadas. Conserva una copia si has editado manualmente el proyecto Origin. Las ediciones de los estilos nunca cambian las fórmulas ni resultados analíticos. Los proyectos anteriores conservan el significado de sus cinco estilos originales.

## Actualizaciones

El icono de descarga superior muestra la versión instalada y permite buscar actualizaciones y activar/desactivar la opción automática. Por defecto está activa en el ejecutable portátil.

- Consulta la última release **estable** de `RpastranaE/PhDexLab`, al iniciar y cada seis horas mientras la app permanezca abierta.
- Descarga en segundo plano y muestra avance integrado. Un fallo de red no impide el trabajo local.
- Exige el SHA-256 publicado por GitHub y verifica además el inventario y cada archivo del ZIP. Rechaza archivos fuera de `Application`, rutas peligrosas y versiones preliminares.
- La actualización queda preparada. Se instala al cerrar normalmente, después de terminar el trabajo de Excel/Origin y resolver los cambios sin guardar.
- Sustituye únicamente `Application`. Experimentos, plantillas, variantes y preferencias quedan fuera de esa sustitución. Requiere una ubicación con permiso de escritura.
- Antes de reabrir, prueba el arranque del nuevo ejecutable. Si falla, intenta restaurar la versión anterior. El resultado se registra en `Documents/PhDexLab/updates/last-install.json`.

La comprobación de hashes verifica integridad; no es firma de código. No se envían lecturas, protocolos privados ni resultados a GitHub. Una actualización no recalcula ni migra tus experimentos hasta que tú los abras y actualices. El modo fuente permite consultar versiones pero se actualiza mediante Git o descarga de código, no sustituyendo su entorno Python.

## Métodos y validación

Incluye FRAP, ABTS, CUPRAC, TPC, TFC, DPPH cinético/EC50, humedad, materia seca, cenizas y granulometría, con variantes. Los parámetros son bases documentales o personales pendientes de validar en la matriz; las variantes incompletas permanecen en borrador. Las fuentes privadas no se publican. TFC identifica la base bibliográfica y su patrón de quercetina. No intercambiar equivalentes de rutina/quercetina cambiando solo una etiqueta.

Excel es la fuente única de cálculo: las figuras leen sus valores recalculados. No hay exclusión automática ni pruebas de significación. Las réplicas técnicas se promedian antes de estimar media, DE y n biológicos. Revisa blancos, rango, pendientes, controles y unidades; un R² alto no valida el método. Las pruebas informáticas no sustituyen la validación experimental.

El menú de ayuda de la app explica el trabajo por apartados. Para problemas, conserva el experimento y consulta el registro de actividad; elimina datos personales antes de publicar una incidencia.
