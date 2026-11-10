import sys, json, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from get import get
from concurrent.futures import ThreadPoolExecutor
lst = json.load(open(sys.argv[1])); outdir = sys.argv[2]
os.makedirs(outdir, exist_ok=True)
def work(path):
    nid = path.rstrip('/').split('/')[-1]
    fn = os.path.join(outdir, nid + '.pdf')
    if os.path.exists(fn): return 'cached'
    r = get(f'/reports/{nid}/pdf-hermes')
    if r.status_code != 200 or not r.content.startswith(b'%PDF'): 
        print(nid, 'bad', r.status_code, flush=True); return 'bad'
    open(fn,'wb').write(r.content); return 'ok'
from collections import Counter
with ThreadPoolExecutor(8) as ex: print(Counter(ex.map(work, lst)))
