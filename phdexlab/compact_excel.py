"""Logical calculation tables packed into two visible sheets per assay.

The chemistry engine still generates one set of formulas. This adapter relocates
cells/references, never computes values or mirrors hidden calculation sheets.
"""
import copy,re,math
from openpyxl.formula.tokenizer import Tokenizer
from openpyxl.utils.cell import get_column_letter,column_index_from_string,coordinate_to_tuple,range_boundaries
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
from openpyxl.worksheet.cell_range import MultiCellRange


def mappings(wb):
    if hasattr(wb,'_compact_layout_cache'):return wb._compact_layout_cache
    if '_PhDexLab' not in getattr(wb,'sheetnames',[]):return {}
    meta=wb['_PhDexLab']
    if meta.cell(1,4).value!='compact_layout':return {}
    result={r[0]:dict(sheet=r[1],row=r[2],col=r[3],rows=r[4],cols=r[5]) for r in meta.iter_rows(min_row=3,min_col=4,max_col=9,values_only=True) if r[0]}
    for logical,entry in result.items():
        defined=wb.defined_names.get('phdex_'+logical)
        if defined is not None:
            places=list(defined.destinations)
            if len(places)!=1:raise ValueError('Managed Excel block must be contiguous: '+logical)
            sheet,address=places[0];left,top,right,bottom=range_boundaries(address)
            entry.update(sheet=sheet,row=top,col=left,rows=bottom-top+1,cols=right-left+1)
    wb._compact_layout_cache=result;return result


def cells(wb,logical):
    entry=mappings(wb).get(logical)
    if not entry:return list(wb[logical].iter_rows())
    ws=wb[entry['sheet']];bottom=entry['row']+entry['rows']-1
    if logical.endswith('_RAW'):bottom=max(bottom,ws.max_row)
    rows=list(ws.iter_rows(min_row=entry['row'],max_row=bottom,min_col=entry['col'],max_col=entry['col']+entry['cols']-1))
    if logical.endswith('_RAW'):
        while len(rows)>1 and not any(c.value not in ('',None) for c in rows[-1]):rows.pop()
    return rows


def table_values(wb,logical):
    if logical not in mappings(wb):return list(wb[logical].values)
    return [tuple(c.value for c in row) for row in cells(wb,logical)]


def cached_tables(wb):
    result={ws.title:list(ws.values) for ws in wb}
    for logical,entry in mappings(wb).items():
        rows=result[entry['sheet']];start=entry['row']-1;left=entry['col']-1
        stop=len(rows) if logical.endswith('_RAW') else start+entry['rows']
        table=[tuple(row[left:left+entry['cols']]) for row in rows[start:stop]]
        if logical.endswith('_RAW'):
            while len(table)>1 and not any(v not in ('',None) for v in table[-1]):table.pop()
        result[logical]=table
    return result


def shift_address(address,row,col):
    def shift(match):
        ac,letters,ar,digits=match.groups()
        return ac+get_column_letter(column_index_from_string(letters)+col)+ar+str(int(digits)+row)
    if not re.fullmatch(r'\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?',address):raise ValueError('Unsupported managed formula reference: '+address)
    return re.sub(r'(\$?)([A-Z]{1,3})(\$?)(\d+)',shift,address)


def rewrite(formula,layout,origin=None):
    tokens=Tokenizer(formula).items
    for token in tokens:
        if token.type!='OPERAND' or token.subtype!='RANGE':continue
        if '!' in token.value:
            sheet,address=token.value.rsplit('!',1);sheet=sheet.strip("'").replace("''", "'")
        else:sheet,address=origin,token.value
        if sheet not in layout:continue
        place=layout[sheet];target=place['sheet'].replace("'","''")
        token.value="'"+target+"'!"+shift_address(address,place['row']-1,place['col']-1)
    return '='+''.join(token.value for token in tokens)


def chart_refs(obj,layout,origin):
    from openpyxl.descriptors.serialisable import Serialisable
    if not isinstance(obj,Serialisable):return
    # Bar Series chooses its XML elements only during serialisation.
    for key in (obj.__elements__ or tuple(vars(obj))):
        value=getattr(obj,key,None)
        if key=='f' and isinstance(value,str):setattr(obj,key,rewrite('='+value,layout,origin)[1:])
        elif isinstance(value,(tuple,list)):
            for child in value:chart_refs(child,layout,origin)
        else:chart_refs(value,layout,origin)


def compact(wb,assays,style):
    source={ws.title:ws for ws in wb if ws.title!='_PhDexLab'};layout={};targets={}
    def place(logical,physical,row,col=1):
        ws=source[logical];layout[logical]=dict(sheet=physical,row=row,col=col,rows=ws.max_row,cols=ws.max_column)
        targets.setdefault(physical,wb.create_sheet(physical) if physical not in wb else wb[physical])
    cursor=4
    for name in ('Index','ExperimentSummary','Samples'):
        place(name,'Overview',cursor);cursor+=source[name].max_row+5
    for assay in assays:
        aid=assay['id'];data=aid+'_Data';analysis=aid+'_Analysis';raw=source[aid+'_RAW']
        place(aid+'_RAW',data,4);place(aid+'_Parameters',data,4,raw.max_column+3)
        place(aid+'_ReadMe',data,source[aid+'_Parameters'].max_row+9,raw.max_column+3)
        cursor=4
        for role in ('Summary','Results','Calibration','DoseCurve','MassBalance','Processing'):
            logical=aid+'_'+role
            if logical not in source:continue
            place(logical,analysis,cursor);ws=source[logical]
            chart_end=max((coordinate_to_tuple(chart.anchor)[0]+math.ceil(chart.height/2.54*72/style['row_height'])+5 for chart in ws._charts),default=0)
            cursor+=max(ws.max_row+5,chart_end)
    labels={'Index':'Assays','ExperimentSummary':'All results','Samples':'Samples','RAW':'Raw readings','Parameters':'Conditions','ReadMe':'Method and notes','Summary':'Final results','Results':'Results by unit','Calibration':'Calibration','DoseCurve':'Dose response','MassBalance':'Mass balance','Processing':'Calculations'}
    for logical,entry in layout.items():
        old=source[logical];new=targets[entry['sheet']];dr,dc=entry['row']-1,entry['col']-1
        for row in old:
            for cell in row:
                if cell.value is None:continue
                dest=new.cell(cell.row+dr,cell.column+dc, rewrite(cell.value,layout,logical) if cell.data_type=='f' else cell.value)
                if cell.data_type=='s':dest.data_type='s'
                dest._style=copy.copy(cell._style);dest.alignment=copy.copy(cell.alignment)
                if cell.comment:dest.comment=copy.copy(cell.comment)
                if cell.hyperlink:
                    link=copy.copy(cell.hyperlink);link.ref=dest.coordinate
                    if link.target and link.target.startswith('#'):
                        link.target='#'+rewrite('='+link.target[1:],layout,logical)[1:]
                    dest._hyperlink=link
        for number,dimension in old.row_dimensions.items():new.row_dimensions[number+dr].height=dimension.height
        for key,dimension in old.column_dimensions.items():
            target=get_column_letter(column_index_from_string(key)+dc);new.column_dimensions[target].width=max(new.column_dimensions[target].width or 0,dimension.width or 0)
        for validation in old.data_validations.dataValidation:
            moved=copy.deepcopy(validation);moved.sqref=MultiCellRange(' '.join(shift_address(str(area),dr,dc) for area in validation.sqref.ranges));new.add_data_validation(moved)
        for chart in old._charts:
            moved=copy.deepcopy(chart);chart_refs(moved,layout,logical)
            moved.x_axis.majorGridlines=None;moved.y_axis.majorGridlines=None
            moved.x_axis.delete=False;moved.y_axis.delete=False
            moved.x_axis.tickLblPos='nextTo';moved.y_axis.tickLblPos='nextTo'
            moved.x_axis.majorTickMark='out';moved.y_axis.majorTickMark='out'
            for index,series in enumerate(moved.series):
                if moved.__class__.__name__=='BarChart':series.graphicalProperties.solidFill=style['accent'][1:]
                else:
                    if index==0 and series.marker:
                        series.marker.graphicalProperties.solidFill=style['accent'][1:];series.marker.graphicalProperties.line.solidFill=style['accent'][1:]
                    if index>0:series.graphicalProperties.line.solidFill=style['header'][1:]
            if not isinstance(chart.anchor,str):raise ValueError('Unsupported chart anchor')
            new.add_chart(moved,shift_address(chart.anchor,dr,dc))
        role=logical.rsplit('_',1)[-1] if logical not in ('Index','ExperimentSummary','Samples') else logical
        heading=new.cell(entry['row']-1,entry['col'],labels[role]);heading.font=Font(name=style['font'],size=style['section_size'],bold=True,color=style['accent'][1:])
        nav=new.cell(1,len([c for c in new[1] if c.value])+1,labels[role]);nav.hyperlink=f"#'{new.title}'!{get_column_letter(entry['col'])}{entry['row']-1}";nav.style='Hyperlink'
        new.sheet_properties.tabColor=style['accent'][1:];new.freeze_panes='A5';new.sheet_view.showGridLines=style['gridlines']
        new.sheet_properties.pageSetUpPr.fitToPage=True;new.page_setup.orientation='landscape';new.page_setup.paperSize=new.PAPERSIZE_A3;new.page_setup.fitToWidth=1;new.page_setup.fitToHeight=0
        for row in range(entry['row'],entry['row']+entry['rows']):
            new.row_dimensions[row].height=style['row_height'] if row!=entry['row'] else style['header_height']
            for col in range(entry['col'],entry['col']+entry['cols']):
                cell=new.cell(row,col);header=row==entry['row'];editable=role=='RAW' or role=='Parameters' and col==entry['col']+1
                cell.font=Font(name=style['font'],size=style['header_size'] if header else style['font_size'],bold=header,color=style['header_text'][1:] if header else style['input_text'][1:] if editable else style['text'][1:])
                cell.fill=PatternFill('solid',fgColor=style['header'][1:] if header else style['input'][1:] if editable else style['stripe'][1:] if style['striped'] and (row-entry['row'])%2 else style['background'][1:])
                if cell.value is not None:cell.alignment=Alignment(wrap_text=True,vertical='center' if header else 'top',horizontal=style['alignment'])
                edge=Side(style='thin',color=style['border_color'][1:])
                cell.border=Border(bottom=edge) if style['border']=='horizontal' else Border(left=edge,right=edge,top=edge,bottom=edge) if style['border']=='all' else Border()
        if role=='RAW':new.column_dimensions[get_column_letter(entry['col'])].hidden=True
        if role=='RAW':new.auto_filter.ref=f"{get_column_letter(entry['col'])}{entry['row']}:{get_column_letter(entry['col']+entry['cols']-1)}{entry['row']+entry['rows']-1}"
    for ws in targets.values():
        assay=next((a for a in assays if ws.title in (a['id']+'_Data',a['id']+'_Analysis')),None)
        title=ws.cell(2,1,assay['label'] if assay else 'Experiment overview');title.font=Font(name=style['font'],size=style['title_size'],bold=True,color=style['accent'][1:]);ws.row_dimensions[2].height=max(28,style['title_size']*1.6)
        for dimension in ws.column_dimensions.values():
            if dimension.width:dimension.width*=style['column_scale']/100
        for row in range(2,ws.max_row+1):
            if ws.row_dimensions[row].height is None:ws.row_dimensions[row].height=style['row_height']
    for ws in source.values():wb.remove(ws)
    meta=wb['_PhDexLab'];meta.cell(1,2,4);meta.cell(1,4,'compact_layout');meta.cell(1,5,1)
    for col,label in enumerate(('Logical table','Worksheet','First row','First column','Rows','Columns'),4):meta.cell(2,col,label)
    for row,(logical,entry) in enumerate(layout.items(),3):
        for col,value in enumerate((logical,entry['sheet'],entry['row'],entry['col'],entry['rows'],entry['cols']),4):meta.cell(row,col,value)
        ref=f"'{entry['sheet']}'!${get_column_letter(entry['col'])}${entry['row']}:${get_column_letter(entry['col']+entry['cols']-1)}${entry['row']+entry['rows']-1}"
        wb.defined_names.add(DefinedName('phdex_'+logical,attr_text=ref))
    wb._sheets=[targets['Overview']]+[targets[a['id']+suffix] for a in assays for suffix in ('_Data','_Analysis')]+[meta]
    wb.active=0
    return layout
