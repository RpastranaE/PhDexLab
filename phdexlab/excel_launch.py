"""Track the shell's asynchronous workbook launch and check before dispatching a worker."""
import time
from PySide6.QtCore import QTimer
from .file_access import assert_available,WorkbookInUseError,EXCEL_IN_USE
from .paths import Layout

def observe(window):
    pending=getattr(window,'_excel_launch',None)
    if not pending:return
    try:assert_available(pending['path']);busy=False
    except WorkbookInUseError:busy=True
    except OSError:busy=False
    if busy:pending['seen']=True
    elif pending['seen'] or time.monotonic()>=pending['deadline']:
        window._excel_launch=None;window._excel_launch_timer.stop()

def launching(window,path):
    window._excel_launch=dict(path=path,seen=False,deadline=time.monotonic()+12)
    if not hasattr(window,'_excel_launch_timer'):
        window._excel_launch_timer=QTimer(window);window._excel_launch_timer.setInterval(250);window._excel_launch_timer.timeout.connect(lambda:observe(window))
    window._excel_launch_timer.start()

def check(window):
    path=Layout(window.folder).master;observe(window)
    pending=getattr(window,'_excel_launch',None)
    if pending and pending['path']==path:raise WorkbookInUseError(EXCEL_IN_USE)
    assert_available(path)
