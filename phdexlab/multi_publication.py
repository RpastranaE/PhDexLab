"""Scientific figures use saved Excel caches only, separated by assay ID."""
from pathlib import Path
from .paths import Layout
from .multi_excel import sheet_name
from .excel import values
from .assay_engine import engine
from .publication import finite
from .graph_styles import for_experiment,role_style,sample_color
from .protocols import digest
from .export_cache import store,restore
import json,re

BLUE='#0072B2';ORANGE='#D55E00'

def print_text(text):
    """Render unit exponents with bundled math glyphs even for Windows fonts."""
    table=str.maketrans('⁻⁰¹²³⁴⁵⁶⁷⁸⁹','-0123456789')
    return re.sub('[⁻⁰¹²³⁴⁵⁶⁷⁸⁹]+',lambda m:'$^{'+m.group().translate(table)+'}$',text)

def labels(p):
    unit=p['result_unit'].replace('umol','µmol').replace('/100 g',' 100 g⁻¹').replace('/g',' g⁻¹').replace('/mL',' mL⁻¹')
    if engine(p)=='ec50':return 'Dose (mg extract mL⁻¹, final mixture)','Inhibition at plateau (%)','EC50 (mg extract mL⁻¹, final mixture)'
    if engine(p)=='gravimetric':return 'Sample','',{'moisture':'Moisture (%)','dry_matter':'Dry matter (%)','ash':'Ash (%; '+p.get('ash_basis','initial')+' mass basis)'}[p['quantity']]
    if engine(p)=='sieve':return 'Sample / sieve fraction','','Retained mass (% of loaded mass)'
    basis='before reaction' if p['calibration_basis']=='before' else 'final reaction mixture'
    x=p['equivalent']+' concentration ('+p['concentration_unit'].replace('umol','µmol').replace('/L',' L⁻¹')+'; '+basis+')'
    y='Inhibition (%)' if engine(p)=='inhibition' else ('Blank-corrected ΔA' if p['response']=='delta' else 'Blank-corrected A')+f" at {p['wavelength_nm']:g} nm (AU)"
    return x,y,p['method']+' ('+unit+')'

def payload(folder,assay):
    l=Layout(folder);p=assay['protocol'];result=dict(protocol=p,summary=values(l.master,sheet_name(assay,'Summary'))[1:],results=values(l.master,sheet_name(assay,'Results'))[1:])
    if engine(p) in ('colorimetric','inhibition'):
        c=values(l.master,sheet_name(assay,'Calibration'));result.update(calibration=sorted([r for r in c[1:] if finite(r[0])],key=lambda r:r[0]),slope=c[2][9],intercept=c[3][9],r2=c[4][9])
    if engine(p)=='ec50':result['curve']=values(l.master,sheet_name(assay,'DoseCurve'))[1:]
    return result

def captions(data):
    p=data['protocol'];return (f"{p['method']}. Source: {p['source']}. Protocol: {p['name']}.\n"
        'Results: biological-unit means after averaging technical measurements. Error bars are biological SD; dots are individual biological units. '
        'No significance test or automatic exclusion. Missing estimates remain explicit; SD is not invented for n<2. '
        'Calibration (where used): technical means ± SD and unweighted OLS with free intercept, computed in Excel. '
        'DPPH EC50 (where used): technical plateau means by dose followed by local linear interpolation around 50%; no extrapolation. '
        'Plateau confirmation is supplied by the operator. A lower EC50 indicates a stronger response under identical conditions. '
        'Sieve percentages use original loaded mass; no renormalisation to 100%. '
        f"Mass basis: {p.get('mass_basis','')}. Protocol status: {p.get('status','DRAFT')}. Transfer to this matrix is not experimentally validated. "
        'All demonstration data are synthetic. Check workbook QC before interpretation.\n')

def export(folder,assays,states,force=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import scienceplots
    plt.style.use(['science','no-latex']);plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'svg.fonttype':'none','pdf.fonttype':42,'axes.linewidth':.8,'xtick.top':False,'ytick.right':False,'axes.spines.top':False,'axes.spines.right':False,'xtick.minor.visible':False,'ytick.minor.visible':False})
    l=Layout(folder);style=for_experiment(folder);report={'exports':[],'errors':[],'presentation':style}
    status=l.meta/'publication_status.json';previous=json.loads(status.read_text(encoding='utf-8')) if status.exists() else {};report.update(assays={},reused_assays=[])
    from cycler import cycler
    plt.rcParams['axes.prop_cycle']=cycler(color=style['colors'])
    calstyle=role_style(style,'calibration');resstyle=role_style(style,'results');dose=role_style(style,'dose');typography=style['typography']
    plt.rcParams.update({'font.family':typography['font'],'font.size':typography['tick_size'],'axes.labelsize':typography['label_size'],'xtick.labelsize':typography['tick_size'],'ytick.labelsize':typography['tick_size']})
    blue,orange=calstyle['colors'][:2];marker=calstyle['marker'];face='white' if calstyle['open'] else blue
    for assay in assays:
        if states[assay['id']]['state'] not in ('calculated','needs_review'):continue
        data=payload(folder,assay);p=assay['protocol'];dest=l.figures/assay['id']/'Publication';dest.mkdir(parents=True,exist_ok=True);xlab,ylab,reslab=labels(p)
        signature=digest(dict(data=data,style=style));old=previous.get('assays',{}).get(assay['id'],{});start=len(report['exports'])
        if not force and old.get('signature')==signature and restore(folder,old.get('files',{})):
            report['assays'][assay['id']]=old;report['exports'].extend(name for name in old['files'] if not name.endswith('.txt'));report['reused_assays'].append(assay['id']);continue
        def save(fig,suffix):
            for ext in ('svg','pdf','png'):
                path=dest/(l.stem+'_'+assay['id']+'_'+suffix+'.'+ext);fig.savefig(path,dpi=600,transparent=True,bbox_inches='tight',pad_inches=.04);report['exports'].append(str(path.relative_to(l.root)))
            plt.close(fig)
        if 'calibration' in data:
            fig,ax=plt.subplots(figsize=(3.9,2.9));cal=data['calibration'];x=[r[0] for r in cal]
            ax.errorbar(x,[r[1] for r in cal],yerr=[r[3] if finite(r[3]) else float('nan') for r in cal],fmt=marker,color=blue,mfc=face,ecolor=calstyle['error'],capsize=2,ms=calstyle['size'],label='Calibration means ± SD')
            ax.plot(x,[r[4] for r in cal],color=orange,ls=calstyle['line'],lw=calstyle['width'],label='OLS fit');ax.set_xlabel(print_text(xlab.replace('; ',';\n')));ax.set_ylabel(print_text(ylab))
            ax.text(.04,.96,f"y = {data['slope']:.4g}x {data['intercept']:+.4g}\nR² = {data['r2']:.4f}",transform=ax.transAxes,va='top',fontsize=7);ax.legend(loc='lower right',frameon=False);ax.margins(x=.08,y=.15);save(fig,'calibration')
        if 'curve' in data:
            fig,ax=plt.subplots(figsize=(6.8,3.8));fig.subplots_adjust(right=.68);keys=sorted({tuple(r[:2]) for r in data['curve']})
            for curve_index,key in enumerate(keys):
                levels=[r for r in data['curve'] if tuple(r[:2])==key]
                ax.errorbar([r[2] for r in levels],[r[3] for r in levels],yerr=[r[4] if finite(r[4]) else float('nan') for r in levels],fmt=dose['marker'],ls=dose['line'],ms=dose['size'],lw=dose['width'],color=dose['colors'][curve_index%len(dose['colors'])],mfc='white' if dose['open'] else dose['colors'][curve_index%len(dose['colors'])],ecolor=dose['error'],capsize=2,label=' / '.join(map(str,key)))
            ax.axhline(50,color='#777777',ls='--',lw=.7);ax.set_xlabel(print_text(xlab));ax.set_ylabel(print_text(ylab));ax.legend(frameon=False,fontsize=max(7,typography['tick_size']-1),loc='upper left',bbox_to_anchor=(1.02,1));save(fig,'dose_response')
        summary=[r for r in data['summary'] if r[0] is not None];width=max(3.9,min(12,len(summary)*.7+1.8));fig,ax=plt.subplots(figsize=(width,3.1))
        for i,r in enumerate(summary,1):
            if not finite(r[2]):continue
            color=sample_color(style,i-1)
            ax.bar(i,r[2],width=.55,color=color if resstyle['per_sample'] else resstyle['fill'],edgecolor=color,lw=.8)
            if finite(r[3]):ax.errorbar(i,r[2],yerr=r[3],fmt='none',ecolor=resstyle['error'],capsize=3,lw=1,zorder=3)
            pts=[t[4] for t in data['results'] if t[0]=='sample' and t[1]==r[0] and finite(t[4])]
            offsets=[0] if len(pts)==1 else [-.13+.26*j/(len(pts)-1) for j in range(len(pts))]
            ax.scatter([i+v for v in offsets],pts,s=resstyle['size']**2,marker=resstyle['marker'],facecolors='white' if resstyle['open'] else color,edgecolors=color if resstyle['open'] else 'white',linewidths=.6,zorder=4)
        ax.set_xticks(range(1,len(summary)+1),[str(r[0])+'\n'+f'n = {int(r[1])}' for r in summary]);ax.set_ylabel(print_text(reslab));ax.set_xlabel('Sample / sieve fraction' if engine(p)=='sieve' else 'Sample');ax.set_xlim(.45,len(summary)+.55);ax.margins(y=.2)
        if len(summary)>5:plt.setp(ax.get_xticklabels(),rotation=35,ha='right')
        if not any(finite(r[2]) for r in summary):ax.text(.5,.5,'No estimable result — review workbook',ha='center',transform=ax.transAxes,fontsize=8)
        save(fig,'results');(dest/(l.stem+'_'+assay['id']+'_captions.txt')).write_text(captions(data),encoding='utf-8')
        report['assays'][assay['id']]=dict(signature=signature,files=store(folder,report['exports'][start:]+[str((dest/(l.stem+'_'+assay['id']+'_captions.txt')).relative_to(l.root))]))
    status.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    return report
