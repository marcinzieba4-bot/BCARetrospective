import sys, os, json, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from overlay_bt import run_all, stats
calls = json.load(open('data/matrix_calls_12m.json'))
CFG = [('naive (hold each call)', {}, 'naive'), ('pre-registered: 1m confirm + 5% stop + re-entry', dict(lb=1, sl=0.05), 'confirm_sl_reentry'),
       ('6m confirm + 5% stop + re-entry', dict(lb=6, sl=0.05), 'confirm_sl_reentry'), ('6m confirm + 3% trailing stop + re-entry', dict(lb=6, sl=0.03), 'confirm_trail_reentry'),
       ('monthly trend filter (6m)', dict(lb=6), 'trend_monthly')]
rows = []; curves = {}
for sizing, kw0 in [('equal 5% notional', dict(target_vol=None, fixed_notional=0.05)), ('2% vol target per call', dict(target_vol=0.02))]:
    for cfg, kw, mode in CFG:
        pc, P, T = run_all(calls, modes={mode: ''}, **kw0, **kw)
        s = stats(P[mode], '2019-12-13', '2025-08-04')
        rows.append(dict(sizing=sizing, config=cfg, cagr=round(s['cagr_pct'], 2), vol=round(s['vol_pct'], 1), sharpe=round(s['sharpe'], 2), maxdd=round(s['maxdd_pct'], 1), calls_positive=f"{(pc.total > 0).mean() * 100:.0f}%"))
        if sizing.startswith('equal'): curves[cfg] = P[mode]
df = pd.DataFrame(rows); df.to_csv('data/overlay_matrix_results.csv', index=False)
pd.DataFrame(curves).to_csv('data/overlay_matrix_daily.csv')
print(df.to_string(index=False))
