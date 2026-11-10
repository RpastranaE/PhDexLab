"""Compact reading counters and a separate, explicit readiness indicator."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QLabel,QHBoxLayout
from .i18n import t


class EntrySummary(QWidget):
    def __init__(self):
        super().__init__();self.setObjectName('entrySummary');self.counts={};self.sample_count=0
        layout=QHBoxLayout(self);layout.setContentsMargins(10,5,10,5);layout.setSpacing(12)
        self.setFixedHeight(40)
        self.assay=QLabel();self.assay.setObjectName('summaryAssay');self.assay.setProperty('userData',True);layout.addWidget(self.assay)
        self.values={};self.captions={}
        for col,key in enumerate(('total','blank','standard','control','samples','sample')):
            box=QHBoxLayout();box.setSpacing(4)
            value=QLabel('0');value.setObjectName('summaryValue');value.setProperty('userData',True)
            caption=QLabel();caption.setObjectName('summaryCaption')
            box.addWidget(value);box.addWidget(caption);layout.addLayout(box)
            self.values[key]=value;self.captions[key]=caption
        layout.addStretch()
        self.status=QLabel();self.status.setObjectName('summaryStatus');layout.addWidget(self.status)
        self.set_status('',False,'');self.set_counts({},0);self.apply_theme(False)

    def set_counts(self,counts,samples):
        self.counts=dict(counts);self.sample_count=samples
        numbers=dict(counts,total=sum(counts.values()),samples=samples)
        labels={'total':'Lecturas','blank':'Blancos','standard':'Patrones','control':'Controles','samples':'Muestras','sample':'Lecturas de muestras'}
        for key,value in self.values.items():value.setText(str(numbers.get(key,0)));self.captions[key].setText(t(labels[key]))

    def set_status(self,assay,ready,issue):
        self.assay.setText(assay);self.assay.setVisible(bool(assay))
        self.status.setProperty('ready',bool(ready));self.status.setVisible(bool(assay))
        self.status.setText(t('Listo para calcular' if ready else 'Revisar entradas'))
        self.status.setToolTip(t(issue) if issue else t('Entradas completas. Guardar y actualizar para calcular.'))
        self.status.style().unpolish(self.status);self.status.style().polish(self.status)

    def text(self):
        # Diagnostic/accessibility compatibility; no punctuation-heavy strip is rendered.
        return f"{self.sample_count} muestras distintas; "+self.status.text()

    def clear(self):
        self.set_counts({},0);self.set_status('',False,'');self.setToolTip('')

    def apply_theme(self,dark):
        bg,fg,muted,border,success,success_text=('#1D3039','#DBF0F2','#ACC5CB','#36515C','#1D5540','#D8FBE5') if dark else ('#F0F7F8','#155D68','#52717A','#D9E8EB','#DDF3E5','#165A35')
        self.setStyleSheet(f'''QWidget#entrySummary{{background:{bg};border:1px solid {border};border-radius:8px}}
QLabel{{background:transparent;border:0;padding:0;color:{fg}}}
QLabel#summaryValue{{font-size:13px;font-weight:700}}
QLabel#summaryCaption{{font-size:11px;color:{muted}}}
QLabel#summaryAssay{{font-size:11px;font-weight:600}}
QLabel#summaryStatus{{padding:4px 8px;border-radius:5px;background:{border};font-size:11px;font-weight:600}}
QLabel#summaryStatus[ready="true"]{{background:{success};color:{success_text};font-weight:700}}''')
