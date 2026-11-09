import os,json,ctypes
from pathlib import Path
from unittest.mock import patch
import pytest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QLineEdit,QAbstractItemView,QProgressBar,QLabel
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from phdexlab.workspace import Window
from phdexlab.protocols import FE
from phdexlab import i18n
from phdexlab.paths import Layout
from phdexlab.file_access import WorkbookInUseError,assert_available,EXCEL_IN_USE

@pytest.fixture(autouse=True)
def isolated(monkeypatch,tmp_path):
    monkeypatch.setenv('PHDEXLAB_DATA_DIR',str(tmp_path/'personal'));i18n.set_language('en')
    yield
    i18n.set_language('es')

def app():return QApplication.instance() or QApplication([])

def test_initial_new_and_close_are_truly_empty():
    q=app();w=Window();w.show();q.processEvents()
    for _ in range(3):
        assert w.assays==[] and w.active_id is None and w.protocol()=={}
        assert w.assay_list.count()==0 and w.variant.count()==0 and w.raw.rowCount()==0 and w.parameters.rowCount()==0
        assert w.assay_pages.currentWidget()==w.empty_page and w.first_assay_button.isEnabled()
        assert not w.save_variant_button.isEnabled()
        with pytest.raises(ValueError,match='assay'):w.save()
        assert w.append_assay(FE,'My first FRAP')=='A01_FRAP'
        assert w.assay_pages.currentWidget()==w.tabs and w.save_variant_button.isEnabled()
        w.dirty=False;w.close_experiment()
    w.language_selector.setCurrentIndex(0);assert w.assays==[] and w.protocol()=={}
    w.close()

def test_duplicate_and_save_protocol_have_different_icons():
    q=app();w=Window();w.append_assay(FE,'FRAP')
    duplicate=next(b for b in w.buttons if b.toolTip() in ('Duplicate selected assay','Duplicar el ensayo seleccionado'))
    assert duplicate.property('iconName')!=w.save_variant_button.property('iconName')
    assert duplicate.icon().pixmap(24).toImage()!=w.save_variant_button.icon().pixmap(24).toImage()
    w.dirty=False;w.close()

def test_first_real_launch_help_is_remembered(tmp_path):
    from phdexlab.onboarding import show_on_first_use
    q=app();w=Window();assert not w.help_dialog.isVisible()
    assert not (tmp_path/'personal').exists()
    assert show_on_first_use(w);q.processEvents();assert w.help_dialog.isVisible()
    assert '<img' in w.help_dialog.browser.toHtml()
    w.help_dialog.close();assert not show_on_first_use(w);assert not w.help_dialog.isVisible()
    w.close();second=Window();assert not show_on_first_use(second);second.close()

def test_all_help_topics_have_real_bilingual_images():
    from phdexlab.help_images import FILES,illustration
    from phdexlab import help_images
    from PySide6.QtGui import QImage
    for lang in ('en','es'):
        i18n.set_language(lang)
        for i,name in enumerate(FILES):
            path=Path(help_images.__file__).parent/'assets/help'/lang/(name+'.png')
            assert not QImage(str(path)).isNull()
            assert '<img' in illustration(i,700)

def test_excel_style_click_then_type_and_f2():
    q=app();w=Window();w.load_demo();w.show();q.processEvents();table=w.raw
    index=table.model().index(0,2);point=table.visualRect(index).center()
    QTest.mouseClick(table.viewport(),Qt.MouseButton.LeftButton,pos=point)
    QTest.mouseClick(table.viewport(),Qt.MouseButton.LeftButton,pos=point)
    assert table.state()!=QAbstractItemView.State.EditingState
    QTest.keyClicks(table,'N');q.processEvents()
    editor=next(e for e in table.findChildren(QLineEdit) if e.isVisible());assert editor.text()=='N'
    QTest.keyClicks(editor,'EW');assert editor.text()=='NEW'
    QTest.keyClick(editor,Qt.Key.Key_Return);q.processEvents();assert table.item(0,2).text()=='NEW'
    table.setCurrentCell(0,2);QTest.keyClick(table,Qt.Key.Key_F2);q.processEvents()
    editor=next(e for e in table.findChildren(QLineEdit) if e.isVisible());assert editor.text()=='NEW'
    QTest.keyClick(editor,Qt.Key.Key_Escape)
    w.tabs.setCurrentIndex(1);q.processEvents()
    r=next(r for r in range(w.parameters.rowCount()) if w.parameters.item(r,0).data(Qt.ItemDataRole.UserRole)=='time_min')
    table=w.parameters;point=table.visualRect(table.model().index(r,1)).center()
    QTest.mouseClick(table.viewport(),Qt.MouseButton.LeftButton,pos=point);QTest.mouseClick(table.viewport(),Qt.MouseButton.LeftButton,pos=point)
    assert table.state()!=QAbstractItemView.State.EditingState
    QTest.keyClicks(table,'8');q.processEvents();editor=next(e for e in table.findChildren(QLineEdit) if e.isVisible());assert editor.text()=='8'
    QTest.keyClick(editor,Qt.Key.Key_Return);q.processEvents();assert w.protocol()['time_min']==8
    w.dirty=False;w.close()

def test_pending_shell_open_blocks_worker_before_it_starts(tmp_path):
    q=app();w=Window();w.load_demo();w.folder=tmp_path;Layout(tmp_path).prepare();Layout(tmp_path).master.write_bytes(b'workbook')
    with patch('phdexlab.interface.os.startfile') as opened:w.open_excel();assert opened.called
    with patch('phdexlab.interface.Window.start') as started:
        with pytest.raises(WorkbookInUseError,match='Excel'):w.start('refresh')
        assert not started.called
        w._excel_launch['seen']=True
        w.start('refresh');assert started.called
    w.dirty=False;w.close()

@pytest.mark.skipif(os.name!='nt',reason='Windows sharing semantics')
def test_native_file_sharing_error_is_actionable_and_non_destructive(tmp_path):
    path=tmp_path/'Workbook.xlsx';path.write_bytes(b'user data');assert_available(path)
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);create=kernel.CreateFileW;create.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE];create.restype=wintypes.HANDLE
    handle=create(str(path),0x80000000,1,None,3,0x80,None);assert handle!=wintypes.HANDLE(-1).value
    try:
        with pytest.raises(WorkbookInUseError,match='Guarda y cierra'):assert_available(path)
        assert path.read_bytes()==b'user data'
    finally:
        kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle(handle)
    assert_available(path)

def test_download_progress_stays_in_its_dialog():
    q=app();w=Window();assert not hasattr(w.updates,'bar')
    assert len(w.centralWidget().findChildren(QProgressBar))==1
    w.updates.show_dialog();w.updates.set_status(50,'Descargando actualización…');q.processEvents()
    assert w.updates.dialog_bar.isVisible() and w.updates.dialog_bar.value()==50
    assert not any('Updates replace' in label.text() for label in w.updates.dialog.findChildren(QLabel))
    assert not w.progress_panel.isVisible()
    w.updates.dialog.close();w.close()
