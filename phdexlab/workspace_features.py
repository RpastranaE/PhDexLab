"""Workspace presentation and reusable-input controls; no chemistry calculations."""
import json
from pathlib import Path
from PySide6.QtCore import Qt,QObject,QEvent,QTimer
from PySide6.QtWidgets import (QApplication,QWidget,QDialog,QMenu,QComboBox,QLabel,QVBoxLayout,QFormLayout,QLineEdit,QCheckBox,QDialogButtonBox,QInputDialog,QMessageBox,QAbstractButton)
from . import i18n,ui_icons
from .i18n import t,localize
from .appearance import preferences,save_preferences,stylesheet
from .graph_styles import DEFAULT,read_presentation,save_presentation,presentation_hash
from .data_templates import make_template,save_template,catalog,instantiate
from .paths import Layout

class DialogTranslator(QObject):
    def eventFilter(self,obj,event):
        if event.type()==QEvent.Type.Show and isinstance(obj,(QDialog,QMenu)):
            localize(obj)
            if isinstance(obj,QMenu):
                for action in obj.actions():action.setText(t(action.text()))
        return False

class WorkspaceFeatures:
    def setup_features(self):
        from .i18n_fields import register
        register();pref=preferences();self.theme_dark=pref['theme']=='dark';self.graph_style=DEFAULT
        i18n.set_language(pref['language']);self.dialog_translator=DialogTranslator(self);QApplication.instance().installEventFilter(self.dialog_translator)
        self.pathlabel.setProperty('userData',bool(self.folder))
        layout=self.centralWidget().layout();heading=layout.itemAt(0).layout();bottom=layout.itemAt(3).layout()
        self.language_selector=QComboBox();self.language_selector.addItem('Español','es');self.language_selector.addItem('English','en');self.language_selector.setToolTip('Idioma de la interfaz');self.language_selector.setCurrentIndex(0 if pref['language']=='es' else 1);heading.insertWidget(heading.count()-1,self.language_selector)
        self.theme_button=self.make_button('Cambiar a modo oscuro',self.toggle_theme,'theme',heading);self.buttons.remove(self.theme_button)
        self.templates_button=self.make_button('Plantillas de datos',lambda:None,'template',bottom);self.templates_menu=QMenu(self.templates_button)
        self.templates_menu.addAction('Guardar plantilla de datos',lambda:self.guard(self.save_data_template));self.templates_menu.addAction('Cargar plantilla de datos',lambda:self.guard(self.load_data_template))
        self.templates_button.setMenu(self.templates_menu)
        from PySide6.QtWidgets import QToolButton
        self.templates_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.graph_button=self.make_button('Personalizar gráficas',self.customize_graphs,'palette',bottom)
        # Keep controls next to the other bottom toolbar actions, before its stretch and legend.
        for button in (self.templates_button,self.graph_button):bottom.removeWidget(button);bottom.insertWidget(max(0,bottom.count()-2),button)
        self.language_selector.currentIndexChanged.connect(self.change_language)
        self.row_count.setSuffix(t(' filas'))
        for button in self.buttons:
            if button.property('iconName')=='refresh':
                button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu);button.customContextMenuRequested.connect(lambda point,b=button:self.rebuild_menu(b,point))
        self.set_protocol(self.protocol());self.raw.set_protocol(self.protocol()) if self.active_id else None;self.apply_appearance();self.retranslate_ui()
        for i,a in enumerate(self.assays):self.assay_list.item(i).setText(self.item_text(a))
        from .ui_tooltips import install_tooltips
        install_tooltips(self)
        from .updater_ui import UpdateController
        self.updates=UpdateController(self)
    def rebuild_menu(self,button,point):
        menu=QMenu(self);menu.addAction(t('Regenerar todos los archivos'),lambda:self.guard(self.force_rebuild));menu.exec(button.mapToGlobal(point))
    def force_rebuild(self):
        self.update(force=True)
    def retranslate_ui(self):
        if not getattr(self,'language_selector',None):return
        self.pathlabel.setProperty('userData',bool(self.folder))
        localize(self);self.row_count.setSuffix(t(' filas'))
        for menu in (self.demo_menu,self.templates_menu):
            for action in menu.actions():
                cache=getattr(action,'_source_text',action.text());action._source_text=cache;action.setText(t(cache))
        self.help_dialog.retranslate()
        self.refresh_result_context(force=True)
        self.log.retranslate()
    def change_language(self,*args):
        self.commit_active();was_dirty=self.dirty;rows=self.raw.records();p=self.protocol();i18n.set_language(self.language_selector.currentData())
        self.loading=True;self.set_protocol(p);self.populate_variants(p);self.raw.set_protocol(p) if p else None;self.raw.load(rows) if p else None;self.loading=False;self.dirty=was_dirty
        for i,a in enumerate(self.assays):self.assay_list.item(i).setText(self.item_text(a))
        self.update_current_state();self.retranslate_ui();save_preferences(i18n.LANGUAGE,'dark' if self.theme_dark else 'light')
    def apply_appearance(self):
        self.setStyleSheet(stylesheet(self.theme_dark));self.assay_list.setStyleSheet('')
        for label in self.findChildren(QLabel):
            if label.text() in ('ENSAYOS DEL EXPERIMENTO','EXPERIMENT ASSAYS'):label.setStyleSheet('font-weight:700;padding:8px 0;color:'+('#83D5DA' if self.theme_dark else '#176E78'))
        if not self.theme_dark:self.assay_list.setStyleSheet('QListWidget{background:white;border:1px solid #D9E6EB;border-radius:7px} QListWidget::item{padding:12px 6px;border-bottom:1px solid #E7EFF1} QListWidget::item:selected{background:#D8EEF1;color:#123E49}')
        self.raw.dark=self.theme_dark
        for row in range(self.raw.rowCount()):self.raw.update_row(row)
        ui_icons.COLOR='#92DDE2' if self.theme_dark else '#176E78'
        for button in self.findChildren(QAbstractButton):
            name=button.property('iconName')
            if name:button.setIcon(ui_icons.icon(name))
        self.theme_button.setToolTip(t('Cambiar a modo claro' if self.theme_dark else 'Cambiar a modo oscuro'))
        self.help_dialog.retranslate()
        self.refresh_result_context(force=True)
    def toggle_theme(self):
        self.theme_dark=not self.theme_dark;self.apply_appearance();save_preferences(i18n.LANGUAGE,'dark' if self.theme_dark else 'light')
    def customize_graphs(self):
        from .graph_dialog import GraphDialog
        dialog=GraphDialog(self.graph_style,self)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        from .graph_styles import selection
        if dialog.selected==selection(self.graph_style):return
        self.graph_style=dialog.selected
        if self.folder:save_presentation(self.folder,self.graph_style)
        else:self.dirty=True
        self.log.appendPlainText(t('La personalización se guardará con el experimento. Actualiza para regenerar las figuras.'))
    def save_data_template(self):
        self.commit_active();dialog=QDialog(self);dialog.setWindowTitle(t('Guardar plantilla de datos'));layout=QVBoxLayout(dialog);form=QFormLayout();layout.addLayout(form)
        name=QLineEdit();form.addRow(t('Nombre de la plantilla'),name);keep=QCheckBox(t('Conservar también lecturas experimentales'));layout.addWidget(keep)
        note=QLabel(t('Por defecto se guardan muestras, réplicas, dosis, tiempos y concentraciones; se vacían las mediciones y la confirmación de meseta.'));note.setWordWrap(True);layout.addWidget(note)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel);buttons.button(QDialogButtonBox.StandardButton.Save).setText(t('Guardar plantilla'));buttons.button(QDialogButtonBox.StandardButton.Save).setEnabled(False);name.textChanged.connect(lambda value:buttons.button(QDialogButtonBox.StandardButton.Save).setEnabled(bool(value.strip())));buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons);dialog.resize(620,220)
        if dialog.exec()==QDialog.DialogCode.Accepted:
            template=make_template(name.text(),self.protocol(),self.raw.records(),keep.isChecked());save_template(template);self.log.appendPlainText(t('Guardar plantilla de datos')+': '+template['name'])
    def load_data_template(self):
        from .assay_engine import engine
        p=self.protocol();items=[]
        for item in catalog():
            try:instantiate(item,p);items.append(item)
            except ValueError:pass
        if not items:QMessageBox.information(self,t('Plantillas de datos'),t('No hay plantillas compatibles con este método.'));return
        dialog=QDialog(self);dialog.setWindowTitle(t('Cargar plantilla de datos'));layout=QVBoxLayout(dialog);choices=QComboBox()
        for item in items:choices.addItem(item['name']+' · '+t('Incluye mediciones' if item['contains_readings'] else 'Estructura sin mediciones'))
        layout.addWidget(choices);mode=QComboBox();mode.addItem(t('Sustituir las filas del ensayo'),False);mode.addItem(t('Añadir al final'),True);layout.addWidget(mode);warning=QLabel();warning.setWordWrap(True);layout.addWidget(warning)
        def changed():warning.setText(t('La plantilla contiene lecturas. Revísalas antes de reutilizarlas; no representan un experimento nuevo.') if items[choices.currentIndex()]['contains_readings'] else '')
        choices.currentIndexChanged.connect(changed);changed()
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t('Aplicar plantilla'));buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons);dialog.resize(640,220)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        rows=instantiate(items[choices.currentIndex()],p)
        if mode.currentData():rows=self.raw.records()+rows
        if len(rows)>10000:raise ValueError('Máximo: 10000 lecturas')
        self.raw.load(rows);self.dirty=True;self.update_current_state()
