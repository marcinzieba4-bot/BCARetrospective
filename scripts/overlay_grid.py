import sys, os, json, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from overlay_bt import run_all, stats
calls = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'data/value_calls.json'))
rows = []
base = run_all(calls, modes={'naive': ''})[1]['naive']
b = stats(base); rows.append(dict(mode='naive', lb='-', thr='-', sl='-', **b))
for lb in [1, 3, 6]:
    for thr in [0.0, 0.02]:
        tf = run_all(calls, modes={'trend_monthly': ''}, thr=thr, lb=lb)[1]['trend_monthly']
        rows.append(dict(mode='trend filter', lb=lb, thr=thr, sl='-', **stats(tf)))
        for sl in [0.03, 0.05, 0.08, 0.10, 0.15]:
            P = run_all(calls, modes={'confirm_sl_reentry': '', 'confirm_trail_reentry': ''}, sl=sl, thr=thr, lb=lb)[1]
            rows.append(dict(mode='confirm+stop+re-entry', lb=lb, thr=thr, sl=sl, **stats(P['confirm_sl_reentry'])))
            rows.append(dict(mode='confirm+trailing stop+re-entry', lb=lb, thr=thr, sl=sl, **stats(P['confirm_trail_reentry'])))
df = pd.DataFrame(rows).round(2)
out = sys.argv[2] if len(sys.argv) > 2 else 'data/overlay_grid.csv'
df.to_csv(out, index=False)
print(df.sort_values('sharpe', ascending=False).head(12).to_string(index=False))
print('...'); print(df.groupby('mode')[['cagr_pct','sharpe','maxdd_pct']].agg(['median','min','max']).round(2).to_string())
print('share of grid configs beating naive CAGR:', round((df[df['mode']!='naive'].cagr_pct > b['cagr_pct']).mean()*100), '%; with positive CAGR:', round((df[df['mode']!='naive'].cagr_pct > 0).mean()*100), '%')
