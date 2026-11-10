# Modificar, probar y distribuir PhDexLab

[Inicio](../README.md) · [Manual de uso](MANUAL.md) · [Validación](VALIDATION.md) · [Historial](../CHANGELOG.md)

Esta guía explica cómo trabajar con el código. Para instalar la aplicación sin modificarla, sigue el [manual](MANUAL.md).

## Preparar el entorno

Descarga el código con Git o mediante **Code → Download ZIP**. Para desarrollar utiliza Windows de 64 bits y Python 3.12, la versión comprobada para las distribuciones actuales. El rango declarado en el proyecto no significa que todas sus combinaciones se hayan probado con Excel y Origin.

Desde la carpeta del código, en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m phdexlab
```

Excel de escritorio y OriginPro se instalan por separado. No son necesarios para todas las pruebas unitarias, pero sí para comprobar la automatización nativa. El lanzador de conveniencia puede priorizar una distribución compilada existente: al modificar código, usa explícitamente `python -m phdexlab` para ejecutar tus cambios.

Trabaja en una rama o fork y utiliza datos sintéticos. El repositorio público no debe contener experimentos privados, credenciales, exportaciones de Notion ni registros con datos personales. Puedes aislar preferencias mediante `PHDEXLAB_DATA_DIR` en tu entorno de pruebas.

## Cómo se organiza el código

| Área | Responsabilidad |
| --- | --- |
| `protocols`, catálogo y motores de ensayo | Condiciones, variantes, campos y reglas específicas de cada método. |
| `data_entry`, `data_table`, `ui_fields` | Registros originales, tabla y ayudas de entrada. |
| `calculations`, `assay_engine` | Reglas y validaciones de cálculo. |
| `excel`, `multi_excel` | Construcción de libros con fórmulas y recálculo mediante Excel. |
| `origin`, `multi_origin` | Proyecto nativo, transferencia/conexión de resultados y exportación. |
| `publication`, `multi_publication`, `graph_styles` | Figuras alternativas y configuración visual. |
| `interface`, `workspace`, `workspace_features` | Interfaz y coordinación de experimentos con varios ensayos. |
| `experiments`, `integration` | Persistencia y operaciones reutilizables para futura integración externa. |
| `updater`, `updater_ui`, `assets/install-update.ps1` | Consulta, descarga, verificación y reemplazo del programa. |

Comprueba los nombres y puntos de entrada en el código al ampliar un área. Algunos módulos mantienen compatibilidad con experimentos antiguos de un solo ensayo. La interfaz actual usa el espacio de trabajo de varios ensayos.

El Excel es la fuente de los cálculos exportados. Los gráficos deben leer sus resultados, evitando crear una segunda implementación numérica que pueda discrepar. Conserva los datos originales y la versión del protocolo utilizada. Una traducción de la interfaz no debe modificar nombres de muestra ni trazabilidad.

## Añadir o adaptar métodos

Para cambiar concentraciones, unidades o condiciones de un cálculo existente, prueba primero una variante desde la interfaz. Si la ecuación o el diseño experimental es distinto, modifica el catálogo y el motor correspondiente.

Un método nuevo necesita: fuente original y condiciones explícitas, campos y unidades, validaciones, fórmulas auditables de Excel, resultados y controles de calidad, gráficos, traducciones, una demostración y comprobaciones independientes. No reutilices automáticamente una fórmula de equivalentes para un porcentaje de inhibición o un EC50. No presentes condiciones incompletas como un método validado.

Prueba también dos ensayos en un mismo experimento, varias muestras con calibración común, réplicas técnicas y experimentales y la reapertura de un trabajo anterior.

## Uso programático y comandos

Ejemplo con una carpeta nueva o vacía, desde el entorno preparado:

```python
from phdexlab.demonstrations import multi_demo
from phdexlab.experiments import create, read, refresh

folder = create("DEMO_API", multi_demo())
assays = read(folder)
report = refresh(folder, origin_mode="none")  # El recálculo requiere Excel.
```

Para editar un experimento existente usa las funciones del módulo y su control de cambios externos; no escribas directamente los JSON internos saltándote la comprobación de versión/hash.

```powershell
.\.venv\Scripts\python.exe -m phdexlab diagnose
.\.venv\Scripts\python.exe -m phdexlab verify RUTA_DEL_EXPERIMENTO
.\.venv\Scripts\python.exe -m phdexlab refresh RUTA_DEL_EXPERIMENTO --origin none
```

El modo de Origin también puede ser `values` o `connector`. El comando de demostración heredado no equivale a todas las demostraciones de varios métodos de la interfaz. El diagnóstico de paquetes/registro COM no sustituye una generación real con las aplicaciones instaladas.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest
```

Ejecuta las pruebas desde la raíz del código. Las pruebas unitarias incluyen comportamiento de la interfaz y lógica de persistencia, pero no acreditan por sí solas la compatibilidad de cada instalación nativa.

Para repetir la auditoría de ecuaciones y unidades de las 15 variantes con Microsoft Excel:

```powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe tests/native_calculation_audit.py ..\PhDexLab-calculation-audit
```

La carpeta debe estar nueva/vacía. Produce un libro de 24 casos y un informe: las ocho variantes ópticas se comprueban con ambos ejes de calibración; se incluyen humedad, materia seca, cenizas en ambas bases, condiciones TAPPI completadas **solo como prueba sintética**, EC50 y balance de tamizado. El programa usa valores conocidos y factores dimensionales independientes del generador de fórmulas. Un segundo argumento opcional permite verificar localmente el banco FRAP del usuario; ese archivo no forma parte del repositorio ni de la distribución. Los resultados se recalculan con Excel, no con un emulador Python.

Los siguientes programas de prueba nativa heredados utilizan datos sintéticos de FRAP. Requieren Excel y Origin disponibles y una carpeta de destino nueva:

```powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe tests/native_validation.py ..\PhDexLab-native-test
.\.venv\Scripts\python.exe tests/varieties_validation.py ..\PhDexLab-varieties-test
```

Para una entrega comprueba además la aplicación compilada: varios métodos, edición de celdas, exportaciones, estilos, libros abiertos y actualización. [VALIDATION.md](VALIDATION.md) documenta qué se comprobó realmente y sus límites. Una prueba de software no equivale a una validación analítica.

## Compilar e instalar una distribución

Utiliza una copia de desarrollo, no la carpeta de instalación en uso. Necesitas PyInstaller y, para el instalador, Inno Setup. Los scripts de compilación indican sus dependencias y rutas aceptadas.

```powershell
.\Build-Windows.ps1
.\.venv\Scripts\python.exe tools/package_windows.py
.\Build-Installer.ps1 -Compiler "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

Respeta ese orden: el empaquetador incorpora avisos y licencias antes de que el instalador recoja `Application`. Se genera una aplicación de carpeta, un ZIP portátil y un instalador. No distribuyas únicamente el ejecutable interno. Consulta los parámetros de los scripts si tu entorno Python o las carpetas de salida son distintos.

Mantén coherentes las versiones de `phdexlab/__init__.py`, `pyproject.toml` y `installer/PhDexLab.iss`. Incluye las imágenes de ayuda, iconos y el ayudante de actualización. En runtimes que proporcionen `codex-rejected-cas.pem` junto a `ssl.py`, el empaquetado debe conservar esa política de certificados públicos. No resuelvas problemas TLS desactivando la verificación HTTPS.

La aplicación compilada admite `--update-healthcheck` y `--check-updates RUTA_JSON`. El primer comando comprueba el arranque sin consumir la bienvenida de primer uso; el segundo consulta las versiones públicas. En PowerShell, espera explícitamente al proceso gráfico si necesitas comprobar su resultado.

Para probar el instalador sin reemplazar la instalación real, usa una carpeta temporal y los parámetros `/InstallId=...`, `/DesktopDir=...`, `/MenuDir=...` y `/DIR=...`. Comprueba accesos directos, arranque, actualización y desinstalación, conservando un experimento de prueba fuera de `Application`. No cambies el identificador estable de la instalación pública entre actualizaciones.

## Publicación y contrato del actualizador

Solo el mantenedor con autorización debe publicar versiones en el repositorio original. Para contribuir, abre una propuesta desde tu fork. Una versión debe incluir el instalador, el ZIP portátil, `latest.json` y `SHA256SUMS.txt`, con nombres, tamaños y hashes coherentes. Actualiza las instrucciones vigentes y el historial; no crees una nueva guía de uso independiente para cada versión.

El script `tools/publish_release.ps1` publica una release: no es una simulación. Revisa primero sus parámetros y el contenido público. También puedes preparar una release borrador, subir los cuatro archivos, verificar sus hashes y publicarla después. Nunca incluyas credenciales ni archivos privados en el paquete o el historial Git.

El actualizador consulta el repositorio oficial por HTTPS y, si la API pública limita las peticiones, utiliza el manifiesto de la última release. Valida versión, URL, tamaño, SHA-256 e inventario de archivos. No necesita un token del usuario ni sube sus experimentos. Los hashes no sustituyen una firma Authenticode.

El reemplazo se prepara aparte, espera a que cierre el proceso, conserva respaldo, comprueba el arranque e intenta restaurar la versión anterior si falla. Una interrupción del sistema o fallo de disco sigue requiriendo recuperación y copia de seguridad. Si mantienes una versión propia, desactiva la actualización binaria para que no reemplace tus cambios.

## Documentación, créditos y licencias

El README es la entrada; el manual explica el uso; esta guía cubre desarrollo; VALIDATION contiene evidencias; PROTOCOL_SOURCES conserva las fuentes científicas y CHANGELOG el historial. Las guías anteriores quedan en `docs/archive`. Evita duplicar instrucciones actuales en varios documentos.

Proyecto personal de RpastranaE, creado con asistencia de ChatGPT/Codex. Contacto: **rpe10@alu.ua.es**. El código utiliza [MIT](../LICENSE); respeta [los avisos de terceros](../THIRD_PARTY_NOTICES.md), incluidas las obligaciones de redistribución de Qt/PySide6 y sus bibliotecas. Excel y OriginPro mantienen sus propias licencias.


## Validación y vista de resultados desde 0.10.0

Desde 0.10.1, `libraries` gestiona únicamente entradas del directorio de usuario: eliminación de archivos personales con comprobación de cambios, y ocultación/restauración de protocolos incluidos mediante preferencias independientes. `library_dialog` presenta búsqueda y confirmación. Al cerrar el gestor se reconstruye el catálogo del selector sin modificar el protocolo/RAW del ensayo, su estado de cambios ni los snapshots del experimento. `PHDEXLAB_DATA_DIR` también controla la biblioteca de variantes.

`input_validation` reutiliza los campos requeridos del motor; `validation_dialog` presenta los problemas sin iniciar el proceso de cálculo salvo elección explícita de continuar con ensayos completos. `workspace.update` confirma el editor activo y guarda antes de validar/iniciar el worker; el guardado mantiene la comprobación del hash del Excel abierto.

`results_view` lee únicamente los valores calculados del Excel (`data_only`) y los PNG de Origin registrados con sus hashes en el estado de generación. No contiene ecuaciones químicas. La lectura de hojas se limita al ensayo seleccionado; el monitor solo está activo mientras la pestaña está visible. Cambios de entradas/libro impiden mostrar resultados viejos; cambios de estilo/proyecto/figuras invalidan las previsualizaciones. Las pruebas GUI mantienen un único QApplication durante la sesión, como la aplicación real.

## Contrato de entrada desde 0.9.2

`reading_design.configure(protocol, legacy=True)` permite activar explícitamente las opciones en una copia de un protocolo anterior, manteniendo su señal y corrección. El catálogo nuevo ya incorpora el diseño. `assay_engine.columns(protocol)` es la autoridad del esquema RAW: las columnas de procedencia se añaden a continuación de las existentes, conservando las referencias históricas de las fórmulas.

`reading_basis` distingue `individual` de `mean`; `technical_n` y `technical_sd` son metadatos opcionales de una media. No expandas una media a filas ficticias. No mezcles ambos orígenes en la misma unidad/condición. En DPPH, la condición incluye dosis y tiempo. El motor genera las referencias y conversiones de SD en Excel; no se añade un segundo motor numérico de producción.

La selección `reading_signal` distingue `endpoint`, `paired` y `delta`; `response` se conserva como valor derivado para compatibilidad. Un cambio manual de señal no convierte las medidas existentes. Las pruebas nativas adicionales pueden ejecutarse con Excel real:

```powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe tests/native_reading_validation.py ..\PhDexLab-reading-test
```

El destino debe ser nuevo o vacío. La prueba compara diez métodos y tres variantes, lecturas individuales, medias con/sin precisión y ΔA directo, usando valores esperados independientes; guarda `validation.json`. No requiere Origin para esta comparación numérica. La generación completa del proyecto se comprueba por separado.

### Release highlights

`release_notes.py` bundles ES/EN highlights for offline use. Update those notes with each release. `onboarding.json` retains the last version shown: a fresh install opens Help and records the current version; an upgrade displays the highlights once. Legacy installations with Help already seen and no recorded version display the current notes once. Health checks construct the GUI without consuming this state.
