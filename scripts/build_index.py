"""Build per-report index + text caches from downloaded HTML (raw/) and PDFs (pdf/).

Outputs: pdftxt/<nid>.json (PDF page texts), txt/<nid>.txt (HTML main text),
web/index.json (date, slug, trade-table pages), web/vm_reports.json, web/vm_graph_reports.json.
Run from the working directory after list_reports.py, download.py and pdf_dl.py.
"""
import gzip, json, os, re, glob
import pypdfium2 as pdfium
from bs4 import BeautifulSoup

os.makedirs('pdftxt', exist_ok=True); os.makedirs('txt', exist_ok=True)
for fn in sorted(glob.glob('pdf/*.pdf')):
    nid = os.path.basename(fn)[:-4]
    out = f'pdftxt/{nid}.json'
    if os.path.exists(out): continue
    pdf = pdfium.PdfDocument(fn)
    pages = [pdf[i].get_textpage().get_text_range() for i in range(len(pdf))]
    pdf.close()
    json.dump({'nid': nid, 'pages': pages}, open(out, 'w'))

lst = json.load(open('web/berezin_global.json'))
idx, vm, vmg = [], [], []
for p in lst:
    nid = p.split('/')[-1]
    m = re.search(r'-(\d{2})-(\d{2})-(\d{4})/\d+$', p)
    d = f'{m.group(3)}-{m.group(2)}-{m.group(1)}'
    tfn = f'txt/{nid}.txt'
    if not os.path.exists(tfn):
        s = BeautifulSoup(gzip.open(f'raw/{nid}.html.gz', 'rt').read(), 'lxml')
        t = (s.find('main') or s).get_text('\n', strip=True)
        for cut in ['Footnotes\nInsert footnotes', 'Questions about this report?', 'Recommended for you']:
            i = t.find(cut)
            if i > 0: t = t[:i]
        open(tfn, 'w').write(t)
    has = os.path.exists(f'pdftxt/{nid}.json'); tp = []
    if has:
        pages = json.load(open(f'pdftxt/{nid}.json'))['pages']
        tp = [i for i, pg in enumerate(pages) if re.search(r'Closed In \d{4}|Tactical Trades|Closed Trades|Strategic Recommendations', pg, re.I)]
        n = [i for i, pg in enumerate(pages) if 'Global Asset Allocation' in pg and '12-Month' in pg]
        g = [i for i, pg in enumerate(pages) if '6-To-12 Month' in pg and 'Global Asset Allocation' in pg]
        if n: vm.append((d, nid, n[0]))
        if g: vmg.append((d, nid, g[0]))
    idx.append(dict(nid=nid, date=d, slug=p.split('/')[2], pdf=has, trade_pages=tp))
idx.sort(key=lambda x: x['date'])
json.dump(idx, open('web/index.json', 'w'), indent=0)
json.dump(sorted(vm), open('web/vm_reports.json', 'w'))
json.dump(sorted(vmg), open('web/vm_graph_reports.json', 'w'))
print(len(idx), 'reports;', len(vm), 'numeric matrices;', len(vmg), 'graphical matrices')
