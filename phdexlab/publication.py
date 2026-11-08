"""Publication graphics from Excel caches only. No analytical recalculation."""
import math
from .excel import values,read_inputs
from .paths import Layout
from .ui_fields import axis_labels

BLUE='#0072B2';ORANGE='#D55E00'

def payload(folder):
    layout=Layout(folder);_,p=read_inputs(layout.master)
    calibration=values(layout.master,'Calibration')
    cal=sorted([r for r in calibration[1:] if isinstance(r[0],(int,float))],key=lambda r:r[0])
    summary=[r for r in values(layout.master,'Summary')[1:] if r[0] is not None]
    results=[r for r in values(layout.master,'Results')[1:] if r[0]=='sample']
    return dict(protocol=p,calibration=cal,summary=summary,results=results,slope=calibration[2][9],intercept=calibration[3][9],r2=calibration[4][9])

def finite(value):return isinstance(value,(int,float)) and math.isfinite(value)

def captions(data):
    n=', '.join(f'{row[0]}: n={int(row[1])}' for row in data['summary'])
    return (
      'FRAP calibration. Points represent calibration-level means; error bars indicate technical standard deviation (SD), where n ≥ 2. '
      'The line is the ordinary least-squares fit with a free intercept, calculated in Excel with equal weight per level. '
      'Regression statistics and predictions are imported from the saved workbook. No points were excluded.\n\n'
      'FRAP results. Bars represent means across independent biological units or extractions, as labelled by the operator; error bars indicate biological SD. '
      'Dots represent individual biological-unit means after averaging technical measurements. '
      'No SD is drawn for n < 2. No significance test has been performed. '+n+'.\n\n'
      'Protocol status: DRAFT; method transfer has not been experimentally validated. '
      'The mass basis and QC flags are recorded in the workbook. Flagged values remain visible and are not silently excluded. '
      'Demonstration datasets are synthetic and are not experimental evidence.\n')

def export_publication(folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import scienceplots
    data=payload(folder);layout=Layout(folder);dest=layout.figures/'Publication';dest.mkdir(parents=True,exist_ok=True)
    plt.style.use(['science','no-latex'])
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,
       'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'svg.fonttype':'none',
       'pdf.fonttype':42,'axes.linewidth':0.8,'lines.linewidth':1.0,
       'xtick.direction':'out','ytick.direction':'out','axes.spines.top':False,'axes.spines.right':False,
       'xtick.top':False,'ytick.right':False,'xtick.minor.visible':False,'ytick.minor.visible':False})
    xlab,ylab,resultlab=axis_labels(data['protocol']);exports=[]
    def save(fig,name):
        for ext in ('svg','pdf','png'):
            path=dest/(layout.stem+'_'+name+'.'+ext)
            fig.savefig(path,dpi=600,transparent=True,bbox_inches='tight',pad_inches=0.04)
            exports.append(str(path.relative_to(layout.root)))
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(3.9,2.9))
    cal=data['calibration'];x=[r[0] for r in cal];y=[r[1] for r in cal]
    errors=[r[3] if finite(r[3]) else float('nan') for r in cal]
    ax.errorbar(x,y,yerr=errors,fmt='o',color=BLUE,mfc='white',mec=BLUE,ms=4,capsize=2,elinewidth=0.8,label='Calibration means ± SD')
    ax.plot(x,[r[4] for r in cal],color=ORANGE,lw=1.1,label='OLS fit')
    ax.set_xlabel(xlab.replace('; ',';\n'));ax.set_ylabel(ylab)
    ax.text(0.04,0.96,f"y = {data['slope']:.4g}x {data['intercept']:+.4g}\nR² = {data['r2']:.4f}",transform=ax.transAxes,va='top',fontsize=7)
    ax.legend(loc='lower right',frameon=False);ax.margins(x=0.08,y=0.14)
    ax.ticklabel_format(axis='both',style='plain',useOffset=False);save(fig,'calibration')
    summary=data['summary'];width=max(3.9,min(12,len(summary)*0.65+1.8))
    fig,ax=plt.subplots(figsize=(width,3.0))
    for i,r in enumerate(summary,1):
        mean=r[2];sd=r[3] if finite(r[3]) else None
        ax.bar(i,mean,width=0.55,color='#D7EAF3',edgecolor=BLUE,linewidth=0.8,zorder=1)
        if sd is not None:ax.errorbar(i,mean,yerr=sd,fmt='none',ecolor='#202A30',capsize=3,elinewidth=1,zorder=3)
        points=[t[4] for t in data['results'] if t[1]==r[0]]
        offsets=[0] if len(points)==1 else [(-0.13+0.26*j/(len(points)-1)) for j in range(len(points))]
        ax.scatter([i+off for off in offsets],points,s=17,c=BLUE,edgecolors='white',linewidths=0.4,zorder=4)
    ax.set_xticks(list(range(1,len(summary)+1)),[str(r[0])+'\n'+f'n = {int(r[1])}' for r in summary])
    if len(summary)>5:plt.setp(ax.get_xticklabels(),rotation=35,ha='right')
    ax.set_ylabel(resultlab);ax.set_xlabel('Sample');ax.set_xlim(0.45,len(summary)+0.55)
    ax.axhline(0,color='#7B858B',lw=0.5,zorder=0);ax.margins(y=0.20);save(fig,'frap_results')
    (dest/(layout.stem+'_captions.txt')).write_text(captions(data),encoding='utf-8')
    return {'exports':exports,'source':'Saved Microsoft Excel formula caches','error_bars':'SD; never SEM or confidence intervals'}
