"""Build a clean, deterministic source archive with per-file SHA-256 hashes."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DIRS={'carecontext','tests','docs','scripts','evaluations','.github'}
FILES={'README.md','PUBLISHING.md','LICENSE','CONTRIBUTING.md','SECURITY.md','CHANGELOG.md','THIRD_PARTY_NOTICES.md','AGENTS.md',
       'pyproject.toml','requirements.lock','package.json','Dockerfile','compose.yaml','.dockerignore','.gitignore','.env.example'}
EXTENSIONS={'.py','.js','.mjs','.css','.html','.svg','.png','.json','.md','.yml','.yaml'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='../CareContext_GitHub_Ready.zip');a=p.parse_args()
    files=[]
    for path in sorted(ROOT.rglob('*')):
        rel=path.relative_to(ROOT)
        if not path.is_file() or path.is_symlink() or '__pycache__' in rel.parts:continue
        if len(rel.parts)==1 and rel.name in FILES:files.append(path)
        elif rel.parts[0] in DIRS and path.suffix in EXTENSIONS:files.append(path)
    for path in files:
        if path.suffix=='.json':json.loads(path.read_text())
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    dest=Path(a.output).resolve();dest.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for path in files:
            info=zipfile.ZipInfo('carecontext/'+str(path.relative_to(ROOT)),date_time=(2026,10,30,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,path.read_bytes())
        info=zipfile.ZipInfo('carecontext/SOURCE_MANIFEST.json',date_time=(2026,10,30,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(files)+1
        for name,digest in manifest.items():assert hashlib.sha256(z.read('carecontext/'+name)).hexdigest()==digest
    print(json.dumps({'archive':str(dest),'source_files':len(files),'size_bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()},indent=2))

if __name__=='__main__':main()
