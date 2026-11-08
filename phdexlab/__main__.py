import argparse
import json
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description="PhDexLab — prototipo autónomo Windows")
    sub=parser.add_subparsers(dest="command")
    d=sub.add_parser("demo");d.add_argument("folder")
    r=sub.add_parser("refresh");r.add_argument("folder");r.add_argument("--origin",choices=["connector","values","none"],default="connector")
    v=sub.add_parser("verify");v.add_argument("folder")
    sub.add_parser("diagnose")
    args=parser.parse_args()
    if args.command is None:
        from .interface import run
        return run()
    from .integration import create_experiment,refresh,verify
    if args.command=="demo":
        from .data_entry import demo_rows
        print(create_experiment(args.folder,demo_rows()))
    elif args.command=="refresh": print(json.dumps(refresh(args.folder,args.origin),indent=2,ensure_ascii=False))
    elif args.command=="verify": print(json.dumps(verify(args.folder),indent=2))
    else:
        from .diagnostics import diagnose
        print(json.dumps(diagnose(),indent=2,ensure_ascii=False))

if __name__=="__main__": main()
