import sys, json, gzip, os, time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from get import get
from concurrent.futures import ThreadPoolExecutor
lst = json.load(open(sys.argv[1])); outdir = sys.argv[2]
def dl(path):
    nid = path.rstrip('/').split('/')[-1]
    fn = os.path.join(outdir, nid + '.html.gz')
    if os.path.exists(fn): return (nid, 'cached')
    r = get(path)
    if r.status_code != 200: return (nid, r.status_code)
    if 'Continue reading this report' in r.text and 'not in your subscription' in r.text:
        st = 'PAYWALL'
    else: st = 'ok'
    with gzip.open(fn, 'wt') as f: f.write(r.text)
    return (nid, st)
from collections import Counter
c = Counter()
with ThreadPoolExecutor(4) as ex:
    for i, (nid, st) in enumerate(ex.map(dl, lst)):
        c[st] += 1
        if st not in ('ok','cached'): print(nid, st)
print(c)
