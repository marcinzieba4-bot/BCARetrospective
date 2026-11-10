import json, re, pandas as pd
idx = json.load(open('web/index.json'))
FWD = re.compile(r'(will|expect|likely|place|setting the stage|set the stage|sow(?:ing)? the seeds|forecast|base case|best guess|ahead of|anticipation of|advance of|culminating|odds|probability|predict|succumb|centered on|tip into|fall into|enter)', re.I)
PAT = re.compile(r'recession[^.\n]{0,40}?\b(?:in|by|starting in|beginning in|begin(?:ning)? in|during|to begin in|to start in)\s+(?:the\s+)?(?:(late|early|mid|second half of|first half of)[\s-]+)?(20\d\d)(?:\s+or\s+(?:early\s+|late\s+)?(20\d\d))?', re.I)
rows = []
for x in idx:
    t = open(f"txt/{x['nid']}.txt").read()
    for sent in re.split(r'(?<=[.!?])\s+', t):
        if 'recession' not in sent.lower() or not FWD.search(sent): continue
        if re.search(r'avoid|averted|without a recession|no recession|economists|consensus|investors (?:were|are) expecting|most (?:people|investors|analysts|strategists)|survey|fund manag|unlikely|as long as the risks|10% (?:odds|chance)', sent, re.I): continue
        for m in PAT.finditer(sent):
            y1 = int(m.group(2)); q = (m.group(1) or '').lower()
            frac = {'late': 0.8, 'second half of': 0.75, 'early': 0.15, 'first half of': 0.25, 'mid': 0.5}.get(q, 0.5)
            pred = y1 + frac
            if m.group(3): pred = (pred + int(m.group(3)) + 0.15) / 2
            sy = int(x['date'][:4]) + (int(x['date'][5:7]) - 0.5) / 12
            if pred < sy - 0.1 or pred > sy + 4: continue
            rows.append(dict(date=x['date'], pred=round(pred, 2), text=sent.strip()[:200]))
df = pd.DataFrame(rows).drop_duplicates(['date', 'pred'])
df.to_csv('data/recession_calls.csv', index=False)
print(len(df)); print(df.groupby(df.date.str[:4]).pred.agg(['count', 'min', 'max']))
