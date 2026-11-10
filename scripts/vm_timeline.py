import json, pandas as pd
num = json.load(open('data/vm_numeric_raw.json')); gr = json.load(open('data/vm_graph_raw.json'))
recs = []
for d, nid, out, st in num:
    if not out: continue
    for k, v in out.items():
        for col, hz in (('3-Month','tac'), ('12-Month','cyc'), ('10-Year','sec'), ('MQ','mq')):
            if col in v and v[col]['cur']: recs.append(dict(date=d, key=k, hz=hz, r=v[col]['cur'], src='numeric'))
for d, nid, out, st in gr:
    if not out: continue
    for k, v in out.items():
        for col, hz in (('1-3M','tac'), ('6-12M','cyc')):
            if col in v and len(v[col]) == 1: recs.append(dict(date=d, key=k, hz=hz, r=v[col][0], src='graphic'))
df = pd.DataFrame(recs); df['date'] = pd.to_datetime(df['date'])
df = df.drop_duplicates(['date','key','hz'], keep='last')
df.to_csv('data/vm_ratings_long.csv', index=False)
piv = df[df.hz=='cyc'].pivot_table(index='date', columns='key', values='r')
print(df.groupby(['src','hz']).size())
print(piv[['AA:Equities','AA:Fixed Income','AA:Cash','EQ:US','FI:Duration','FX:USD']].resample('QE').last().to_string())
