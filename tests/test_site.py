from pathlib import Path
from html.parser import HTMLParser

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('href','src') and v:self.links.append(v)

def test_static_links_and_blocked_release():
    root=Path(__file__).resolve().parents[1]
    for p in [root/'index.html',*root.glob('docs/*.html')]:
        parser=Links();parser.feed(p.read_text())
        for link in parser.links:
            if not link.startswith(('http','mailto','#')):
                assert (p.parent/link.split('#')[0]).is_file(),(p,link)
    home=(root/'docs/index.html').read_text()
    assert 'Approved .TIF not available' in home
    assert not list((root/'docs').rglob('*.tif'))

def test_archived_result_and_preregistration():
    import json,hashlib
    root=Path(__file__).resolve().parents[1];r=json.loads((root/'evidence/screening.json').read_text())
    assert len(r['folds'])==4 and r['release_allowed'] is False
    assert (root/'docs/screening.json').read_bytes()==(root/'evidence/screening.json').read_bytes()
    assert hashlib.sha256((root/'evidence/preregistered-hypotheses.md').read_bytes()).hexdigest()==r['source_sha256']['docs/hypotheses.md']
