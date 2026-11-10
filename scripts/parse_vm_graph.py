import os
import json, sys, pdfplumber, re
from multiprocessing import Pool
LABELS = ['Equities','Fixed Income','Cash','US','Euro Area','UK','Canada','Australia','Japan','EM','Communication Services','Consumer Discretionary','Consumer Staples','Energy','Financials','Health Care','Industrials','Information Technology','Materials','Real Estate','Utilities','Government','Investment Grade','High Yield','Duration','Inflation Protection','USD','EUR','GBP','CHF','JPY','CAD','AUD','EM Currencies','Base/Bulk Metals','Gold']
SECT = [('Global Asset Allocation','AA'),('Global Equities (Region)','EQ'),('Global Equities (Sectors)','SEC'),('Global Fixed Income','FI'),('Currencies','FX'),('Commodities','CMD')]
def darkness(c):
    if c is None: return 0
    if isinstance(c,(int,float)): c=(c,)
    c=list(c)
    if len(c)==4: return min(1, c[3] + sum(c[:3])/3)
    if len(c)==3: return 1 - sum(c)/3
    if len(c)==1: return 1 - c[0]
    return 0
def parse(args):
    date, nid, pi = args
    pdf = pdfplumber.open(f'pdf/{nid}.pdf'); pg = pdf.pages[pi]
    boxes = [r for r in pg.rects if 4 <= r['width'] <= 14 and 4 <= r['height'] <= 14 and abs(r['width']-r['height']) < 2.5]
    if len(boxes) < 50: return (date, nid, None, f'few boxes {len(boxes)}')
    xs = sorted(set(round((b['x0']+b['x1'])/2) for b in boxes))
    # cluster x centers
    cl = []
    for x in xs:
        if cl and x - cl[-1][-1] <= 3: cl[-1].append(x)
        else: cl.append([x])
    centers = [sum(c)/len(c) for c in cl]
    words = pg.extract_words()
    if len(centers) == 5:
        hz_words = [w for w in words if w['text'] in ('1-To-3','6-To-12')]
        if len(hz_words) != 1: return (date, nid, None, f'xclusters5 hz {[w["text"] for w in hz_words]}')
        only = '1-3M' if hz_words[0]['text']=='1-To-3' else '6-12M'
        centers = centers + [9999]*5 if only=='1-3M' else [-9999]*5 + centers
    elif len(centers) != 10: return (date, nid, None, f'xclusters {len(centers)}')
    # rows: label words to the left of boxes
    left = min(c for c in centers if c > 0) - 10
    lines = {}
    for w in words:
        if w['x1'] < left: lines.setdefault(round(w['top']), []).append(w)
    rowpos = []; section = None; seen=set()
    for t in sorted(lines):
        ws = sorted(lines[t], key=lambda w: w['x0'])
        lab = ' '.join(w['text'] for w in ws).replace('*','').strip()
        for s, code in SECT:
            if lab.startswith(s): section = code
        if lab in LABELS and section:
            ymid = (ws[0]['top'] + ws[0]['bottom'])/2
            rowpos.append((f'{section}:{lab}', ymid))
    # commodities 'Energy' vs sector 'Energy' disambiguated by section
    out = {}
    for b in boxes:
        fill = b.get('fill') and darkness(b.get('non_stroking_color')) > 0.5
        if not fill: continue
        cx = (b['x0']+b['x1'])/2; cy = (b['top']+b['bottom'])/2
        ci = min(range(10), key=lambda i: abs(centers[i]-cx))
        row = min(rowpos, key=lambda rp: abs(rp[1]-cy)) if rowpos else None
        if not row or abs(row[1]-cy) > 8: continue
        hz = '1-3M' if ci < 5 else '6-12M'
        out.setdefault(row[0], {}).setdefault(hz, []).append(ci % 5 + 1)
    return (date, nid, out, 'ok')
if __name__ == '__main__':
    reps = json.load(open(sys.argv[1]))
    with Pool(4) as p: res = p.map(parse, [tuple(r) for r in reps])
    json.dump(res, open(sys.argv[2], 'w'))
    from collections import Counter
    print(Counter(r[3] for r in res))
    multi = sum(1 for r in res if r[2] for k,v in r[2].items() for h,l in v.items() if len(l)!=1)
    print('cells with !=1 filled box:', multi, Counter(len(r[2]) for r in res if r[2]))
