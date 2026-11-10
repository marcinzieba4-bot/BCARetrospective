import json, re, sys, pdfplumber
from multiprocessing import Pool
ROWS = ['Equities','Fixed Income','Cash','US','Euro Area','UK','Canada','Australia','Japan','EM','Government','Investment Grade','High Yield','Duration','Inflation Protection','US Treasuries','UK Gilts','German Bunds','JGBs','EM Sovereign','USD','EUR','GBP','CHF','JPY','CAD','AUD','EM Currencies','Energy','Base/Bulk Metals','Gold','Softs']
SECTIONS = {'Global Asset Allocation':'AA','Global Equities':'EQ','Global Fixed Income (Region)':'FIR','Global Fixed Income':'FI','Currencies':'FX','Commodities':'CMD'}
def parse(args):
    date, nid, pi = args
    try:
        pdf = pdfplumber.open(f'pdf/{nid}.pdf'); pg = pdf.pages[pi]
        words = pg.extract_words(keep_blank_chars=False, use_text_flow=False)
        hdr = {}
        for w in words:
            if w['text'] in ('3-Month','12-Month','10-Year'): hdr[w['text']] = (w['x0']+w['x1'])/2
            if w['text'] == 'Recommendations' or w['text'].startswith('MacroQuant'): hdr.setdefault('MQ', (w['x0']+w['x1'])/2)
        if not {'3-Month','12-Month','10-Year'} <= set(hdr): return (date, nid, None, 'nohdr')
        cols = sorted(hdr.items(), key=lambda kv: kv[1])
        segs = [l for l in pg.lines + pg.curves if (l['x1']-l['x0']) < 15 and (l['bottom']-l['top']) > 2]
        # group words into lines by top
        lines = {}
        for w in words:
            lines.setdefault(round(w['top']), []).append(w)
        merged = {}
        for t in sorted(lines):
            key = next((k for k in merged if abs(k - t) <= 2), t)
            merged.setdefault(key, []).extend(lines[t])
        out = {}; section = None
        for t in sorted(merged):
            ws = sorted(merged[t], key=lambda w: w['x0'])
            label = ' '.join(w['text'] for w in ws if w['x1'] < min(hdr.values()) - 25)
            label = label.replace('*','').strip()
            for s, code in SECTIONS.items():
                if label.startswith(s): section = code
            if label not in ROWS or section is None: continue
            vals = {}
            for w in ws:
                if not re.fullmatch(r'[1-5]', w['text']) or w['x1'] < min(hdr.values()) - 25: continue
                struck = any(s['x0'] <= w['x1'] and s['x1'] >= w['x0'] and s['top'] <= w['bottom'] and s['bottom'] >= w['top'] for s in segs)
                cx = (w['x0']+w['x1'])/2
                col = min(cols, key=lambda kv: abs(kv[1]-cx))[0]
                vals.setdefault(col, []).append((int(w['text']), struck))
            rec = {}
            for col, lst in vals.items():
                cur = [v for v, s in lst if not s]; old = [v for v, s in lst if s]
                rec[col] = dict(cur=cur[-1] if cur else None, old=old[-1] if old else None, n=len(lst))
            out[f'{section}:{label}'] = rec
        return (date, nid, out, 'ok')
    except Exception as e:
        return (date, nid, None, f'err {e}')
if __name__ == '__main__':
    reps = json.load(open(sys.argv[1]))
    with Pool(4) as p: res = p.map(parse, [tuple(r) for r in reps])
    json.dump(res, open(sys.argv[2], 'w'))
    from collections import Counter
    print(Counter(r[3].split()[0] for r in res))
    print(Counter(len(r[2]) for r in res if r[2]))
