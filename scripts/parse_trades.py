import sys, re
from bs4 import BeautifulSoup
def parse(h):
    s=BeautifulSoup(h,'lxml')
    out=[]
    # find table rows
    for tr in s.select('table tbody tr'):
        cells=[td.get_text(' | ',strip=True) for td in tr.find_all('td', recursive=False)]
        if cells: out.append(cells)
    return s,out
if __name__=='__main__':
    s,out=parse(open(sys.argv[1]).read())
    print('rows',len(out))
    for r in out[:int(sys.argv[2]) if len(sys.argv)>2 else 5]: print(r)
    for a in s.find_all('a',href=True):
        if 'page=' in a['href']: print('PAGER', a['href'], a.get_text(strip=True))
