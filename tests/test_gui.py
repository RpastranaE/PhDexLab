import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from phdexlab.interface import Window
from phdexlab.data_entry import normalize

def test_gui_demo_and_parameters(tmp_path):
    app=QApplication.instance() or QApplication([])
    w=Window();w.load_demo()
    assert len(normalize(w.raw.records(),w.protocol()))==27
    assert w.protocol()['equivalent']=='Fe(II)'
    w.set_protocol(dict(w.protocol(),time_min=8))
    assert w.protocol()['time_min']==8
    w.close()
