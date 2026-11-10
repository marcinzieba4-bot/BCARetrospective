import requests, json, os, sys, time, urllib.parse
import pandas as pd
D = os.path.join(os.environ.get('BCA_WORKDIR', '.'), 'px')
S = requests.Session(); S.headers['User-Agent'] = 'Mozilla/5.0'
def fetch(t, start='2007-01-01'):
    fn = os.path.join(D, t.replace('^','_').replace('=','_') + '.csv')
    if os.path.exists(fn):
        return pd.read_csv(fn, index_col=0, parse_dates=True)
    p1 = int(pd.Timestamp(start).timestamp()); p2 = int(time.time())
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(t)}?period1={p1}&period2={p2}&interval=1d&events=div,split'
    for i in range(4):
        r = S.get(url, timeout=60)
        if r.status_code == 200: break
        time.sleep(2**i)
    j = r.json()['chart']['result'][0]
    ts = pd.to_datetime(j['timestamp'], unit='s').normalize()
    q = j['indicators']['quote'][0]
    adj = j['indicators'].get('adjclose', [{}])[0].get('adjclose', q['close'])
    df = pd.DataFrame({'close': q['close'], 'adj': adj}, index=ts)
    df = df[~df.index.duplicated(keep='last')].dropna(how='all')
    df.to_csv(fn)
    return df
if __name__ == '__main__':
    ok = []; bad = []
    for t in sys.argv[1:]:
        try:
            df = fetch(t); ok.append(f'{t}:{df.index[0].date()}')
        except Exception as e:
            bad.append(f'{t}:{type(e).__name__}')
        time.sleep(0.3)
    print('OK', ' '.join(ok)); print('BAD', bad)
