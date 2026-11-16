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
    js=(ROOT/'carecontext/web/app.js').read_text()
    for id in re.findall(r"\$\('([^']+)'\)",js):
        if id not in html.ids:errors.append(f'JavaScript references missing ID {id}')
    data=json.loads((ROOT/'carecontext/data/cases.json').read_text())
    count=sum(len(d['entries']) for d in data['documents'])
    if not data['synthetic'] or not all(d['synthetic'] for d in data['documents']):errors.append('Corpus must remain synthetic')
    if errors:raise SystemExit('\n'.join(errors))
    print(f'Release checks passed: local doc links, {len(html.ids)} DOM IDs, {count} synthetic passages.')

if __name__=='__main__':main()
