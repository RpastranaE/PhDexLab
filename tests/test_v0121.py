import pytest
from PySide6.QtCore import Qt,QTimer,QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QToolButton


@pytest.mark.parametrize('language,width',[('es',1000),('en',1000),('es',1280),('en',1480)])
def test_data_entry_whole_button_opens_import_menu_without_tab_overlap(tmp_path,monkeypatch,language,width):
    monkeypatch.setenv('PHDEXLAB_DATA_DIR',str(tmp_path))
    from phdexlab import workspace
    from phdexlab.interface import configure_font
    configure_font(QApplication.instance())
    from phdexlab.appearance import save_preferences
    save_preferences(language,'light')
    w=workspace.Window();w.load_demo();w.resize(width,800);w.show();QApplication.processEvents()
    b=w.measure_button
    assert b.isVisible() and b.isEnabled()
    assert b.popupMode()==QToolButton.ToolButtonPopupMode.InstantPopup
    corner=w.tabs.cornerWidget(Qt.Corner.TopRightCorner)
    assert corner is w.entry_corner
    assert w.tabs.rect().contains(b.mapTo(w.tabs,QPoint(0,0)))
    assert w.tabs.rect().contains(b.mapTo(w.tabs,b.rect().bottomRight()))
    assert corner.rect().contains(b.mapTo(corner,b.rect().bottomRight()))
    assert w.tabs.tabBar().geometry().right()<corner.geometry().left()
    called=[];opened=[]
    monkeypatch.setattr(w,'add_sample',lambda:called.append('sample'))
    monkeypatch.setattr(w,'import_readings',lambda:called.append('import'))
    def shown():
        opened.append(True)
        QTimer.singleShot(0,b.menu().close)
    b.menu().aboutToShow.connect(shown)
    # Test a click on the left icon and in the middle, never the arrow region.
    for pos in (QPoint(12,b.height()//2),b.rect().center()):
        QTest.mouseClick(b,Qt.MouseButton.LeftButton,pos=pos)
        QApplication.processEvents()
    assert len(opened)==2 and called==[]
    actions=[a for a in b.menu().actions() if not a.isSeparator()]
    assert ('Importar archivo' if language=='es' else 'Import file') in actions[1].text()
    actions[1].trigger();assert called==['import']
    actions[0].trigger();assert called==['import','sample']
    w.dirty=False;w.close()


@pytest.mark.parametrize('language',['en','es'])
def test_help_contains_import_and_calculation_route(language):
    from phdexlab import i18n
    from phdexlab.help_readings import revise
    i18n.set_language(language)
    content=revise([('title','') for _ in range(12)])
    assert ('Import a text file' if language=='en' else 'Importar un archivo de texto') in content[2][1]
    assert ('calculation route' if language=='en' else 'recorrido de cálculo') in content[8][1]
