"""Regression checks for spreadsheet editing, update choices and readable help."""
import os,copy
from pathlib import Path
from unittest.mock import patch
import pytest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import Qt,QUrl
from PySide6.QtWidgets import QApplication,QLineEdit,QMessageBox,QTableWidgetSelectionRange
from PySide6.QtTest import QTest
from phdexlab import i18n,updater
from phdexlab.workspace import Window
from phdexlab.graph_styles import selection,resolved,role_style

@pytest.fixture
def window(tmp_path,monkeypatch):
    monkeypatch.setenv('PHDEXLAB_DATA_DIR',str(tmp_path/'personal'))
    q=QApplication.instance() or QApplication([]);i18n.set_language('en')
    w=Window();w.load_demo();w.show();q.processEvents()
    yield w
    w.dirty=False;w.updates.ready=None;w.close();q.processEvents();i18n.set_language('es')

def test_clear_text_in_editor_and_delete_contents(window):
    q=QApplication.instance();table=window.raw;c=table.columns.index('sample_id')
    table.setCurrentCell(0,c);table.editItem(table.item(0,c));q.processEvents();editor=q.focusWidget();assert isinstance(editor,QLineEdit)
    editor.selectAll();QTest.keyClick(editor,Qt.Key.Key_Backspace);QTest.keyClick(editor,Qt.Key.Key_Return);q.processEvents()
    assert table.item(0,c).text()==''
    table.setCurrentCell(1,c);QTest.keyClick(table,Qt.Key.Key_Delete)
    assert table.item(1,c).text()=='' and window.dirty
    window.commit_active();window.assay_list.setCurrentRow(0);assert window.assays[0]['rows'][0]['sample_id']==''

def test_copy_cut_paste_and_empty_paste(window):
    table=window.raw;c=table.columns.index('sample_id');old=table.item(0,c).text();table.setCurrentCell(0,c)
    QTest.keyClick(table,Qt.Key.Key_C,Qt.KeyboardModifier.ControlModifier);assert QApplication.clipboard().text()==old
    QTest.keyClick(table,Qt.Key.Key_X,Qt.KeyboardModifier.ControlModifier);assert table.item(0,c).text()==''
    QTest.keyClick(table,Qt.Key.Key_V,Qt.KeyboardModifier.ControlModifier);assert table.item(0,c).text()==old
    table.paste('');assert table.item(0,c).text()==''

def test_whole_row_copy_paste_allocates_new_ids_and_delete_is_persistent(window):
    table=window.raw;old=copy.deepcopy(table.records()[0]);before=table.rowCount();table.selectRow(0);table.copy_cells(True)
    table.setCurrentCell(2,1);table.paste_rows();rows=table.records()
    assert table.rowCount()==before+1 and rows[2]['record_id']!=old['record_id']
    assert all(rows[2][key]==value for key,value in old.items() if key not in ('record_id','kind_label'))
    table.selectRow(2);table.delete_rows();assert table.rowCount()==before and len(table.records())==len(window.assays[0]['rows'])
    assert window.dirty

def test_paste_invalid_role_is_atomic_and_uses_visible_columns(window):
    table=window.raw;before=copy.deepcopy(table.records());table.setCurrentCell(0,1)
    with pytest.raises(ValueError):table.paste('sample\tA\nNOT_A_KIND\tB')
    assert table.records()==before
    table.setCurrentCell(0,table.columns.index('notes'));table.paste('note\tIGNORED_HIDDEN_ID')
    assert table.item(0,table.columns.index('notes')).text()=='note'
    assert table.item(0,0).text()==before[0]['record_id']

@pytest.mark.parametrize('role',['results','calibration','dose'])
def test_no_markers_preview_and_serialization(role):
    from phdexlab.graph_dialog import preview
    q=QApplication.instance() or QApplication([]);s=selection('classic');before=preview(resolved(s),role=role).toImage()
    s['settings'][role]['marker']='none';style=resolved(selection(s));assert role_style(style,role)['symbol']==0
    assert before!=preview(style,role=role).toImage()

def test_readable_images_viewer_and_credits(window):
    from phdexlab.help_images import FILES
    from PySide6.QtGui import QImage
    from phdexlab import help_images
    for lang in ('en','es'):
        for name in FILES:
            image=QImage(str(Path(help_images.__file__).parent/'assets/help'/lang/(name+'.png')))
            assert image.width()>=1200 and image.height()>=240
    help=window.help_dialog;help.open_link(QUrl('phdexlab-help:3'));viewer=help.image_viewer
    viewer.zoom.setValue(100);assert viewer.label.pixmap().size()==viewer.original.size();viewer.close()
    help.topics.setCurrentRow(12);text=help.browser.toPlainText()
    assert 'rpe10@alu.ua.es' in text and 'MIT' in text and 'ChatGPT/Codex' in text

def test_release_check_offers_both_choices_without_downloading(window,tmp_path):
    c=window.updates;c.root=tmp_path;c.finished({'release':{'newer':True,'version':'9.0.0'},'stage':None},'')
    assert c.dialog.isVisible() and c.now_button.isVisible() and c.exit_button.isVisible()
    assert c.ready is None and not c.install_action
    with patch.object(c,'begin_download') as download:c.choose_install('exit');assert download.called and c.install_action=='exit'
    c.dialog.close()

@pytest.mark.parametrize('action',['now','exit'])
def test_explicit_install_choice_restarts_even_if_background_checks_disabled(window,tmp_path,action):
    c=window.updates;c.root=tmp_path;c.ready=tmp_path/'stage';c.install_action=action;updater.set_automatic(False)
    with patch('phdexlab.updater.schedule_install') as install:
        assert c.prepare_close();assert install.call_args.kwargs['relaunch'] is True

def test_update_now_respects_unsaved_cancel(window,tmp_path):
    c=window.updates;c.root=tmp_path;c.ready=tmp_path/'stage';window.dirty=True
    with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Cancel),patch('phdexlab.updater.schedule_install') as install:
        c.choose_install('now');QApplication.instance().processEvents();assert window.isVisible() and window.dirty and not install.called

@pytest.mark.parametrize('run_now',[False,True])
def test_new_save_offers_calculation(window,tmp_path,run_now):
    def answer(dialog):
        button=next(b for b in dialog.buttons() if ('Update and export now' if run_now else 'Continue editing')==b.text())
        button.click();return 0
    with patch('phdexlab.workspace.QFileDialog.getExistingDirectory',return_value=str(tmp_path)),patch('phdexlab.workspace.QInputDialog.getText',return_value=('NEW_EXP',True)),patch.object(QMessageBox,'exec',answer),patch.object(window,'start') as start:
        window.save();assert (tmp_path/'NEW_EXP/Documents/NEW_EXP.xlsx').is_file();assert start.called==run_now
