"""Application preferences; scientific figures always retain their own print style."""
import json
from .data_templates import user_data_dir
from .integration import dump

def preferences():
    path=user_data_dir()/'preferences.json'
    try:data=json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):data={}
    return dict(language=data.get('language','en') if data.get('language') in ('es','en') else 'en',theme=data.get('theme','light') if data.get('theme') in ('light','dark') else 'light')

def save_preferences(language,theme):
    user_data_dir().mkdir(parents=True,exist_ok=True);dump(user_data_dir()/'preferences.json',dict(language=language,theme=theme))

def stylesheet(dark=False):
    from .interface import STYLE
    if not dark:return STYLE
    colors={'#F4F8FA':'#17232D','#203944':'#E2EAF0','#155D68':'#83D5DA','#FFF7E6':'#3C3525','#77561D':'#F2D38A','#EAD9AE':'#72623A',
      '#CADCE1':'#47606D','#E6F3F4':'#344F59','#5CA8AD':'#76BAC2','#91A1A9':'#758895','#EDF1F4':'#243540','#177E89':'#207E89','#106772':'#2A929E',
      '#DFF0F2':'#284A54','#D9EFF1':'#365660','#D9E6EB':'#3A5362','#E7EFF2':'#263A46','#E9F2F5':'#29424F','#234D5A':'#DBE9EF',
      '#D8E5EB':'#405C6B','#BFD4DC':'#4B6B7A','#F7FAFC':'#22333F','#E4ECF0':'#364C59','#D8EEF1':'#345963','#123E49':'#EFFCFF',
      '#E8F3F5':'#263F4A','#EFF6FA':'#29404C','#365767':'#BBD4DF','#DCEFF1':'#344F59','#C8EAE9':'#285A61','#B5CDD3':'#506C79',
      '#EDF4F6':'#263B48','#123D47':'#EAF7FA','#B9DEDF':'#36757D'}
    result=STYLE.replace('background:white','background:#20313D').replace('color:white','color:#FFFFFF')
    for old,new in colors.items():result=result.replace(old,new)
    return result+'''QListWidget{background:#20313D;border:1px solid #405C6B;border-radius:7px} QListWidget::item{padding:12px 6px;border-bottom:1px solid #364C59} QListWidget::item:selected{background:#345963;color:#EFFCFF} QTextBrowser,QLineEdit{background:#20313D;color:#E2EAF0;border:1px solid #405C6B} QMenu{background:#20313D;color:#E2EAF0} QMenu::item:selected{background:#345963} QToolTip{background:#E3F0F3;color:#17232D;border:1px solid #47606D}'''
