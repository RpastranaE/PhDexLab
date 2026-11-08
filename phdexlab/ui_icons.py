"""Bundled Lucide SVGs with a shared application color; see assets/toolbar/LICENSE-Lucide.txt."""
from pathlib import Path
from functools import lru_cache
from PySide6.QtCore import QByteArray,Qt
from PySide6.QtGui import QIcon,QPixmap,QPainter
from PySide6.QtSvg import QSvgRenderer

COLOR='#176E78'
@lru_cache(maxsize=96)
def svg(name,color='#176E78'):
    return (Path(__file__).parent/'assets'/'toolbar'/(name+'.svg')).read_text(encoding='utf-8').replace('currentColor',color)

def icon(name):
    result=QIcon();renderer=QSvgRenderer(QByteArray(svg(name,COLOR).encode()))
    if not renderer.isValid():raise ValueError('Icono SVG no válido: '+name)
    for size in (24,48,72):
        pixmap=QPixmap(size,size);pixmap.fill(Qt.GlobalColor.transparent)
        painter=QPainter(pixmap);renderer.render(painter);painter.end();result.addPixmap(pixmap)
    return result
