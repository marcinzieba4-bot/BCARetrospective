import os, re, pickle, sys, requests
from bs4 import BeautifulSoup
OUT = sys.argv[1]
s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
r = s.get('https://www.bcaresearch.com/user/login', allow_redirects=True)
soup = BeautifulSoup(r.text, 'lxml')
state = soup.find('input', {'name': 'state'})['value']
data = {'state': state, 'username': os.environ['BCA_USER'], 'password': os.environ['BCA_Pass'], 'action': 'default'}
r2 = s.post(r.url, data=data, allow_redirects=True)
print('post', r2.status_code, r2.url.split('?')[0])
f = BeautifulSoup(r2.text, 'lxml').find('form')
fd = {i.get('name'): i.get('value') for i in f.find_all('input') if i.get('name')}
r3 = s.post(f['action'], data=fd, allow_redirects=True)
print('saml', r3.status_code, r3.url)
for h in r3.history: print('  hop', h.status_code, h.url)
print('cookies:', sorted({c.domain + ':' + c.name for c in s.cookies}))
pickle.dump(s.cookies, open(OUT, 'wb'))
open(OUT + '.html', 'w').write(r3.text)
t = BeautifulSoup(r3.text, 'lxml')
print('title', t.title.get_text(strip=True) if t.title else None)
print('logout link present:', 'logout' in r3.text.lower())
