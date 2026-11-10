import sys, pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
sys.path.insert(0, 'scripts')
from yahoo import fetch
SURF='#fcfcfb'; T1='#0b0b0b'; T2='#52514e'; GRID='#e4e3df'
C=['#2a78d6','#eb6834','#1baf7a','#eda100','#e87ba4','#008300']
POS='#2a78d6'; NEG='#e34948'; NEU='#c9c8c2'
plt.rcParams.update({'figure.facecolor':SURF,'axes.facecolor':SURF,'axes.edgecolor':GRID,'axes.labelcolor':T2,'xtick.color':T2,'ytick.color':T2,'text.color':T1,'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.color':GRID,'grid.linewidth':0.6,'axes.titleweight':'bold','axes.titlesize':12,'axes.titlelocation':'left'})
def save(fig, name): fig.savefig(f'charts/{name}.png', dpi=160, bbox_inches='tight'); plt.close(fig)

# 1) Equity stance vs ACWI
acwi = fetch('ACWI')['adj'].loc['2016-01-01':]
stance = [('2016-01-01',3),('2016-07-01',4),('2018-06-20',3),('2018-12-19',4),('2022-06-01',3)]
R = pd.read_csv('data/vm_ratings_long.csv', parse_dates=['date'])
eq = R[(R.key=='AA:Equities')&(R.hz=='cyc')].set_index('date').r
st = pd.Series({pd.Timestamp(d): v for d, v in stance})
st = pd.concat([st[st.index < eq.index[0]], eq]).sort_index()
st = pd.concat([st, pd.Series({pd.Timestamp('2025-10-24'): 3})])  # FullView era: ~benchmark/slight UW per text
st = st[~st.index.duplicated(keep='last')].reindex(acwi.index.union(st.index)).ffill().reindex(acwi.index)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 5.6), sharex=True, gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.08})
a1.plot(acwi.index, acwi / acwi.iloc[0] * 100, color=T1, lw=1.6)
a1.set_yscale('log'); a1.set_ylabel('ACWI total return (Jan-2016 = 100, log)')
a1.set_title('GIS 12-month equity stance vs. global stocks, 2016–2026')
for lo, hi, col, lab in [(4, 5, POS, 'Overweight'), (3, 3, NEU, 'Neutral'), (1, 2, NEG, 'Underweight')]:
    m = (st >= lo) & (st <= hi)
    a2.fill_between(st.index, 0, 1, where=m, color=col, step='post', lw=0, label=lab)
a2.set_yticks([]); a2.grid(False); a2.legend(loc='upper left', ncol=3, frameon=False, bbox_to_anchor=(0, -0.25))
for d, txt in [('2018-06-20','Jun-18: cut to neutral\n(ahead of Q4 sell-off) ✓'),('2018-12-19','Dec-18: back to OW\nnear the low ✓'),('2024-06-27','Jun-24 "Here Comes The Pain";\nUW from ~Sep-24 ✗')]:
    y = acwi.loc[:d].iloc[-1] / acwi.iloc[0] * 100
    a1.annotate(txt, (pd.Timestamp(d), y), xytext={'2018-06-20': (-40, 52), '2018-12-19': (20, -50), '2024-06-27': (0, -60)}[d], textcoords='offset points', ha='center', fontsize=8, color=T2, arrowprops=dict(arrowstyle='-', color=T2, lw=0.6))
a2.xaxis.set_major_locator(mdates.YearLocator()); a2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
save(fig, '1_equity_stance')

# 2) Recession moving target
rc = pd.read_csv('data/recession_calls.csv', parse_dates=['date'])
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.scatter(rc.date, rc.pred, s=34, color=C[1], edgecolor=SURF, linewidth=1.5, zorder=3, label='Forecast recession start (stated in a GIS report)')
lo, hi = 2016, 2027.5
ax.plot([pd.Timestamp('2016-01-01'), pd.Timestamp('2027-06-30')], [2016, 2027.5], color=T2, lw=1, ls='--')
ax.text(pd.Timestamp('2025-09-01'), 2025.2, '"recession now" line', color=T2, fontsize=8, rotation=28)
ax.axhspan(2020.15, 2020.33, color=NEG, alpha=0.18, lw=0); ax.text(pd.Timestamp('2020-08-01'), 2019.85, 'Only actual US recession: Feb–Apr 2020 (COVID, not the forecast mechanism)', fontsize=8, color=T2)
ax.set_ylim(2018.5, 2027.2); ax.set_xlim(pd.Timestamp('2016-01-01'), pd.Timestamp('2026-12-31'))
ax.set_ylabel('Predicted start of recession'); ax.set_title('The moving target: GIS recession-timing forecasts, 2017–2026')
ax.legend(loc='upper left', frameon=False)
save(fig, '2_recession_forecasts')

# 3) Matrix overlays cumulative
cv = pd.read_csv('data/vm_portfolio_curves.csv', index_col=0, parse_dates=True)
cv['aa_active'] = cv['cyc_aa'] - cv['bench']
series = [('aa_active','Equity/bond/cash allocation vs 60/40'),('cyc_EQ:','Regional equity tilts'),('cyc_FI:Duration','Duration'),('cyc_FX:','Currency tilts'),('cyc_CMD:','Commodity tilts'),('cyc_SEC:','Sector tilts (2024–25)')]
fig, ax = plt.subplots(figsize=(10, 5))
for i, (k, lab) in enumerate(series):
    y = ((1 + cv[k]).cumprod() - 1) * 100
    ax.plot(y.index, y, color=C[i], lw=2, label=lab)
    ax.annotate(f'{y.iloc[-1]:+.1f}%', (y.index[-1], y.iloc[-1]), xytext=(6, 0), textcoords='offset points', va='center', fontsize=9, color=T1)
ax.axhline(0, color=T2, lw=0.8)
ax.set_ylabel('Cumulative active return, %'); ax.set_title('Portfolio built from the GIS View Matrix (12-month views), Jan-2020 → Aug-2025')
ax.legend(loc='upper left', frameon=False, fontsize=8.5)
ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
save(fig, '3_matrix_overlays')

# 4) Trade book annual P&L
yr = pd.Series({2015:6.73,2016:5.09,2017:1.87,2018:0.38,2019:-1.68,2020:-0.66,2021:-1.05,2022:-0.33,2023:0.51,2024:0.66})
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.bar(yr.index, yr.values, color=[POS if v > 0 else NEG for v in yr.values], width=0.6, edgecolor=SURF, linewidth=2)
for x, v in yr.items(): ax.text(x, v + (0.2 if v > 0 else -0.2), f'{v:+.1f}', ha='center', va='bottom' if v > 0 else 'top', fontsize=9, color=T1)
ax.axhline(0, color=T2, lw=0.8); ax.set_xticks(yr.index)
ax.set_ylabel('Overlay P&L, % of capital'); ax.set_title('GIS trade book as an overlay (5% notional per trade), by year')
ax.grid(axis='x', visible=False); ax.set_ylim(-2.8, 7.6)
fig.text(0.07, -0.03, 'Blue = gain, red = loss. 2015 includes legacy trades opened 2009–14. FullView era (Oct-25→Jun-26) per BCA: −0.34 pp from overlays.', fontsize=8, color=T2)
save(fig, '4_trade_book')
print('ok')
