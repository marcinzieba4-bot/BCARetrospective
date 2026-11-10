import os
import sys, re, json, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from get import get
from bs4 import BeautifulSoup
def search(params):
    r = get('/search?' + urllib.parse.urlencode(params))
    s = BeautifulSoup(r.text, 'lxml')
    m = s.find('main') or s
    out = []
    seen=set()
    for a in m.find_all('a', href=True):
        h = a['href']
        if h.startswith('/reports/') and h not in seen:
            seen.add(h)
            # find container text
            par = a
            for _ in range(4):
                if par.parent: par = par.parent
            out.append((h, a.get_text(' ', strip=True)[:90], par.get_text(' | ', strip=True)[:300]))
    last = None
    for a in m.find_all('a', href=True):
        if 'Last' in a.get_text() and 'page=' in a['href']:
            last = a['href']
    return out, last, s
if __name__ == '__main__':
    params = json.loads(sys.argv[1])
    out, last, s = search(params)
    print('n', len(out), 'last', last)
    for o in out[:int(sys.argv[2]) if len(sys.argv)>2 else 10]: print(o)
