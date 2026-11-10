import os
import json, re, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from parse_ledger import parse_date
MON = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?'
DATE = rf'{MON}\s*\d{{1,2}}\s*/\s*\d{{2,4}}|{MON}\s+\d{{4}}'
RET = r'-?\$?[\d,]+(?:\.\d+)?\s*(?:%|BPS|bps|Bps)|\.\.\.|N/A'
LEVEL = r'\$?-?[\d,]+(?:\.\d+)?\s*(?:%|BPS|bps|Bps)?'
TAIL = re.compile(rf'\s(?P<level>{LEVEL})\s+(?P<date>{DATE})\s+(?P<ret>{RET})', re.I)
START = re.compile(r'\b(Long(?!-term)|Short|Overweight|Underweight|MacroQuant|Buy|Sell)\b')
SECTION = re.compile(r'(Tactical Trades|Strategic Recommendations|Special Trade Recommendations|Trades Closed In|Closed Trades)', re.I)
def page_kind(p):
    ks = set(m.group(1).lower() for m in SECTION.finditer(p))
    return ks
def snap(page):
    t = re.sub(r'\s+', ' ', page.replace('￾', '-').replace('￾', ''))
    out = []; prev_end = 0
    for m in TAIL.finditer(t):
        seg = t[prev_end:m.start()]
        # name starts at first START keyword in segment
        sm = START.search(seg)
        name = seg[sm.start():].strip() if sm else seg.strip()[-80:]
        out.append(dict(name=name, level=m.group('level').strip(), init=parse_date(re.sub(r'\s+',' ',m.group('date'))), ret=m.group('ret').replace(' ','')))
        prev_end = m.end()
    return out
if __name__ == '__main__':
    pages = json.load(open(sys.argv[1]))['pages']
    for i in sys.argv[2].split(','):
        for r in snap(pages[int(i)]): print(r)
