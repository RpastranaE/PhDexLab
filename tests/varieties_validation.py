"""Independent synthetic multi-variety check; needs installed Excel and Origin."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from phdexlab.data_entry import demo_varieties
from phdexlab.protocols import FE
from phdexlab.integration import create_experiment,refresh,verify
from phdexlab.excel import values
from phdexlab.paths import Layout

def main(folder):
    root=create_experiment(folder,demo_varieties(),FE)
    stages=[]
    def progress(step,label):stages.append(step);print(f'{step}/6 {label}',flush=True)
    report=refresh(root,'connector',progress=progress)
    assert report['state']=='complete',report
    actual=values(Layout(root).master,'Summary')[1:]
    assert [r[0] for r in actual]==['Variety A','Variety B','Variety C']
    for row,expected in zip(actual,(16,24,32)):
        assert row[1]==3 and abs(row[2]-expected)<1e-9 and abs(row[3]-1.6)<1e-9,row
    assert stages==[1,2,3,4,5,6]
    assert 'Book1' not in report['origin']['workbooks']
    assert len(report['origin']['exports'])==6
    verify(root)
    print(json.dumps({'summary':actual,'stages':stages,'origin':report['origin']},indent=2))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
