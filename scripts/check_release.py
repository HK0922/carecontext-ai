"""Source-only release checks; no installed project dependencies required."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re

ROOT=Path(__file__).resolve().parents[1]
class Elements(HTMLParser):
    def __init__(self): super().__init__(); self.ids=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key=='id': self.ids.append(value)

def main():
    errors=[]
    for path in [ROOT/'README.md',*sorted((ROOT/'docs').glob('*.md'))]:
        text=path.read_text()
        links=re.findall(r'\]\(([^)]+)\)',text)+re.findall(r'src="([^"]+)"',text)
        for link in links:
            if link.startswith(('https://','http://','#','mailto:')):continue
            if not (path.parent/link.split('#')[0]).exists():errors.append(f'Missing link in {path.name}: {link}')
    html=Elements();html.feed((ROOT/'carecontext/web/index.html').read_text())
    if len(html.ids)!=len(set(html.ids)):errors.append('Duplicate DOM IDs')
    studio=Elements();studio.feed((ROOT/'carecontext/web/studio.html').read_text())
    if len(studio.ids)!=len(set(studio.ids)): errors.append('Duplicate Studio DOM IDs')
    research=Elements();research.feed((ROOT/'carecontext/web/research.html').read_text())
    if len(research.ids)!=len(set(research.ids)):errors.append('Duplicate Research Lab DOM IDs')
    research_js=(ROOT/'carecontext/web/research.js').read_text()
    for target in re.findall(r"\$\('([^']+)'\)",research_js):
        if target not in research.ids:errors.append(f'Research Lab JavaScript references missing ID {target}')
    if not (ROOT/'carecontext/web/research.css').exists():errors.append('Missing Research Lab stylesheet')
    registry=json.loads((ROOT/'data/registry.json').read_text())
    if not registry.get('sources'):errors.append('Missing research source registry')
    for entry in registry.get('sources',[]):
        if entry.get('kind','').startswith('restricted') and entry.get('local_path'):
            errors.append(f'Restricted dataset must not be bundled: {entry["id"]}')
    studio_js=(ROOT/'carecontext/web/studio.js').read_text()
    for target in re.findall(r"\$\('#([^']+)'\)",studio_js):
        if target not in studio.ids: errors.append(f'Studio JavaScript references missing ID {target}')
    if not (ROOT/'carecontext/web/fictional_lab_sample.pdf').exists(): errors.append('Synthetic sample PDF missing')
    js=(ROOT/'carecontext/web/app.js').read_text()
    for id in re.findall(r"\$\('([^']+)'\)",js):
        if id not in html.ids:errors.append(f'JavaScript references missing ID {id}')
    data=json.loads((ROOT/'carecontext/data/cases.json').read_text())
    count=sum(len(d['entries']) for d in data['documents'])
    if not data['synthetic'] or not all(d['synthetic'] for d in data['documents']):errors.append('Corpus must remain synthetic')
    if errors:raise SystemExit('\n'.join(errors))
    print(f'Release checks passed: local doc links, {len(html.ids)} legacy IDs, {len(studio.ids)} Studio IDs, {len(research.ids)} research IDs, {len(registry["sources"])} registry sources, {count} synthetic passages.')

if __name__=='__main__':main()
