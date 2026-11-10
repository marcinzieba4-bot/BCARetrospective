import os
import sys, re, json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from get import get
from bs4 import BeautifulSoup
def page(params, p):
    q = '&'.join(f'{k}={v}' for k,v in params.items())
    r = get(f'/site/core/reports?{q}&page={p}')
    s = BeautifulSoup(r.text,'lxml')
    m = s.find('main') or s
    out=[]; seen=set()
    for a in m.find_all('a',href=True):
        h=a['href']
        if h.startswith('/reports/') and h not in seen:
            seen.add(h); out.append(h)
    more = any('page=' in a['href'] and 'Load More' in a.get_text() for a in m.find_all('a',href=True))
    return out, more
if __name__=='__main__':
    params = json.loads(sys.argv[1]); outf = sys.argv[2]
    allr=[]; p=0
    while True:
        out, more = page(params, p)
        new=[o for o in out if o not in allr]
        allr += new
        print(p, len(out), len(new), out[-1][-40:] if out else None, flush=True)
        if not more or not new: break
        p+=1
    json.dump(allr, open(outf,'w'), indent=0)
    print('total', len(allr))
