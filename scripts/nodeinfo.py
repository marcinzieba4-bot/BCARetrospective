import os
import sys, re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from get import get
from bs4 import BeautifulSoup
def info(nid):
    r = get(f'/node/{nid}', allow_redirects=True)
    if r.status_code != 200: return (nid, r.status_code, None, None, None)
    s = BeautifulSoup(r.text,'lxml')
    t = (s.title.get_text(strip=True) if s.title else '').replace(' | BCA Research','')[:70]
    pub = re.search(r'Published on\W+(\d{1,2} \w{3} \d{4})', s.get_text(' '))
    m = s.find('main') or s
    first = m.get_text('|',strip=True)[:60]
    return (nid, r.status_code, r.url.replace('https://www.bcaresearch.com','')[:60], t, pub.group(1) if pub else None, first)
if __name__=='__main__':
    from concurrent.futures import ThreadPoolExecutor
    ids=[int(x) for x in sys.argv[1:]]
    with ThreadPoolExecutor(8) as ex:
        for r in ex.map(info, ids): print(r)
