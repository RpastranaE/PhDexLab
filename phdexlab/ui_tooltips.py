"""Consistent visible hover descriptions, including inactive Windows app windows."""
from PySide6.QtCore import QObject,QEvent,Qt
from PySide6.QtWidgets import QApplication,QAbstractButton,QWidget,QToolTip,QDialogButtonBox
from . import i18n

STOCK={
 'Ok':('Aceptar','OK'),'Cancel':('Cancelar','Cancel'),'Close':('Cerrar','Close'),
 'Save':('Guardar','Save'),'Open':('Abrir','Open'),'Apply':('Aplicar','Apply'),
 'Yes':('Sí','Yes'),'No':('No','No'),'Discard':('Descartar','Discard'),
 'Reset':('Restablecer','Reset'),'Retry':('Reintentar','Retry')}

def describe(root):
    root.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips,True)
    for box in root.findChildren(QDialogButtonBox):
        for button in box.buttons():
            standard=box.standardButton(button)
            for name,labels in STOCK.items():
                if standard==getattr(QDialogButtonBox.StandardButton,name) and button.text().replace('&','') in labels:
                    button.setText(labels[1 if i18n.LANGUAGE=='en' else 0]);button.setToolTip(button.text())
    for button in root.findChildren(QAbstractButton):
        tip=button.toolTip() or button.accessibleName() or button.text().replace('&','')
        if tip:
            button.setToolTip(tip);button.setStatusTip(tip);button.setAccessibleName(tip);button.setToolTipDuration(12000);button.setMouseTracking(True)

class HoverDescriptions(QObject):
    def eventFilter(self,obj,event):
        if event.type()==QEvent.Type.Show and isinstance(obj,QWidget) and obj.isWindow():describe(obj)
        if event.type()==QEvent.Type.ToolTip and isinstance(obj,QAbstractButton) and obj.toolTip():
            QToolTip.showText(event.globalPos(),obj.toolTip(),obj);event.accept();return True
        return False

def install_tooltips(window):
    app=QApplication.instance()
    if not hasattr(app,'_phdexlab_hover'):
        app._phdexlab_hover=HoverDescriptions(app);app.installEventFilter(app._phdexlab_hover)
    describe(window)
