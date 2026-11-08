import importlib.metadata
import platform
import sys

def diagnose():
    report={"python":sys.version,"platform":platform.platform(),"packages":{}}
    for name in ("PySide6","openpyxl","pywin32","originpro","OriginExt"):
        try: report["packages"][name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: report["packages"][name]="missing"
    try:
        import winreg
        for prog in ("Excel.Application","Origin.Application","Origin.ApplicationSI"):
            try:
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,prog+"\\CLSID") as key:
                    report[prog]=winreg.QueryValue(key,None)
            except OSError as e: report[prog]=str(e)
    except ImportError: pass
    report["note"]="Registro/instalación no prueba funcionamiento. Ver informe de ejecución con Excel y Origin."
    return report
