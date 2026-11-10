import os
import pickle, sys, requests, time
ck = os.path.join(os.environ.get('BCA_WORKDIR', '.'), 'web', 'cookies.pkl')
s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
s.cookies.update(pickle.load(open(ck,'rb')))
def get(url, **kw):
    if url.startswith('/'): url = 'https://www.bcaresearch.com' + url
    for i in range(3):
        try:
            r = s.get(url, timeout=60, **kw)
            return r
        except Exception as e:
            time.sleep(2**i)
    raise
if __name__ == '__main__':
    r = get(sys.argv[1])
    print(r.status_code, r.url, len(r.content), r.headers.get('content-type'))
    open(sys.argv[2], 'wb').write(r.content)
