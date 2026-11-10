import os
import pandas as pd, numpy as np
df = pd.read_csv('data/all_trades.csv', parse_dates=['open','close'])
df = df[df.unit == '%'].copy()
df['close'] = df['close'].fillna(pd.Timestamp('2026-06-18'))
# FullView era website shows weights; use 5% notional uniformly for comparability (option at 1%)
df['w'] = np.where(df.trade.str.contains('Put Contract'), 0.01, 0.05)
# trades entered before 2015 (legacy strategic) -> only count P&L accrued from 2015-01-01 onward
idx = pd.date_range('2015-01-01', '2026-06-30', freq='D')
pnl = pd.Series(0.0, index=idx); conc = pd.Series(0, index=idx)
for _, r in df.iterrows():
    o, c = max(r.open, idx[0]), r.close
    if c <= o: c = o + pd.Timedelta(days=1)
    days = (c - r.open).days or 1
    seg = pnl.loc[o:c].index
    if len(seg) == 0: continue
    daily = r.w * r.ret / 100 / days   # linear accrual of total return over full holding period
    pnl.loc[seg] += daily
    conc.loc[seg] += 1
ann = pnl.groupby(pnl.index.year).sum() * 100
avgpos = conc.groupby(conc.index.year).mean()
out = pd.DataFrame({'overlay_pnl_%': ann.round(2), 'avg_open_positions': avgpos.round(1), 'implied_gross_exposure_%': (avgpos * 5).round(0)})
print(out.to_string())
print('total 2015-2026H1 (sum):', round(ann.sum(), 1), '%; avg per year:', round(ann.mean(), 2), '%')
