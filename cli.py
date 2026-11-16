import argparse
import json
from pathlib import Path
import uvicorn

def main():
    parser=argparse.ArgumentParser(description='CareContext synthetic evidence workspace')
    commands=parser.add_subparsers(dest='command',required=True)
    serve=commands.add_parser('serve'); serve.add_argument('--host',default='127.0.0.1'); serve.add_argument('--port',type=int,default=8000)
    evaluate=commands.add_parser('evaluate'); evaluate.add_argument('--output',default='evaluations/results.json')
    args=parser.parse_args()
    if args.command=='serve':
        uvicorn.run('carecontext.api:create_app',factory=True,host=args.host,port=args.port,workers=1)
    else:
        from .evaluation import evaluate
        from .catalog import Catalog
        from .engine import Engine
        result=evaluate(Engine(Catalog()))
        path=Path(args.output); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result['summary'],indent=2))
        if result['summary']['passed'] != result['summary']['total']: raise SystemExit(1)

if __name__=='__main__': main()
