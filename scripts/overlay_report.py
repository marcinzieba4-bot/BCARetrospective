import sys, os, json, pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from overlay_bt import run_all, stats
calls = json.load(open('data/value_calls.json'))
CFG = [('A', 'Naive: hold each call', {}, 'naive'),
       ('B', 'BCA-style: 5% stop, no re-entry', dict(sl=0.05), 'naive_sl'),
       ('C', 'Your rule: 1-month confirm + 5% stop + re-entry', dict(lb=1, sl=0.05), 'confirm_sl_reentry'),
       ('D', 'Improved: 6-month confirm + 3% trailing stop + re-entry', dict(lb=6, sl=0.03), 'confirm_trail_reentry'),
       ('E', 'Monthly trend filter (6-month)', dict(lb=6), 'trend_monthly')]
curves, rows, percall, trades = {}, [], [], []
for k, lab, kw, mode in CFG:
    pc, P, T = run_all(calls, modes={mode: ''}, **kw)
    curves[k] = P[mode]
    s = stats(P[mode]); rows.append(dict(key=k, strategy=lab, **{a: round(b, 2) for a, b in s.items()}, entries=len(T), entry_hit_rate=round((T.ret > 0).mean() * 100, 1) if len(T) else None))
    pc['key'] = k; percall.append(pc); T['key'] = k; trades.append(T)
S = pd.DataFrame(rows); S.to_csv('data/overlay_summary.csv', index=False)
pd.DataFrame(curves).to_csv('data/overlay_value_daily.csv')
PC = pd.concat(percall); PC.to_csv('data/overlay_per_call.csv', index=False)
pd.concat(trades).to_csv('data/overlay_trades.csv', index=False)
print(S.to_string(index=False))
piv = (PC.pivot_table(index=['id', 'name'], columns='key', values='total') * 100).round(1).reset_index()
order = [c['id'] for c in calls]; piv['o'] = piv.id.map({k: i for i, k in enumerate(order)}); piv = piv.sort_values('o').drop(columns='o')
piv.to_csv('data/overlay_per_call_table.csv', index=False)
print(piv.to_string(index=False))
yr = pd.DataFrame(curves).loc['2015-02-06':'2025-08-04']
print((yr.groupby(yr.index.year).apply(lambda g: ((1 + g).prod() - 1) * 100)).round(1).to_string())
