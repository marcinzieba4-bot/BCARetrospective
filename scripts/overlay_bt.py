"""Execution overlay on GIS conviction calls: monthly confirmation entry, stop-loss, re-entry.

All position returns are excess returns (pairs long-short; outright legs funded vs T-bills; FX incl. JPY carry).
Decision at a day's close applies from the next day's return (no look-ahead).
"""
import sys, os, json, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yahoo import fetch
from returns import build

PRICE_INDEX = {'^STOXX50E', '^N225', '^HSCE', '^GSPC'}
_TW = None
def leg_returns(t):
    global _TW
    if t.startswith('TW_'):
        if _TW is None: _TW = build()
        return _TW[t].pct_change()
    if t == 'JPYLONG':
        usdjpy = fetch('JPY=X')['close'].dropna()
        irx = fetch('^IRX')['close'].dropna().reindex(usdjpy.index).ffill() / 100
        jp = pd.Series(0.0, index=usdjpy.index)
        jp[jp.index >= '2024-03-19'] = 0.001; jp[jp.index >= '2024-07-31'] = 0.0025; jp[jp.index >= '2025-01-24'] = 0.005
        return (usdjpy.shift(1) / usdjpy - 1) - (irx - jp) / 252   # long JPY spot minus negative carry
    col = 'close' if (t in PRICE_INDEX or t.endswith('=X')) else 'adj'
    return fetch(t)[col].dropna().pct_change()

def position_returns(legs):
    rs = {t: leg_returns(t) for t in legs}
    df = pd.DataFrame(rs).dropna(how='all')
    df = df[df.index.dayofweek < 5].fillna(0.0)   # holidays in one market -> 0 return that day
    return sum(w * df[t] for t, w in legs.items())

def month_ends(idx):
    s = pd.Series(idx, index=idx)
    return set(s.groupby([idx.year, idx.month]).max())

def simulate(r, start, end, mode, sl=0.05, thr=0.0, lb=1):
    r = r.dropna()
    P = (1 + r).cumprod()
    me = sorted(d for d in month_ends(r.index))
    prev_me = {me[i]: me[i - lb] for i in range(lb, len(me))}
    days = r.loc[start:end].index
    held = pd.Series(0.0, index=days)   # exposure decided at close of day d (applies to d+1)
    trades = []; inpos = False; entry_P = None; entry_d = None; stopped_forever = False
    for i, d in enumerate(days):
        last = (i == len(days) - 1)
        if inpos:   # check exit conditions at this close
            cum = P[d] / entry_P - 1
            exit_reason = None
            if mode in ('naive_sl', 'confirm_sl_reentry', 'confirm_trail_reentry') and cum <= -sl: exit_reason = 'stop'
            if mode == 'confirm_trail_reentry':
                peak = P.loc[entry_d:d].max()
                if P[d] / peak - 1 <= -sl: exit_reason = 'trail stop'
            if mode == 'trend_monthly' and d in prev_me and (P[d] / P[prev_me[d]] - 1) <= thr: exit_reason = 'monthly reversal'
            if last: exit_reason = exit_reason or 'call ended'
            if exit_reason:
                trades.append(dict(entry=entry_d, exit=d, ret=cum, reason=exit_reason)); inpos = False
                if mode == 'naive_sl': stopped_forever = True
                held[d] = 0.0; continue
        if not inpos and not last and not stopped_forever:
            enter = False
            if mode in ('naive', 'naive_sl') and i == 0: enter = True
            elif mode in ('confirm', 'confirm_sl_reentry', 'confirm_trail_reentry', 'trend_monthly') and d in prev_me:
                if mode == 'confirm' and trades: enter = False
                else: enter = (P[d] / P[prev_me[d]] - 1) > thr
            if enter: inpos = True; entry_P = P[d]; entry_d = d
        held[d] = 1.0 if inpos else 0.0
    daily = held.shift(1).fillna(0.0) * r.loc[days]
    return daily, trades

def vol63(r, d):
    x = r.loc[:d].iloc[-64:-1]
    return x.std() * np.sqrt(252) if len(x) > 20 else np.nan

MODES = {'naive': 'Naive: hold the call', 'naive_sl': 'Naive + 5% stop, no re-entry (BCA style)', 'confirm': 'Monthly confirmation, then hold',
         'confirm_sl_reentry': 'Confirm + 5% stop + re-entry  [proposed]', 'confirm_trail_reentry': 'Confirm + 5% trailing stop + re-entry', 'trend_monthly': 'Monthly trend filter (in/out each month-end)'}

_cache = {}
def run_all(calls, sl=0.05, thr=0.0, target_vol=0.05, modes=MODES, lb=1, fixed_notional=0.05):
    per_call = []; port = {m: [] for m in modes}; trades_all = []
    for c in calls:
        r = _cache.setdefault(json.dumps(c['legs'], sort_keys=True), None)
        if r is None: r = _cache[json.dumps(c['legs'], sort_keys=True)] = position_returns(c['legs'])
        for m in modes:
            daily, trades = simulate(r, c['start'], c['end'], m, sl=sl, thr=thr, lb=lb)
            # vol-targeted notional fixed at each entry (trailing 63d vol at entry)
            notional = pd.Series(0.0, index=daily.index)
            for t in trades:
                v = vol63(r, t['entry'])
                n = (min(3.0, target_vol / v) if v and v > 0 else 1.0) if target_vol else fixed_notional
                notional.loc[t['entry']:t['exit']] = n
            port[m].append((notional.shift(1).fillna(0) * daily).rename(c['id']))
            tot = (1 + daily).prod() - 1
            eq = (1 + daily).cumprod(); dd = (eq / eq.cummax() - 1).min()
            per_call.append(dict(id=c['id'], name=c['name'], mode=m, total=tot, maxdd=dd, n_entries=len(trades), time_in=(daily != 0).mean(), win_entries=sum(t['ret'] > 0 for t in trades)))
            for t in trades: trades_all.append(dict(id=c['id'], mode=m, **t))
    P = {m: pd.concat(v, axis=1).astype(float).fillna(0.0).sum(axis=1) for m, v in port.items()}
    return pd.DataFrame(per_call), P, pd.DataFrame(trades_all)

def stats(x, start='2015-02-06', end='2025-08-04'):
    x = x.loc[start:end]; x = x[x.index.dayofweek < 5]
    yrs = len(x) / 252; cum = (1 + x).prod() - 1
    cagr = (1 + cum) ** (1 / yrs) - 1; vol = x.std() * np.sqrt(252)
    eq = (1 + x).cumprod(); dd = (eq / eq.cummax() - 1).min()
    return dict(cum_pct=100 * cum, cagr_pct=100 * cagr, vol_pct=100 * vol, sharpe=cagr / vol if vol else np.nan, maxdd_pct=100 * dd, calmar=cagr / -dd if dd < 0 else np.nan)

if __name__ == '__main__':
    calls = json.load(open('data/value_calls.json'))
    pc, P, T = run_all(calls)
    pc.to_csv('data/overlay_per_call.csv', index=False); T.to_csv('data/overlay_trades.csv', index=False)
    pd.DataFrame(P).to_csv('data/overlay_portfolio_daily.csv')
    print(pd.DataFrame({MODES[m]: stats(P[m]) for m in MODES}).T.round(2).to_string())
