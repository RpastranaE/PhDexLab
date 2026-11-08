"""PyInstaller entry point, also supports worker subprocesses in the frozen app."""
import json
import sys
from pathlib import Path

def main():
    if '--worker' in sys.argv:
        from phdexlab.worker import run
        index=sys.argv.index('--worker')
        folder=Path(sys.argv[index+1])
        from phdexlab.paths import Layout
        log=Layout(folder).meta/'worker.log'
        with log.open('a',encoding='utf-8',buffering=1) as stream:
            sys.stdout=stream;sys.stderr=stream
            try:run(sys.argv[index+1:index+4])
            except Exception:
                import traceback
                traceback.print_exc();return 1
        return 0
    if '--smoke-test' in sys.argv or '--update-healthcheck' in sys.argv:
        if '--update-healthcheck' in sys.argv:
            import os,tempfile
            os.environ['QT_QPA_PLATFORM']='offscreen'
            health=tempfile.TemporaryDirectory(prefix='PhDexLab-health-');os.environ['PHDEXLAB_DATA_DIR']=health.name
        from PySide6.QtWidgets import QApplication
        from phdexlab.workspace import Window
        from phdexlab.interface import configure_font
        app=QApplication([]);configure_font(app);w=Window();w.load_demo();w.show();app.processEvents()
        if '--output' in sys.argv:
            path=Path(sys.argv[sys.argv.index('--output')+1]);path.parent.mkdir(parents=True,exist_ok=True);w.grab().save(str(path))
        assert len(w.raw.records())==27;assert not w.windowIcon().isNull();w.dirty=False;w.close()
        if '--update-healthcheck' in sys.argv:health.cleanup()
        return 0
    from phdexlab.interface import run
    return run()

if __name__=='__main__':
    try:code=main()
    except Exception:
        import traceback
        log=Path(sys.executable).parent/'startup-error.log' if getattr(sys,'frozen',False) else Path(__file__).parent/'startup-error.log'
        log.write_text(traceback.format_exc(),encoding='utf-8')
        code=1
    sys.exit(code)
