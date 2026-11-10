"""Remove a verified Origin title-rendering artifact, retaining native vector data.

Only a straight overline immediately following an expected axis-title text object
is eligible. Plot groups, fitted lines, axes, error bars and annotations are kept.
"""
import hashlib,math,re
from pathlib import Path
import xml.etree.ElementTree as ET

NUMBER=r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?'
SVG='http://www.w3.org/2000/svg'

def portable_superscripts(root):
    """Render superscripts with ordinary glyphs and explicit SVG positioning.

    This avoids broken superscript-minus fallback in SVG viewers, retaining
    editable vector text, coordinates, rotations and ordinary punctuation.
    """
    from PySide6.QtGui import QGuiApplication,QFont,QFontMetricsF
    global _application
    count=0;alphabet='⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹';translation=str.maketrans(alphabet,'-+0123456789')
    for parent in list(root.iter()):
        for node in list(parent):
            if node.tag!='{'+SVG+'}text':continue
            content=''.join(node.itertext()).strip()
            if not re.search('['+alphabet+']',content):continue
            # Native Origin axis labels contain a single plain tspan. Avoid
            # flattening rich annotations with independently positioned runs.
            if len(node)>1 or len(node)==1 and (len(node[0]) or node[0].tag!='{'+SVG+'}tspan'):continue
            if QGuiApplication.instance() is None:_application=QGuiApplication([])
            attrs=dict(node.attrib);leaf=node[0] if len(node) else node
            try:size=float(attrs['font-size']);x=float(re.findall(NUMBER,leaf.get('x',node.get('x','0')))[0]);y=float(re.findall(NUMBER,leaf.get('y',node.get('y','0')))[0])
            except (ValueError,KeyError,IndexError):continue
            font=QFont(attrs.get('font-family','Arial').split(',')[0].strip("'\""));font.setPixelSize(round(size));font.setBold(int(attrs.get('font-weight','400'))>=600)
            parts=re.split('(['+alphabet+']+)',content);position=list(parent).index(node);parent.remove(node)
            for index,part in enumerate(parts):
                if not part:continue
                superscript=index%2;run=part.translate(translation) if superscript else part
                run_font=QFont(font);run_font.setPixelSize(round(size*.7) if superscript else round(size))
                attributes=dict(attrs,x=str(x),y=str(y-size*.4 if superscript else y))
                attributes['font-size']=str(run_font.pixelSize());attributes['{http://www.w3.org/XML/1998/namespace}space']='preserve'
                attributes['style']='white-space:pre'
                segment=ET.Element('{'+SVG+'}text',attributes);segment.text=run;parent.insert(position,segment);position+=1
                x+=QFontMetricsF(run_font).horizontalAdvance(run)
                if superscript:count+=1
    return count


def cleaned_svg(raw,titles):
    root=ET.fromstring(raw);expected={' '.join(title.split()) for title in titles};removed=0
    # Origin 2024 exports axis titles directly under the SVG root. Never touch
    # text/lines inside plot, clipping or annotation groups.
    for parent in (root,):
        children=list(parent)
        for index,text in enumerate(children[:-1]):
            if text.tag!='{'+SVG+'}text' or ' '.join(''.join(text.itertext()).split()) not in expected:continue
            line=children[index+1]
            if line.tag!='{'+SVG+'}path':continue
            match=re.fullmatch(r'\s*M\s*('+NUMBER+r')[,\s]+('+NUMBER+r')\s*L\s*('+NUMBER+r')[,\s]+('+NUMBER+r')\s*',line.get('d',''))
            if not match:continue
            matrix=[1,0,0,1,0,0];transform=text.get('transform','')
            if transform:
                if not re.fullmatch(r'\s*matrix\([^()]+\)\s*',transform):continue
                matrix=[float(value) for value in re.findall(NUMBER,transform)]
                if len(matrix)!=6:continue
            a,b,c,d,e,f=matrix
            try:x=float(text.get('x','0'));y=float(text.get('y','0'));size=float(text.attrib['font-size'])
            except (ValueError,KeyError):continue
            scale=math.hypot(a,b)
            if scale==0 or size<=0:continue
            ux,uy=a/scale,b/scale;size*=scale;bx=a*x+c*y+e;by=b*x+d*y+f
            x1,y1,x2,y2=map(float,match.groups());dx,dy=x1-bx,y1-by
            along=dx*ux+dy*uy;above=-dx*uy+dy*ux
            length=(x2-x1)*ux+(y2-y1)*uy;cross=-(x2-x1)*uy+(y2-y1)*ux
            if abs(along)<=size*.2 and -size*1.3<=above<=-size*.4 and length>=size*.5 and abs(cross)<=size*.03:
                parent.remove(line);removed+=1
    normalized=portable_superscripts(root)
    if not removed and not normalized:return raw,0
    ET.register_namespace('',SVG);ET.register_namespace('xlink','http://www.w3.org/1999/xlink');ET.register_namespace('olab','http://www.originlab.com/namespaces/olab')
    return ET.tostring(root,encoding='utf-8',xml_declaration=True),removed

_application=None
def render_svg(svg_path,png_path,pdf_path,width=2600):
    from PySide6.QtCore import QByteArray,QRectF,QSizeF,QMarginsF
    from PySide6.QtGui import QGuiApplication,QImage,QPainter,QPdfWriter,QPageSize
    from PySide6.QtSvg import QSvgRenderer
    global _application
    if QGuiApplication.instance() is None:_application=QGuiApplication([])
    raw=Path(svg_path).read_bytes();renderer=QSvgRenderer(QByteArray(raw))
    if not renderer.isValid():raise RuntimeError('Origin SVG could not be rendered')
    box=renderer.viewBoxF();height=round(width*box.height()/box.width())
    image=QImage(width,height,QImage.Format.Format_RGB32);image.fill(0xFFFFFFFF)
    painter=QPainter(image);painter.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.TextAntialiasing)
    renderer.render(painter,QRectF(0,0,width,height));painter.end()
    png_path=Path(png_path);pdf_path=Path(pdf_path);png_path.parent.mkdir(parents=True,exist_ok=True);pdf_path.parent.mkdir(parents=True,exist_ok=True)
    if not image.save(str(png_path),'PNG'):raise OSError('Could not write Origin PNG')
    root=ET.fromstring(raw)
    def millimetres(value,fallback):
        match=re.fullmatch(r'('+NUMBER+r')(in|mm|cm|pt|px)?',value or '')
        if not match:return fallback/300*25.4
        factor={'in':25.4,'mm':1,'cm':10,'pt':25.4/72,'px':25.4/96,None:25.4/96}[match[2]]
        return float(match[1])*factor
    pdf=QPdfWriter(str(pdf_path));pdf.setResolution(300)
    pdf.setPageSize(QPageSize(QSizeF(millimetres(root.get('width'),box.width()),millimetres(root.get('height'),box.height())),QPageSize.Unit.Millimeter))
    pdf.setPageMargins(QMarginsF(0,0,0,0));painter=QPainter(pdf)
    if not painter.isActive():raise OSError('Could not write Origin PDF')
    renderer.render(painter,QRectF(pdf.pageLayout().paintRectPixels(300)));painter.end()

def repair_exports(svg_path,titles,layout,assay_id,stem):
    path=Path(svg_path);raw=path.read_bytes();cleaned,count=cleaned_svg(raw,titles)
    if cleaned==raw:return None
    sha=hashlib.sha256(raw).hexdigest();source=layout.meta/'origin_svg_sources'/(sha+'.svg');source.parent.mkdir(parents=True,exist_ok=True)
    if not source.exists():source.write_bytes(raw)
    path.write_bytes(cleaned)
    base=layout.figures/assay_id/'Origin';name=layout.stem+'_'+assay_id+'_'+stem
    png=base/'PNG'/(name+'.png');pdf=base/'PDF'/(name+'.pdf');render_svg(path,png,pdf)
    return dict(removed_title_overlines=count,original_sha256=sha,original_svg=str(source.relative_to(layout.root)),rendered=[str(png.relative_to(layout.root)),str(pdf.relative_to(layout.root))])
