import json, re, sys
MON = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
DATE = rf'{MON}\s*\d{{1,2}}/\d{{2,4}}|{MON}\s+\d{{4}}'
PNL = r'-?\d+(?:\.\d+)?\s*(?:%|BPS|bps)'
LEVEL = r'\$?-?[\d,]+(?:\.\d+)?\s*%?(?:\s*BPS)?'
ROW = re.compile(rf'^(?P<name>.+?)\s+(?P<level>{LEVEL})\s+(?P<open>{DATE})\s+(?P<close>{DATE})\s+(?P<pnl>{PNL})\s+(?P<type>Tactical|Strategic)\s*$', re.I)
def parse_date(s):
    import datetime
    s = s.strip().title()
    m = re.match(r'([A-Za-z]{3})[a-z]*\s*(\d{1,2})/(\d{2,4})$', s)
    if m:
        mon, d, y = m.groups(); y = int(y); y = y + 2000 if y < 100 else y
        return datetime.date(y, ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].index(mon[:3])+1, int(d)).isoformat()
    m = re.match(r'([A-Za-z]{3})[a-z]*\s+(\d{4})$', s)
    if m:
        mon, y = m.groups()
        return datetime.date(int(y), ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].index(mon[:3])+1, 15).isoformat() + '~'
    return None
def parse_lines(text):
    rows = []; buf = ''
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        cand = (buf + ' ' + line).strip() if buf else line
        m = ROW.match(cand)
        if m:
            d = m.groupdict(); rows.append(d); buf = ''
        else:
            # keep as potential prefix only if it looks like a trade name (uppercase start, no header words)
            if re.match(r'^(Long|Short|Overweight|Underweight|Buy|Sell)\b', line, re.I):
                buf = line
            elif buf and not re.search(r'INCEPTION|INITIATION|Copyright|AVERAGE|CUMULATIVE|TRADE ', line, re.I):
                buf = buf + ' ' + line
            else:
                buf = ''
    return rows
if __name__ == '__main__':
    pages = json.load(open(sys.argv[1]))['pages']
    text = '\n'.join(pages[int(i)] for i in sys.argv[2].split(','))
    rows = parse_lines(text)
    out = []
    for r in rows:
        pnl = r['pnl'].replace(' ', '')
        unit = 'bps' if 'bps' in pnl.lower() else '%'
        val = float(re.sub(r'[^0-9.\-]', '', pnl))
        out.append(dict(trade=re.sub(r'\*+$', '', r['name']).strip(), level=r['level'], open=parse_date(r['open']), close=parse_date(r['close']), pnl=val, unit=unit, type=r['type'].title()))
    json.dump(out, open(sys.argv[3], 'w'), indent=1)
    print(len(out))
    for o in out: print(o['open'], o['close'], f"{o['pnl']:>7}{o['unit']:<4}", o['type'][:5], o['trade'][:70])
