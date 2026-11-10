import pandas as pd, numpy as np
df = pd.read_csv('data/all_trades.csv', parse_dates=['open','close'])
def stats(d, label):
    p = d[d.unit == '%'].ret.dropna(); b = d[d.unit == 'bps'].ret.dropna()
    allv = pd.concat([p, b])
    wins = (allv > 0).sum(); n = len(allv)
    w = p[p > 0]; l = p[p <= 0]
    pf = w.sum() / -l.sum() if len(l) and l.sum() != 0 else np.nan
    hold = ((d.close - d.open).dt.days / 365.25).dropna()
    return dict(group=label, n=n, hit_rate=round(wins / n * 100, 1) if n else None, n_pct=len(p), mean_pct=round(p.mean(), 2), median_pct=round(p.median(), 2),
                avg_win=round(w.mean(), 2), avg_loss=round(l.mean(), 2), profit_factor=round(pf, 2), n_bps=len(b), sum_bps=round(b.sum(), 0), med_hold_yrs=round(hold.median(), 2))
out = []
e1 = df[df.era == '2015-19 trade tables']
out.append(stats(e1[e1.status == 'closed (reported)'], '2015-19 closed only (as BCA reports)'))
out.append(stats(e1, '2015-19 closed + open book at Mar-2020 marks'))
for t in ['Tactical', 'Strategic']:
    out.append(stats(e1[(e1.type == t)], f'  2015-19 {t} (incl. open marks)'))
for a in ['Equities','Rates/Credit','FX','Commodities']:
    out.append(stats(e1[e1.asset == a], f'  2015-19 {a}'))
e2 = df[df.era == '2020-25 special trades']
out.append(stats(e2, '2020-25 special trades'))
for a in ['Equities','Rates/Credit','FX','Commodities','Crypto']:
    if (e2.asset == a).any(): out.append(stats(e2[e2.asset == a], f'  2020-25 {a}'))
e3 = df[df.era == '2025-26 FullView era']
out.append(stats(e3, '2025-26 FullView-era overlays'))
out.append(stats(df, 'ALL ERAS'))
print(pd.DataFrame(out).to_string(index=False))
