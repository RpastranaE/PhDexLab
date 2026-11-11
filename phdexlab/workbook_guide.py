"""Visible calculation navigation and concise, contextual formula annotations."""
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter
from .assay_engine import engine


def add_guides(targets,layout,assays,style):
    for assay in assays:
        aid=assay['id'];ws=targets[aid+'_Analysis'];e=engine(assay['protocol'])
        for col,width in enumerate((32,18,22,24,28,22,16,18,24,20,18,20,22),1):ws.column_dimensions[get_column_letter(col)].width=width
        ws['A4']='Calculation route';ws['A4'].font=Font(name=style['font'],size=12,bold=True,color=style['accent'][1:])
        roles=[r for r in ('Calibration','DoseCurve','MassBalance','Processing','Results','Summary') if aid+'_'+r in layout]
        details={
            'Calibration':('Calibration','Blank/control → corrected standards → fitted curve. Slope, intercept and QC are beside the standards.'),
            'DoseCurve':('Dose response','Matched controls → inhibition at each dose → local EC50 bracket.'),
            'MassBalance':('Mass balance','Loaded and recovered masses → recovery and losses.'),
            'Processing':('Individual readings','Follow each sample/unit/repeat. Select a formula to inspect its inputs; hover over a column heading for the calculation step.'),
            'Results':('Experimental units','Technical readings are combined within each independent preparation.'),
            'Summary':('Final sample results','Independent preparations → sample mean and between-unit SD. Samples remain separate.')}
        for row,role in enumerate(roles,5):
            place=layout[aid+'_'+role];label,explanation=details[role]
            cell=ws.cell(row,1,label);cell.hyperlink=f"#'{ws.title}'!A{place['row']-1}";cell.style='Hyperlink'
            ws.merge_cells(start_row=row,start_column=2,end_row=row,end_column=7)
            cell=ws.cell(row,2,explanation);cell.alignment=Alignment(wrap_text=True,vertical='center');cell.font=Font(name=style['font'],size=10,color=style['text'][1:]);ws.row_dimensions[row].height=30
        steps={2:'Measured signal from the original reading(s).',3:'Blank/background-corrected response or inhibition, according to the selected protocol.',
            4:'Equivalent concentration from the calibration, or the method-specific intermediate.',
            5:'Final result for this reading, with the recorded normalization. Control rows use recovery (%).',
            7:'Reaction-volume correction; distinct from prior sample dilution.',8:'Prior sample dilution factor.',
            9:'Original extract concentration after dilution corrections.',10:'Total extract volume converted to litres.',
            11:'Reference sample mass in grams.',12:'Reporting/unit conversion factor.',13:'Equivalent amount in the complete extract.'}
        for role in roles:
            block=layout[aid+'_'+role];sheet=targets[block['sheet']]
            if role=='Processing' and e in ('colorimetric','inhibition'):
                for col in range(2,6):sheet.cell(block['row'],col,str(col-1)+'. '+str(sheet.cell(block['row'],col).value))
            # One explanation per column, not per formula: large imports must
            # not create hundreds of thousands of duplicate Excel note objects.
            for col in range(block['col'],block['col']+block['cols']):
                header=sheet.cell(block['row'],col);label=header.value or role
                detail=steps.get(col,'') if role=='Processing' and e in ('colorimetric','inhibition') else ''
                note=str(label)+'. '+detail+' Same-sheet references use cell addresses; references to other sheets retain the sheet name.'
                header.comment=Comment(note,'PhDexLab')
                first=sheet.cell(block['row']+1,col)
                if first.data_type=='f':first.comment=Comment(note,'PhDexLab')
            if role in ('Summary','Processing'):
                col=3 if role=='Summary' else 5
                emphasis=Font(name=style['font'],size=style['font_size'],bold=True,color=style['accent'][1:])
                for row in range(block['row']+1,block['row']+block['rows']):
                    cell=sheet.cell(row,col)
                    if cell.value is not None:cell.font=emphasis
            # A compact header and normal-width body make the route usable without panes.
            sheet.row_dimensions[block['row']-1].height=max(22,style['section_size']*1.5)
        # Navigation stays at the beginning and never freezes a section of results.
        for target in (targets[aid+'_Data'],ws):
            target.row_dimensions[1].height=28
            for cell in target[1]:
                if cell.value:cell.alignment=Alignment(wrap_text=True,vertical='center')
