"""Versioned presentation presets, independent of analytical protocol and UI theme."""
import copy,json,re,uuid
from .paths import Layout
from .protocols import digest
from .integration import dump

STYLES={
 'classic':dict(name='Azul científico',en='Scientific blue',colors=['#0072B2','#D55E00','#009E73','#CC79A7'],fill='#D7EAF3',marker='o',symbol=2,open=False,line='-',line_origin=0,font='Arial'),
 'teal':dict(name='Verde petróleo',en='Petroleum teal',colors=['#008579','#CC6677','#4477AA','#AA4499'],fill='#D3ECE7',marker='s',symbol=1,open=False,line='-',line_origin=0,font='Arial'),
 'violet':dict(name='Violeta y ámbar',en='Violet and amber',colors=['#6F4C9B','#C17D11','#1B9E77','#D95F02'],fill='#E5DDF0',marker='D',symbol=5,open=False,line='--',line_origin=1,font='Arial'),
 'mono':dict(name='Monocromo abierto',en='Open monochrome',colors=['#30343B','#737B84','#4B5563','#9CA3AF'],fill='#E5E7EB',marker='^',symbol=3,open=True,line='--',line_origin=1,font='Arial'),
 'warm':dict(name='Terracota',en='Terracotta',colors=['#AF4B32','#286A84','#7B6D26','#72558E'],fill='#F1DBD3',marker='v',symbol=4,open=True,line='-',line_origin=0,font='Arial'),
}
DEFAULT='classic'
MARKERS={'none':0,'o':2,'s':1,'^':3,'v':4,'D':5}
PALETTES={
 'Accessible':['#0072B2','#D55E00','#009E73','#CC79A7','#E69F00','#56B4E9'],
 'Muted':['#4477AA','#EE6677','#228833','#CCBB44','#66CCEE','#AA3377'],
 'Earth':['#8C510A','#01665E','#C17D11','#72558E','#5E7C42','#AD6B56'],
 'Ocean':['#154C79','#007F8B','#2CA6A4','#7BC8C0','#52689C','#A0BFE0'],
 'Monochrome':['#242A30','#515A64','#7E8894','#ABB3BD','#D4D8DE'],
}
for key,name,english,palette,marker in [
 ('ocean','Océano','Ocean','Ocean','o'),('earth','Tierra','Earth','Earth','s'),
 ('muted','Tonos suaves','Muted tones','Muted','D'),('forest','Bosque','Forest','Earth','^'),
 ('rose','Rosa y pizarra','Rose and slate','Muted','v')]:
    colors=list(PALETTES[palette])
    if key=='forest':colors=['#2F6B49','#AA7733','#4477AA','#AA4499']
    if key=='rose':colors=['#AA3377','#4477AA','#228833','#CCBB44']
    STYLES[key]=dict(name=name,en=english,colors=colors,fill=colors[0],marker=marker,symbol=MARKERS[marker],open=True,line='-',line_origin=0,font='Arial')

def preset(key):
    if key not in STYLES:raise ValueError('Unknown graph style: '+str(key))
    return copy.deepcopy(STYLES[key])

def defaults(key=DEFAULT):
    s=preset(key)
    return dict(results=dict(colors=s['colors'],fill=s['fill'],per_sample=False,marker=s['marker'],open=s['open'],size=4.5,error='#30343B'),
        calibration=dict(colors=s['colors'][:2],marker=s['marker'],open=s['open'],size=4.5,line=s['line'],width=1.2,error='#30343B'),
        dose=dict(colors=s['colors'],marker=s['marker'],open=s['open'],size=4,line=s['line'],width=1.1,error='#30343B'),
        typography=dict(font='Arial',label_size=9,tick_size=8))

def selection(value=DEFAULT):
    """Canonical, validated settings. Accept old preset IDs without changing their meaning."""
    if isinstance(value,str):value=dict(style=value)
    if not isinstance(value,dict):raise ValueError('Invalid graph settings')
    key=value.get('style',DEFAULT);settings=defaults(key)
    overrides=value.get('settings',{})
    if not isinstance(overrides,dict) or set(overrides)-set(settings):raise ValueError('Invalid style section')
    for role,fields in overrides.items():
        if not isinstance(fields,dict) or set(fields)-set(settings[role]):raise ValueError('Invalid style field')
        settings[role].update(copy.deepcopy(fields))
    def color(c):
        if not isinstance(c,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',c):raise ValueError('Expected #RRGGBB colour')
        return c.upper()
    for role in ('results','calibration','dose'):
        s=settings[role];colors=s['colors']
        if not isinstance(colors,list) or not 2<=len(colors)<=12:raise ValueError('Palette: 2–12 colours')
        s['colors']=[color(c) for c in colors];s['error']=color(s['error'])
        if s['marker'] not in MARKERS or type(s['open']) is not bool:raise ValueError('Invalid marker')
        if isinstance(s['size'],bool) or not isinstance(s['size'],(int,float)) or not 2<=s['size']<=12:raise ValueError('Marker size: 2–12 pt')
        if role=='results':
            s['fill']=color(s['fill'])
            if type(s['per_sample']) is not bool:raise ValueError('Invalid colour mode')
        else:
            if s['line'] not in ('-','--',':','-.'):raise ValueError('Invalid line type')
            if isinstance(s['width'],bool) or not isinstance(s['width'],(int,float)) or not .5<=s['width']<=3:raise ValueError('Line width: 0.5–3 pt')
    typography=settings['typography']
    if typography['font'] not in ('Arial','Calibri','Times New Roman','DejaVu Sans'):raise ValueError('Unsupported font')
    for field in ('label_size','tick_size'):
        if type(typography[field]) not in (int,float) or not 7<=typography[field]<=14:raise ValueError('Print text size: 7–14 pt')
    return dict(style=key,settings=settings)

def resolved(value):
    data=selection(value);s=preset(data['style']);s.update(copy.deepcopy(data['settings']))
    return dict(s,id=data['style'])

def role_style(style,role):
    """Flat adapter shared by native Origin and Matplotlib exporters."""
    s=copy.deepcopy(style[role]);s['symbol']=MARKERS[s['marker']];s['line_origin']={'-':0,'--':1,':':2,'-.':3}.get(s.get('line'),0)
    return s

def sample_color(style,index):
    s=style['results'];return s['colors'][index%len(s['colors'])] if s['per_sample'] else s['colors'][0]

def save_user_style(name,value):
    from .data_templates import user_data_dir
    if not isinstance(name,str) or not name.strip() or len(name)>100:raise ValueError('Style name: 1–100 characters')
    data=dict(schema=1,name=name.strip(),**selection(value));folder=user_data_dir()/'graph_styles';folder.mkdir(parents=True,exist_ok=True)
    path=folder/(uuid.uuid4().hex+'.json');dump(path,data);return path

def user_styles():
    from .data_templates import user_data_dir
    items=[]
    for path in sorted((user_data_dir()/'graph_styles').glob('*.json')):
        try:
            data=json.loads(path.read_text(encoding='utf-8'));selection(data)
            if data.get('schema')==1 and isinstance(data.get('name'),str):items.append(data)
        except (ValueError,OSError,KeyError,TypeError):continue
    return sorted(items,key=lambda x:x['name'].casefold())

def read_presentation(folder):
    path=Layout(folder).meta/'presentation.json'
    data=json.loads(path.read_text(encoding='utf-8')) if path.exists() else dict(schema=1,style=DEFAULT,revision=1)
    if data.get('schema') not in (1,2):raise ValueError('Unsupported presentation schema')
    selection(data)
    return data

def save_presentation(folder,key):
    selected=selection(key);old=read_presentation(folder)
    if selection(old)==selected:return old
    data=dict(schema=2,**selected,revision=old.get('revision',1)+1)
    dump(Layout(folder).meta/'presentation.json',data)
    return data

def presentation_hash(folder):return digest(read_presentation(folder))

def for_experiment(folder):
    data=read_presentation(folder);return dict(resolved(data),revision=data['revision'],renderer=7)
