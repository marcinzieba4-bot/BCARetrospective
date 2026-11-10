import sys, pandas as pd, numpy as np
sys.path.insert(0,'scripts')
from returns import build, MAP
def spearmanr(a,b):
    class R: pass
    o=R(); o.correlation=pd.Series(list(a)).rank().corr(pd.Series(list(b)).rank()); return o
P = build()
P['BAL'] = np.exp((0.6*np.log(P.ACWI).diff() + 0.4*np.log(P.FI).diff()).fillna(0).cumsum())
R = pd.read_csv('data/vm_ratings_long.csv', parse_dates=['date'])
H = {'tac': 63, 'cyc': 252}
dates = P.index
def fwd(series, bench, d, h):
    i = dates.searchsorted(d)
    if i + h >= len(dates): return np.nan
    a = P[series].iloc[i+h] / P[series].iloc[i] - 1
    b = 0 if bench is None else P[bench].iloc[i+h] / P[bench].iloc[i] - 1
    return a - b
rows = []
for _, r in R[R.hz.isin(['tac','cyc'])].iterrows():
    if r.key not in MAP: continue
    s, b = MAP[r.key]
    rows.append(dict(date=r.date, key=r.key, cat=r.key.split(':')[0], hz=r.hz, r=r.r, fwd=fwd(s, b, r.date, H[r.hz])))
E = pd.DataFrame(rows).dropna()
E.to_csv('data/vm_eval_obs.csv', index=False)
def summ(g):
    act = g[g.r != 3]
    hit = (np.sign(act.r - 3) == np.sign(act.fwd)).mean() if len(act) else np.nan
    ow = g[g.r >= 4].fwd.mean(); uw = g[g.r <= 2].fwd.mean(); nt = g[g.r == 3].fwd.mean()
    ic = spearmanr(g.r, g.fwd).correlation if g.r.nunique() > 1 else np.nan
    return pd.Series(dict(n=len(g), active=len(act), hit_rate=round(100*hit,1), OW_fwd=round(100*ow,2), N_fwd=round(100*nt,2), UW_fwd=round(100*uw,2), OW_minus_UW=round(100*(ow-uw),2), IC=round(ic,3)))
print('=== By category & horizon (weekly obs, overlapping windows) ===')
print(E.groupby(['hz','cat']).apply(summ, include_groups=False).to_string())
print('\n=== Key single calls (12m horizon) ===')
print(E[(E.hz=='cyc') & E.key.isin(['AA:Equities','AA:Fixed Income','AA:Cash','EQ:US','EQ:EM','EQ:Euro Area','FI:Duration','FX:USD','CMD:Gold'])].groupby('key').apply(summ, include_groups=False).to_string())
print('\n=== Key single calls (3m horizon) ===')
print(E[(E.hz=='tac') & E.key.isin(['AA:Equities','AA:Fixed Income','AA:Cash','EQ:US','FI:Duration','FX:USD'])].groupby('key').apply(summ, include_groups=False).to_string())
