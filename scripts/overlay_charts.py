import sys, os, json, pandas as pd, numpy as np, matplotlib, warnings
warnings.filterwarnings('ignore'); matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from overlay_bt import position_returns, simulate
SURF='#fcfcfb'; T1='#0b0b0b'; T2='#52514e'; GRID='#e4e3df'
C=['#2a78d6','#eb6834','#1baf7a','#eda100','#e87ba4','#008300']
plt.rcParams.update({'figure.facecolor':SURF,'axes.facecolor':SURF,'axes.edgecolor':GRID,'axes.labelcolor':T2,'xtick.color':T2,'ytick.color':T2,'text.color':T1,'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.color':GRID,'grid.linewidth':0.6,'axes.titleweight':'bold','axes.titlesize':12,'axes.titlelocation':'left'})
def save(fig, name): fig.savefig(f'charts/{name}.png', dpi=160, bbox_inches='tight'); plt.close(fig)

# 5) equity curves
cv = pd.read_csv('data/overlay_value_daily.csv', index_col=0, parse_dates=True).loc['2015-02-06':'2025-08-04']
S = pd.read_csv('data/overlay_summary.csv').set_index('key')
fig, ax = plt.subplots(figsize=(10, 5.2))
ends = {}
for i, k in enumerate(['A', 'B', 'C', 'D', 'E']):
    y = ((1 + cv[k]).cumprod() - 1) * 100
    lab = S.loc[k, 'strategy']
    ax.plot(y.index, y, color=C[i], lw=2.4 if k == 'D' else 1.6, label=f"{k}. {lab}  (CAGR {S.loc[k,'cagr_pct']:+.1f}%, maxDD {S.loc[k,'maxdd_pct']:.0f}%)")
    ends[k] = y.iloc[-1]; last = y.index[-1]
pos = {}; prev = None
for k, v in sorted(ends.items(), key=lambda kv: kv[1]):
    p = v if prev is None else max(v, prev + 5.5); pos[k] = p; prev = p
for k, v in ends.items():
    ax.annotate(f'{k} {v:+.0f}%', (last, v), xytext=(last + pd.Timedelta(days=40), pos[k]), va='center', fontsize=9, annotation_clip=False)
ax.axhline(0, color=T2, lw=0.8)
ax.set_ylabel('Cumulative return, % of capital'); ax.set_title('GIS "inevitable value" calls: same views, different execution (24 calls, 2015–2025)')
ax.legend(loc='upper left', frameon=False, fontsize=8.3)
ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
save(fig, '5_overlay_equity_curves')

# 6) per-call dumbbell A vs D
T = pd.read_csv('data/overlay_per_call_table.csv').sort_values('A')
fig, ax = plt.subplots(figsize=(10, 7.4))
y = np.arange(len(T))
for yi, (_, r) in zip(y, T.iterrows()):
    ax.plot([r.A, r.D], [yi, yi], color=GRID, lw=3, zorder=1)
ax.scatter(T.A, y, s=60, color=C[0], edgecolor=SURF, linewidth=2, zorder=3, label='A. Naive: hold the call')
ax.scatter(T.D, y, s=60, color=C[3], edgecolor=SURF, linewidth=2, zorder=3, label='D. 6m confirm + 3% trailing stop + re-entry')
ax.set_yticks(y); ax.set_yticklabels([f"{r.id}  {r['name'][:46]}" for _, r in T.iterrows()], fontsize=8.5)
ax.axvline(0, color=T2, lw=0.8); ax.grid(axis='y', visible=False)
ax.set_xlabel('Return over the life of the call, % (unlevered)'); ax.set_title('Per call: where the execution overlay helps and where it hurts')
ax.legend(loc='lower right', frameon=False, fontsize=9)
save(fig, '6_overlay_per_call')

# 7) grid heatmap (Sharpe) for trailing-stop variant, thr=0
G = pd.read_csv('data/overlay_grid.csv')
g = G[(G['mode'] == 'confirm+trailing stop+re-entry') & (G.thr.astype(str) == '0.0')].copy()
g['sl'] = g.sl.astype(float); g['lb'] = g.lb.astype(int)
H = g.pivot_table(index='lb', columns='sl', values='sharpe')
naive = float(G[G['mode'] == 'naive'].sharpe.iloc[0])
fig, ax = plt.subplots(figsize=(7.5, 3.4))
vmax = max(abs(H.values).max(), 0.5)
im = ax.imshow(H.values, cmap=matplotlib.colors.LinearSegmentedColormap.from_list('d', ['#e34948', '#f0efec', '#2a78d6']), vmin=-vmax, vmax=vmax, aspect='auto')
for i in range(H.shape[0]):
    for j in range(H.shape[1]):
        ax.text(j, i, f'{H.values[i, j]:+.2f}', ha='center', va='center', fontsize=10, color=T1)
ax.set_xticks(range(H.shape[1])); ax.set_xticklabels([f'{int(s*100)}%' for s in H.columns]); ax.set_yticks(range(H.shape[0])); ax.set_yticklabels([f'{l}-month' for l in H.index])
ax.set_xlabel('Trailing stop'); ax.set_ylabel('Confirmation look-back'); ax.grid(False)
ax.set_title(f'Sharpe ratio across settings (naive hold = {naive:+.2f})')
save(fig, '7_overlay_grid')

# 8) mechanics example: V5 non-US vs US
calls = {c['id']: c for c in json.load(open('data/value_calls.json'))}
fig, axes = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True, gridspec_kw={'hspace': 0.25})
for ax, cid in zip(axes, ['V5', 'S1']):
    c = calls[cid]; r = position_returns(c['legs'])
    P = (1 + r.loc[c['start']:c['end']]).cumprod() * 100
    daily, trades = simulate(r, c['start'], c['end'], 'confirm_trail_reentry', sl=0.03, lb=6)
    ax.plot(P.index, P, color=T1, lw=1.5)
    for t in trades:
        ax.axvspan(pd.Timestamp(t['entry']), pd.Timestamp(t['exit']), color=C[3], alpha=0.25, lw=0)
    naive = P.iloc[-1] - 100; ov = ((1 + daily).prod() - 1) * 100
    ax.set_title(f"{cid}: {c['name']}  —  naive {naive:+.0f}%, overlay D {ov:+.0f}%", fontsize=10.5)
    ax.set_ylabel('Position value (start = 100)')
axes[0].text(0.01, 0.06, 'Shaded = invested under rule D (6-month confirmation, 3% trailing stop, re-entry)', transform=axes[0].transAxes, fontsize=8.5, color=T2)
axes[1].xaxis.set_major_locator(mdates.YearLocator()); axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
save(fig, '8_overlay_mechanics')
print('ok')
