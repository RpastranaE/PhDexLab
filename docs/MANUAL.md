# Manual de PhDexLab

[Inicio](../README.md) · [Índice de documentación](README.md) · [Desarrollo](DEVELOPMENT.md) · [Historial](../CHANGELOG.md)

Esta es la guía de uso vigente. Las guías por versión se conservan en [el archivo histórico](archive/README.md). La interfaz permite español e inglés; aquí se indican los nombres de los controles en ambos idiomas cuando resulta útil.

## 1. Qué hace y qué necesitas

PhDexLab reúne datos introducidos manualmente, protocolos, un Excel con cálculos auditables y un proyecto de Origin con gráficos editables. Es una aplicación independiente: no requiere PhDex ni lo modifica.

Un **experimento** es la carpeta completa del trabajo. Contiene uno o varios **ensayos**: por ejemplo FRAP, CUPRAC y TPC de las mismas muestras. Cada ensayo tiene su propio protocolo, datos, calibración y resultados. Un **protocolo** define condiciones y reglas de cálculo; una variante conserva una versión concreta de esas condiciones.

Necesitas Windows de 64 bits. La aplicación instalada incluye Python y sus bibliotecas. Para recalcular el Excel necesitas Microsoft Excel de escritorio; para generar el proyecto y las figuras nativas de Origin necesitas OriginPro 2024 instalado, con licencia y automatización disponible. Tener las bibliotecas instaladas no garantiza que la automatización local funcione: utiliza Diagnóstico y una prueba con datos sintéticos.

El programa no valida por sí mismo un método analítico. Antes de usar resultados científicos revisa las condiciones, unidades, blancos, calibración y controles de calidad. Consulta [las fuentes y limitaciones de los protocolos](PROTOCOL_SOURCES.md).

## 2. Descargar e instalar

1. Abre [la última versión publicada](https://github.com/RpastranaE/PhDexLab/releases/latest).
2. En **Assets**, descarga `PhDexLab-Setup-X.Y.Z.exe` y ejecútalo.
3. Abre el acceso directo de PhDexLab del escritorio o del menú Inicio. La primera apertura muestra la ayuda. El idioma inicial es inglés y se puede cambiar en la aplicación.

El instalador incluye las dependencias y crea una instalación por usuario. No necesitas mantener archivos al lado del instalador. La carpeta instalada contiene `Application`, que sí necesita conservar sus archivos internos. No extraigas solo su ejecutable.

La alternativa `PhDexLab-Windows-x64.zip` es una distribución portátil: extrae **todo** el ZIP. `latest.json` es información del actualizador; `SHA256SUMS.txt` permite comprobar la integridad de las descargas. Los enlaces **Source code** contienen el código, no una instalación lista para usar. El ejecutable no dispone de firma comercial de Windows.

Guarda tus experimentos fuera de `Application`. La actualización reemplaza esa carpeta de programa. Una copia de seguridad debe incluir la carpeta completa del experimento.

## 3. Primera prueba sin datos reales

Abre el menú de datos sintéticos y elige una demostración con varios ensayos o variedades. Guarda en una carpeta nueva, por ejemplo `DEMO_001`. Cierra cualquier Excel o proyecto de Origin de esa prueba y pulsa **Actualizar y exportar / Update and export**.

Elige el modo de Origin que corresponda: conexión con Excel, valores copiados o sin Origin. Al terminar, revisa el estado, el registro, el Excel y las figuras. Esta prueba sirve para comprobar tu instalación, sin interpretar sus números como medidas reales.

![Interfaz de trabajo](interface-v9.png)

## 4. Crear, abrir y cerrar experimentos

La aplicación empieza sin ensayos seleccionados. Pulsa **Nuevo ensayo / New assay**, selecciona el método y el protocolo y asigna un nombre reconocible. Puedes añadir otro ensayo con otro método o repetir un método con otra calibración o lote.

**Duplicar ensayo** copia su diseño para trabajar por separado. **Guardar protocolo como variante** conserva condiciones del método: no equivale a duplicar un ensayo ni a guardar una plantilla de datos.

Para continuar un trabajo, abre su carpeta raíz desde la aplicación. **Cerrar experimento** vuelve a la pantalla vacía; no elimina la carpeta. Guarda antes de cerrar si quieres conservar las modificaciones de la tabla.

## 5. Introducir datos

Cada fila representa una lectura original. El tipo de lectura se elige de una lista: patrón, blanco, control o muestra, según el método. Puedes añadir nombres personalizados vinculados a esas categorías. Los identificadores internos se generan automáticamente.

Un clic selecciona la celda. Escribir sustituye su contenido; F2 o doble clic permite editar el texto existente. Puedes pegar una tabla de Excel con tabulaciones desde la celda seleccionada. Añade las filas necesarias con el control de cantidad de filas. Los asteriscos rojos indican campos obligatorios para la categoría y el protocolo de esa fila. Las columnas atenuadas no se utilizan en ese contexto.

Las ayudas de las cabeceras explican qué introducir. No confundas un campo vacío con un cero medido. Usa valores numéricos y las unidades indicadas; el programa admite coma o punto decimal en la entrada manual.

| Campo | Qué significa |
| --- | --- |
| Muestra / Sample | Nombre que agrupa los resultados de esa muestra o variedad. |
| Réplica biológica | Identifica muestras biológicas independientes. |
| Réplica técnica | Lecturas repetidas del mismo material biológico. |
| Concentración del patrón | Concentración en las unidades del protocolo, utilizada para la calibración. |
| Dilución | Factor adimensional: 1 es sin diluir; 2 significa llevar una parte de extracto a dos partes de volumen total. No escribas una razón como `1:2`. |
| Volumen de extracto | Volumen total de extracción en mL, cuando el cálculo lo requiere; no el volumen de una alícuota. |
| Masa | Masa en g utilizada para expresar el resultado. Comprueba si corresponde a base seca o húmeda. |
| Corrección de matriz | Corrección adicional de señal definida en el protocolo; consulta la ayuda del método antes de aplicarla. |

### Varias variedades y réplicas

Usa nombres distintos en **Muestra**, por ejemplo `Variety A` y `Variety B`, dentro del mismo ensayo. Comparten la calibración de ese ensayo y se presentan como resultados separados. Para otra calibración, crea otro ensayo.

Las réplicas técnicas se agrupan antes de resumir las biológicas. Tres lecturas de una misma extracción no equivalen a tres muestras biológicas independientes. Las demostraciones con variedades permiten comprobar esta diferencia. El mismo nombre en FRAP y TPC no mezcla sus resultados ni sus unidades.

## 6. Protocolos y plantillas

En **Protocolo y condiciones / Protocol and conditions** revisa unidades, concentraciones, diluciones y demás parámetros. Guardar una variante crea una versión para reutilizar esas condiciones; el experimento conserva la versión que utilizó. No cambia retrospectivamente todos los experimentos anteriores.

La ficha de metodología incluye las fuentes originales. Una adaptación bibliográfica no implica que las condiciones hayan sido validadas para tu matriz. Los métodos con condiciones pendientes requieren completarlas. No interpretes un resultado de equivalentes, un porcentaje de inhibición y un EC50 como magnitudes intercambiables. En dosis-respuesta, revisa la definición de dosis y la cobertura del intervalo: no fuerces una extrapolación fuera de los datos.

Las **plantillas de datos** reutilizan el diseño: nombres de muestras, patrones y réplicas. Comprueba si al guardarlas has elegido incluir medidas. En una plantilla para nuevas medidas conviene dejar absorbancias y masas medidas vacías. Al cargarla, revisa su compatibilidad con el método seleccionado.

Crear una variante desde la interfaz sirve para modificar condiciones de un cálculo existente. Incorporar un motor de cálculo distinto requiere modificar el código; se explica en [Desarrollo](DEVELOPMENT.md).

## 7. Guardar, recalcular y exportar

**Guardar** conserva los datos y condiciones del experimento. **Actualizar y exportar** recalcula mediante Excel, comprueba los resultados, actualiza Origin si está habilitado y exporta las figuras. Son operaciones diferentes.

Cierra el libro del experimento en Excel y su proyecto en Origin antes de actualizar. Si estás abriendo el Excel, espera, guarda y ciérralo. El programa evita sobrescribir un libro en uso. La barra integrada muestra las fases; el registro aporta detalles cuando una fase falla.

Puedes modificar manualmente las entradas editables del Excel. Mantén sus nombres de hojas, cabeceras e identificadores y no sobrescribas las fórmulas. Después usa la actualización explícita. Si también vas a editar los datos en la aplicación, vuelve a abrir el experimento para leer los cambios externos antes de guardar la tabla: una tabla antigua no representa necesariamente el Excel que acabas de modificar.

Los modos de Origin son:

| Modo | Comportamiento |
| --- | --- |
| Conector Excel | Intenta establecer la conexión con las hojas de resultados. Su disponibilidad depende de Origin local. |
| Valores | Transfiere los resultados calculados a Origin de forma explícita. |
| Sin Origin | Permite trabajar sin crear el proyecto nativo. Las figuras alternativas utilizan los resultados disponibles. |

No se promete sincronización permanente al escribir en Excel. La acción fiable es **Actualizar y exportar**. Revisa los controles de calidad y avisos antes de usar los resultados. Un archivo generado correctamente puede contener datos insuficientes o un ensayo pendiente de revisión.

## 8. Dónde están los archivos

Ejemplo de organización; los nombres de los ensayos dependen de tu experimento:

```text
EXP_001/
  Documents/
    EXP_001.xlsx
    EXP_001.opju
  Figures/
    A01_FRAP/
      Excel/
      Origin/
      Publication/
    A02_TPC/
      ...
  Results/
    ...
  _internal/
    ...
```

`Documents` contiene los archivos de trabajo principales; `Figures` separa las exportaciones por ensayo y generador. El Excel separa ensayos por hojas y Origin por carpetas. `_internal` conserva versiones, estado y trazabilidad: no necesitas editarlo para usar el programa, pero forma parte del experimento.

Los botones de Excel y Origin abren sus archivos. El botón de figuras abre la carpeta general si hay varios ensayos; con un único ensayo y figuras disponibles puede abrir directamente su carpeta. Antes de generar figuras, la carpeta puede estar vacía.

Para mover o respaldar el trabajo, copia toda la carpeta raíz. Los nombres principales proceden del nombre del experimento al crearlo; renombrar archivos individuales puede romper referencias.

## 9. Idioma, apariencia y gráficos

El selector de idioma cambia la interfaz; el selector claro/oscuro cambia su apariencia. Los nombres de muestra y textos introducidos por ti no se traducen automáticamente. Los gráficos científicos utilizan inglés.

La ventana de estilos permite elegir una plantilla y ajustar colores, símbolos, líneas, barras de error y tipografía por tipo de gráfica. La previsualización usa ejemplos: no recalcula el experimento. Para aplicar cambios a archivos exportados, guarda el estilo y actualiza los resultados.

Las figuras de **Origin** pertenecen al proyecto editable. **Publication** ofrece exportaciones alternativas. Revisa las unidades, el número de réplicas, las barras de error y la legibilidad al tamaño final del artículo. Si haces ajustes manuales en Origin, conserva una copia antes de regenerar: una reconstrucción puede reemplazar los gráficos generados.

## 10. Actualizaciones

El menú de actualizaciones permite consultar GitHub y descargar versiones. Mantén los experimentos fuera de `Application`. El actualizador verifica el paquete y comprueba el arranque; si falla, intenta restaurar la versión anterior. Conserva una copia de seguridad independiente de tus trabajos.

Si utilizas la versión 0.7.0 y aparece `[Errno 2]` al buscar actualizaciones, instala manualmente la última versión desde GitHub una vez. No necesitas instalar las versiones intermedias. Para una copia del código modificada por ti, utiliza Git y tu entorno de desarrollo en lugar del actualizador binario.

## 11. Resolver problemas

| Problema | Qué comprobar |
| --- | --- |
| Excel está en uso o abriéndose | Guarda y cierra ese libro, espera a que termine de cerrarse y vuelve a actualizar. |
| Los cambios externos no aparecen en la tabla | Vuelve a abrir el experimento antes de editarlo y guardarlo desde la aplicación. |
| Faltan resultados | Revisa los campos obligatorios, blancos, patrones y controles de calidad del ensayo. |
| No se crea Origin | Comprueba instalación, licencia, diagnóstico y modo seleccionado; prueba con datos sintéticos. |
| La carpeta de figuras está vacía | Guarda y ejecuta la actualización; revisa en el registro qué fase terminó. |
| Un estilo nuevo no aparece en los archivos | Guarda el estilo y regenera las exportaciones. |
| Falla la consulta de actualizaciones | Reintenta con conexión a Internet o descarga el instalador de la última versión. |
| Un error interrumpe la generación | Conserva la carpeta y consulta el registro antes de borrar o editar archivos internos. |

Puedes comunicar errores en [GitHub Issues](https://github.com/RpastranaE/PhDexLab/issues) o a **rpe10@alu.ua.es**. Incluye versión, pasos y mensaje de error. Comparte un ejemplo sintético: los experimentos y registros pueden contener información privada.

## 12. Créditos y licencias

Proyecto personal de **RpastranaE**, desarrollado con asistencia de inteligencia artificial (ChatGPT/Codex), sin afiliación oficial con OpenAI, Microsoft u OriginLab. Contacto: **rpe10@alu.ua.es**.

El código se publica bajo [licencia MIT](../LICENSE). Consulta [los avisos de terceros](../THIRD_PARTY_NOTICES.md) y las licencias incluidas en la distribución. Excel y OriginPro son productos independientes y requieren sus propias licencias. La licencia del programa no sustituye la revisión científica de los protocolos.
