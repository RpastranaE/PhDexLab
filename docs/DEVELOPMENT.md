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

Prueba también dos ensayos en un mismo experimento, varias muestras con calibración común, réplicas técnicas y biológicas y la reapertura de un trabajo anterior.

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
