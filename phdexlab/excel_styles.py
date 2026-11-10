"""Workbook-only appearance, independently versioned from scientific plot styles."""
import copy,json,re
from .paths import Layout
from .integration import dump

PRESETS={
 'teal':dict(name='Turquesa',en='Teal',header='#173E4A',accent='#177E89',input='#EAF4FC',input_text='#145B9B',stripe='#F3F7F8'),
 'blue':dict(name='Azul',en='Blue',header='#183B65',accent='#356FA8',input='#EDF4FD',input_text='#22548B',stripe='#F1F5FA'),
 'green':dict(name='Verde',en='Green',header='#254D3D',accent='#368367',input='#EDF6EE',input_text='#246144',stripe='#F1F6F3'),
 'violet':dict(name='Violeta',en='Violet',header='#493963',accent='#8061A0',input='#F3EFF9',input_text='#634384',stripe='#F7F4FA'),
 'sand':dict(name='Arena',en='Sand',header='#66513A',accent='#A17B42',input='#FBF4E8',input_text='#755124',stripe='#F8F5EF'),
 'mono':dict(name='Monocromo',en='Monochrome',header='#30363D',accent='#535E6A',input='#EFF1F4',input_text='#283C55',stripe='#F4F5F6')}

def selection(value=None):
    value=value or {};key=value.get('preset','teal')
    if key not in PRESETS:raise ValueError('Unknown Excel preset')
    result=dict(preset=key,**{k:v for k,v in PRESETS[key].items() if k not in ('name','en')},font='Calibri',font_size=11,row_height=29,striped=True,header_text='#FFFFFF',text='#26373D',background='#FFFFFF',border_color='#DCE5E9',border='none',alignment='left',header_size=11,section_size=12,title_size=14,header_height=58,column_scale=100,gridlines=False)
    result.update({k:v for k,v in value.items() if k in result})
    for key in ('header','accent','input','input_text','stripe','header_text','text','background','border_color'):
        if not isinstance(result[key],str) or not re.fullmatch('#[0-9A-Fa-f]{6}',result[key]):raise ValueError('Invalid Excel colour')
    if result['font'] not in ('Calibri','Arial','Aptos','Times New Roman'):raise ValueError('Invalid Excel font')
    if type(result['font_size']) is not int or not 9<=result['font_size']<=16:raise ValueError('Excel font size: 9–16')
    if type(result['row_height']) is not int or not 22<=result['row_height']<=48:raise ValueError('Excel row height: 22–48')
    if type(result['striped']) is not bool:raise ValueError('Invalid stripe setting')
    for key,low,high in [('header_size',9,20),('section_size',10,24),('title_size',12,28),('header_height',36,100),('column_scale',75,150)]:
        if type(result[key]) is not int or not low<=result[key]<=high:raise ValueError('Invalid Excel '+key)
    if result['border'] not in ('none','horizontal','all'):raise ValueError('Invalid Excel borders')
    if result['alignment'] not in ('left','center','right'):raise ValueError('Invalid Excel alignment')
    if type(result['gridlines']) is not bool:raise ValueError('Invalid Excel gridlines')
    return result

def read(folder):
    path=Layout(folder).meta/'excel_style.json'
    return selection(json.loads(path.read_text(encoding='utf-8')) if path.exists() else None)

def save(folder,value):
    result=selection(value);dump(Layout(folder).meta/'excel_style.json',result);return result
import uuid

def save_user_style(name,value):
    from .data_templates import user_data_dir
    if not isinstance(name,str) or not name.strip() or len(name)>100:raise ValueError('Style name: 1–100 characters')
    folder=user_data_dir()/'excel_styles';folder.mkdir(parents=True,exist_ok=True);path=folder/(uuid.uuid4().hex+'.json')
    dump(path,dict(schema=1,name=name.strip(),settings=selection(value)));return path


def user_styles():
    from .data_templates import user_data_dir
    result=[]
    for path in (user_data_dir()/'excel_styles').glob('*.json'):
        try:
            data=json.loads(path.read_text(encoding='utf-8'));settings=selection(data['settings'])
            if data.get('schema')==1 and isinstance(data.get('name'),str):result.append(dict(name=data['name'],settings=settings))
        except (OSError,ValueError,KeyError,TypeError):continue
    return sorted(result,key=lambda x:x['name'].casefold())
