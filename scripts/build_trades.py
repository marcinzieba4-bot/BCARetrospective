import json, re, pandas as pd, numpy as np
closed = json.load(open('data/closed_2015_2019.json'))
life = json.load(open('data/lifecycle.json'))
web = json.load(open('data/website_trades_berezin.json'))
def pct(s):
    if s is None: return None, None
    s = s.replace(' ', '').replace(',', '')
    m = re.match(r'^([+\-]?[\d.]+)(%|BPS|bps|BPs|Bps)$', s)
    if not m: return None, None
    v = float(m.group(1)); u = '%' if m.group(2) == '%' else 'bps'
    return v, u
def asset_class(n):
    n = n.lower()
    if re.search(r'bitcoin|proof of', n): return 'Crypto'
    if re.search(r'gold|oil|brent|wti|crb|copper|silver|slv|uso|commodit|dba|cper', n) and not re.search(r'stocks|equit|miners', n): return 'Commodities'
    if re.search(r'eurodollar|fed funds|sofr|bax|estr|cpi swap|tips', n): return 'Rates/Credit'
    if re.search(r'dollar|euro /|/ euro|yen|pound|krona|franc|ruble|rub|yuan|cny|cnh|riyal|aud|cad|nzd|eur|usd|jpy|gbp|dxy|brl|currenc', n) and not re.search(r'bond|treasur|equit|stocks|etf \(|msci', n): return 'FX'
    if re.search(r'bond|treasur|bund|jgb|gilt|swap|fed funds|eurodollar|sofr|bax|estr|tlt|ief|tips|government|high yield', n) and not re.search(r's&p 500 /|short s&p|/ short s&p', n): return 'Rates/Credit'
    return 'Equities'
rows = []
# Era 1: 2015-2019 closed ledger (self-reported realized P&L)
for t in closed:
    rows.append(dict(era='2015-19 trade tables', trade=t['trade'], type=t['type'], open=t['open'].rstrip('~'), close=t['close'], ret=t['pnl'], unit=t['unit'], status='closed (reported)'))
# Era 1b: strategic book open at 27 Mar 2020, silently dropped -> mark at last reported value
closed_keys = {(t['open'][:7], round(float(re.sub(r'[^\d.]', '', t['level']) or 0), 2)) for t in closed}
import sys
sys.path.insert(0,'scripts')
from snapshots import snap
pg = json.load(open('pdftxt/166486.json'))['pages'][26]
for r in snap(pg):
    nm = re.sub(r'^.*?Gain\s+', '', r['name']).strip()
    nm = re.sub(r'(?<=[a-zA-Z)])\d$', '', nm)
    v, u = pct(r['ret'])
    rows.append(dict(era='2015-19 trade tables', trade=nm, type='Strategic', open=r['init'][:10], close='2020-03-27', ret=v, unit=u, status='open, dropped Apr-2020 (last mark)'))
# Era 2: special trades Dec 2020 - May 2025
web_by_name = {}
for w in web: web_by_name.setdefault(w['trade'][:40].lower(), w)
for e in life:
    if e['kind'] != 'special': continue
    v, u = pct(e['last_ret'])
    status = 'closed (last mark before removal)'
    close = e['last_seen']
    # trades still listed at end of table era -> use website final value if available
    if e['dropped_by'] is None or e['last_seen'] >= '2024-11':
        key = e['name'][:40].lower()
        w = next((w for k, w in web_by_name.items() if k[:25] == key[:25]), None)
        if w:
            v2, u2 = pct(w['ret'])
            if v2 is not None: v, u, status = v2, u2, 'closed (website final)'
            close = None
    if u == 'bps' and 'Canada 10-Year' in e['name']: v, u = v / 100, '%'
    rows.append(dict(era='2020-25 special trades', trade=e['name'], type='Special', open=e['init'][:10], close=close, ret=v, unit=u, status=status))
# Era 3: FullView-era trades on website (dated via comments)
for w in web:
    if not w['true_open']: continue
    v, u = pct(w['ret'])
    rows.append(dict(era='2025-26 FullView era', trade=w['trade'], type='Overlay' + (f" w={w['weight']}%" if w['weight'] else ''), open=w['true_open'], close=w['true_last'] if w['closed'] else None, ret=v, unit=u, status='closed' if w['closed'] else 'open'))
df = pd.DataFrame(rows)
df['asset'] = df['trade'].apply(asset_class)
df['open'] = pd.to_datetime(df['open']); df['close'] = pd.to_datetime(df['close'])
df.to_csv('data/all_trades.csv', index=False)
print(df.groupby(['era','status']).size())
