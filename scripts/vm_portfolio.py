import sys, pandas as pd, numpy as np, json
sys.path.insert(0,'scripts')
from returns import build, MAP
P = build()
ret = P.pct_change().fillna(0)
R = pd.read_csv('data/vm_ratings_long.csv', parse_dates=['date'])
START, END = pd.Timestamp('2020-01-17'), pd.Timestamp('2025-08-29')
days = ret.loc[START:END].index
def ratings(hz):
    w = R[R.hz == hz].pivot_table(index='date', columns='key', values='r')
    # signal known on publication date -> apply from next trading day
    return w.reindex(days.union(w.index)).ffill().reindex(days).shift(1).ffill()
def perf(x, label):
    x = x.dropna(); yrs = len(x) / 252
    cum = (1 + x).prod() - 1; ann = (1 + cum) ** (1 / yrs) - 1; vol = x.std() * np.sqrt(252)
    eq = (1 + x).cumprod(); dd = (eq / eq.cummax() - 1).min()
    return dict(strategy=label, cum_pct=round(100*cum, 1), ann_pct=round(100*ann, 2), vol_pct=round(100*vol, 1), sharpe_or_IR=round(ann/vol, 2) if vol else None, maxDD_pct=round(100*dd, 1))
out = []; curves = {}
for hz in ['cyc', 'tac']:
    W = ratings(hz)
    # 1) Asset allocation: benchmark 60/40/0, tilt 10pp per notch, cash min 0
    we = (0.60 + 0.10*(W['AA:Equities'] - 3)).clip(0.2, 0.9)
    wf = (0.40 + 0.10*(W['AA:Fixed Income'] - 3)).clip(0, 0.8)
    wc = (0.00 + 0.10*(W['AA:Cash'] - 3)).clip(0, 0.4)
    tot = we + wf + wc
    aa = (we/tot)*ret.ACWI.loc[days] + (wf/tot)*ret.FI.loc[days] + (wc/tot)*ret.BIL.loc[days]
    bench = 0.6*ret.ACWI.loc[days] + 0.4*ret.FI.loc[days]
    out.append(perf(aa, f'{hz}: GIS asset allocation (60/40 ±10pp/notch)')); out.append(perf(bench, f'{hz}: 60/40 benchmark'))
    out.append(perf(aa - bench, f'{hz}: AA active return'))
    curves[f'{hz}_aa'] = aa; curves['bench'] = bench
    # 2) overlays: long-short, 5% notional per notch vs benchmark
    def overlay(prefix, size):
        tot = pd.Series(0.0, index=days)
        for k, (s, b) in MAP.items():
            if not k.startswith(prefix) or k not in W: continue
            rel = ret[s].loc[days] - (0 if b is None else (ret[b].loc[days] if b != 'BAL' else 0))
            tot += size * (W[k] - 3).fillna(0) * rel
        return tot
    for prefix, size, lab in [('EQ:', 0.05, 'regional equity tilts'), ('FI:Duration', 0.25, 'duration (IEF vs T-bills)'), ('FI:', 0.05, 'fixed-income sectors+duration'), ('FX:', 0.05, 'currency tilts'), ('CMD:', 0.05, 'commodity tilts'), ('SEC:', 0.03, 'sector tilts (2024-25)')]:
        o = overlay(prefix, size); curves[f'{hz}_{prefix}'] = o
        out.append(perf(o[o != 0] if prefix == 'SEC:' else o, f'{hz}: overlay {lab}'))
df = pd.DataFrame(out); print(df.to_string(index=False))
pd.DataFrame(curves).to_csv('data/vm_portfolio_curves.csv')
# year by year for cyc AA active & overlays
c = pd.DataFrame(curves)
yr = c.groupby(c.index.year).apply(lambda g: ((1+g).prod()-1)*100).round(2)
yr['cyc_aa_active'] = (c.groupby(c.index.year).apply(lambda g: ((1+g.cyc_aa).prod()-(1+g.bench).prod())*100)).round(2)
print(yr[['cyc_aa','bench','cyc_aa_active','cyc_EQ:','cyc_FI:Duration','cyc_FX:','cyc_CMD:']].to_string())
