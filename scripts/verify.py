import os
import sys, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from yahoo import fetch
def px(t, d, col='close'):
    s = fetch(t)[col].dropna(); d = pd.Timestamp(d)
    s = s[s.index <= d + pd.Timedelta(days=0)]
    return s.iloc[-1]
def ratio(a, b, d, col='adj'): return px(a, d, col) / px(b, d, col)
# (label, open, close, reported%, fn(date)->level, direction)
checks = [
 ('Short Gold (stop)', '2014-12-10','2015-01-23', -5.0, lambda d: px('GC=F',d), -1),
 ('Long Gold (stop)', '2015-02-06','2015-03-09', -5.0, lambda d: px('GC=F',d), 1),
 ('Short NASDAQ100 fut', '2015-11-06','2016-01-20', 16.2, lambda d: px('^NDX',d), -1),
 ('Short EUR/JPY', '2015-06-01','2016-06-16', 19.4, lambda d: px('EURJPY=X',d), -1),
 ('Short S&P500', '2017-05-04','2017-06-15', -2.0, lambda d: px('^GSPC',d), -1),
 ('Long GBP/JPY', '2016-08-11','2017-08-03', 9.9, lambda d: px('GBPUSD=X',d)*px('JPY=X',d), 1),
 ('Long Brent', '2017-05-04','2017-09-21', 13.8, lambda d: px('BZ=F',d), 1),
 ('Short S&P500', '2017-11-16','2017-11-30', -2.0, lambda d: px('^GSPC',d), -1),
 ('Long Glob Industrials/Utilities', '2017-09-29','2018-02-01', 12.0, lambda d: ratio('EXI','JXI',d), 1),
 ('Long S&P500/Short HY', '2018-01-11','2018-02-15', -5.0, lambda d: ratio('SPY','HYG',d), 1),
 ('Short AUD/JPY', '2018-02-01','2019-01-07', 10.0, lambda d: px('AUDUSD=X',d)*px('JPY=X',d), -1),
 ('Long USD/CNY', '2018-09-20','2019-04-18', -3.1, lambda d: px('CNY=X',d), 1),
 ('Long DXY', '2014-10-31','2019-04-18', 16.4, lambda d: px('DX-Y.NYB',d), 1),
 ('Long EA banks', '2019-04-25','2019-05-22', -7.0, lambda d: px('EUFN',d,'adj'), 1),
 ('Short S&P500', '2019-05-10','2019-06-20', -3.8, lambda d: px('^GSPC',d), -1),
 ('Long EUR/JPY', '2019-04-18','2019-08-01', -5.0, lambda d: px('EURJPY=X',d), 1),
 ('Long EA banks', '2019-06-28','2019-08-13', -10.0, lambda d: px('EUFN',d,'adj'), 1),
 ('Long Gold', '2019-04-17','2019-08-29', 20.5, lambda d: px('GC=F',d), 1),
 ('Long Greek stocks', '2015-01-30','2015-03-09', 15.0, None, 1),
]
rows = []
for lab, o, c, rep, f, sgn in checks:
    if f is None: continue
    a, b = f(o), f(c)
    ours = sgn * (b / a - 1) * 100 if sgn > 0 else (a / b - 1) * 100 * 1  # short: inverse return approx
    ours = sgn * (b / a - 1) * 100
    rows.append((lab, o, c, rep, round(ours, 1), round(ours - rep, 1)))
df = pd.DataFrame(rows, columns=['trade','open','close','reported%','ours%','diff'])
print(df.to_string(index=False))
print('sign agreement', (df['reported%'].apply(lambda x: x>0) == df['ours%'].apply(lambda x: x>0)).mean())
