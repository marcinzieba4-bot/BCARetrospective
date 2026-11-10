import os
import sys, pandas as pd, numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from yahoo import fetch
def tr(t, col='adj'): return fetch(t)[col].dropna()
def build():
    px = {}
    for t in ['ACWI','SPY','EZU','EWU','EWC','EWA','EWJ','EEM','AGG','BNDX','IEF','TLT','BIL','SHY','LQD','HYG','TIP','GOVT','CEW','GLD','DBB','BZ=F','IXP','RXI','KXI','IXC','IXG','IXJ','EXI','IXN','MXI','REET','JXI']:
        px[t] = tr(t)
    fx = {k: fetch(t)['close'].dropna() for k, t in [('EURUSD','EURUSD=X'),('GBPUSD','GBPUSD=X'),('USDCHF','CHF=X'),('USDJPY','JPY=X'),('USDCAD','CAD=X'),('AUDUSD','AUDUSD=X')]}
    fx['DXY'] = fetch('DX-Y.NYB')['close'].dropna()
    P = pd.DataFrame(px).ffill()
    F = pd.DataFrame(fx).ffill()
    P = P.join(F, how='left').ffill()
    P = P[P.index >= '2016-01-01']
    # value of 1 unit of each currency in USD
    ccy = pd.DataFrame({'USD': 1.0, 'EUR': P.EURUSD, 'GBP': P.GBPUSD, 'CHF': 1 / P.USDCHF, 'JPY': 1 / P.USDJPY, 'CAD': 1 / P.USDCAD, 'AUD': P.AUDUSD}, index=P.index)
    lc = np.log(ccy)
    # trade-weighted proxy: currency vs equal-weight basket of the other 6 (log space)
    tw = pd.DataFrame({c: lc[c] - lc.drop(columns=c).mean(axis=1) for c in lc.columns})
    TW = np.exp(tw)
    P['FI'] = np.exp(0.5 * np.log(P.AGG / P.AGG.iloc[0]) + 0.5 * np.log(P.BNDX / P.BNDX.iloc[0]))
    for c in TW: P['TW_' + c] = TW[c]
    return P
# key -> (asset series, benchmark series or None for absolute vs cash)
MAP = {
 'AA:Equities': ('ACWI', 'BAL'), 'AA:Fixed Income': ('FI', 'BAL'), 'AA:Cash': ('BIL', 'BAL'),
 'EQ:US': ('SPY','ACWI'), 'EQ:Euro Area': ('EZU','ACWI'), 'EQ:UK': ('EWU','ACWI'), 'EQ:Canada': ('EWC','ACWI'), 'EQ:Australia': ('EWA','ACWI'), 'EQ:Japan': ('EWJ','ACWI'), 'EQ:EM': ('EEM','ACWI'),
 'FI:Government': ('GOVT','AGG'), 'FI:Investment Grade': ('LQD','AGG'), 'FI:High Yield': ('HYG','AGG'), 'FI:Duration': ('IEF','BIL'), 'FI:Inflation Protection': ('TIP','IEF'),
 'FX:USD': ('TW_USD', None), 'FX:EUR': ('TW_EUR', None), 'FX:GBP': ('TW_GBP', None), 'FX:CHF': ('TW_CHF', None), 'FX:JPY': ('TW_JPY', None), 'FX:CAD': ('TW_CAD', None), 'FX:AUD': ('TW_AUD', None), 'FX:EM Currencies': ('CEW','BIL'),
 'CMD:Energy': ('BZ=F','BIL'), 'CMD:Base/Bulk Metals': ('DBB','BIL'), 'CMD:Gold': ('GLD','BIL'),
 'SEC:Communication Services': ('IXP','ACWI'), 'SEC:Consumer Discretionary': ('RXI','ACWI'), 'SEC:Consumer Staples': ('KXI','ACWI'), 'SEC:Energy': ('IXC','ACWI'), 'SEC:Financials': ('IXG','ACWI'), 'SEC:Health Care': ('IXJ','ACWI'), 'SEC:Industrials': ('EXI','ACWI'), 'SEC:Information Technology': ('IXN','ACWI'), 'SEC:Materials': ('MXI','ACWI'), 'SEC:Real Estate': ('REET','ACWI'), 'SEC:Utilities': ('JXI','ACWI'),
}
