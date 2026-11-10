import os
import json, re, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from snapshots import snap, page_kind
idx = json.load(open('web/index.json'))
life = {}; dates = []
for x in idx:
    if not x['pdf']: continue
    pages = json.load(open(f"pdftxt/{x['nid']}.json"))['pages']
    got = False
    for p in pages:
        k = page_kind(p)
        if not k or ('trades closed in' in k and not ({'tactical trades','strategic recommendations','special trade recommendations'} & k)): continue
        if 'closed trades' in k and len(k) == 1: continue
        kind = 'special' if 'special trade recommendations' in k else ('strategic' if 'strategic recommendations' in k and 'tactical trades' not in k else 'tact/strat')
        for r in snap(p):
            if not r['init']: continue
            lvl = re.sub(r'[^\d.\-]', '', r['level'])
            key = (r['init'][:10], lvl)
            e = life.setdefault(key, dict(init=r['init'], level=r['level'], names={}, first=x['date'], last=x['date'], rets=[], kind=kind))
            e['names'][r['name']] = e['names'].get(r['name'], 0) + 1
            e['last'] = max(e['last'], x['date']); e['first'] = min(e['first'], x['date'])
            e['rets'].append((x['date'], r['ret']))
            got = True
    if got: dates.append(x['date'])
def clean(n):
    n = re.sub(r'^.*?(?=\b(?:Long(?!-term)|Short|Overweight|Underweight|MacroQuant)\b)', '', n) if re.search(r'\b(?:Long(?!-term)|Short|Overweight|Underweight|MacroQuant)\b', n) else n
    # choose the last START occurrence that begins a plausible name if prefix junk like 'Long Put Option) On ...'
    m = list(re.finditer(r'(?:Long(?!-term)|Short|Overweight|Underweight|MacroQuant)\b', n))
    if len(m) > 1 and re.search(r'Gain|report\*\*|position|Closed', n[:m[-1].start()], re.I):
        for mm in m:
            if not re.search(r'Gain|report\*\*|position|Closed', n[mm.start():], re.I): return n[mm.start():].strip()
    return n.strip()
out = []
for key, e in life.items():
    name = max(e['names'].items(), key=lambda kv: kv[1])[0]
    e2 = dict(init=e['init'], level=e['level'], name=clean(name), first_seen=e['first'], last_seen=e['last'], n_obs=len(e['rets']), last_ret=e['rets'][-1][1] if e['rets'] else None, kind=e['kind'])
    # next table date after last_seen
    nxt = [d for d in dates if d > e['last']]
    e2['dropped_by'] = nxt[0] if nxt else None
    e2['rets'] = e['rets']
    out.append(e2)
out.sort(key=lambda r: r['init'])
json.dump(out, open('data/lifecycle.json', 'w'), indent=1)
print(len(out), 'distinct positions;', len(dates), 'reports with tables;', dates[0], '->', dates[-1])
for r in out:
    if r['n_obs'] >= 1:
        print(r['init'][:10], r['first_seen'], r['last_seen'], str(r['dropped_by']), f"{r['n_obs']:>3}", f"{r['last_ret']:>9}", r['kind'][:5], r['name'][:75])
