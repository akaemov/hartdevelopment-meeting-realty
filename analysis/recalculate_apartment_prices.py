"""Check published aggregates; optionally reproduce them from the user's XLSX.

The original registry is deliberately not included in the public repository.
Python 3 standard library only. This script never prints individual records.
"""
import argparse,hashlib,json,math,statistics,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

parser=argparse.ArgumentParser();parser.add_argument('--registry',type=Path);args=parser.parse_args()
root=Path(__file__).resolve().parents[1];d=json.loads((root/'data/apartment_price_comparison.json').read_text())
for project,v in d['projects'].items():
    assert sum(x['count'] for x in v['buckets'])==v['n']
    assert math.isclose(sum(x['share'] for x in v['buckets']),1,abs_tol=1e-10)
    assert v['min']<=v['q1']<=v['median']<=v['q3']<=v['max']
    assert math.isclose(max(.201*v['median'],v['median']-6000000),v['mortgage_scenario']['median_own_money'],abs_tol=.01)
assert sum(x['n'] for x in d['projects'].values())==d['filters']['apartments_used']
if args.registry:
    assert hashlib.sha256(args.registry.read_bytes()).hexdigest()==d['source']['sha256'],'Registry differs from the analyzed snapshot'
    ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(args.registry) as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            strings=[''.join(t.text or '' for t in si.findall('.//x:t',ns)) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('x:si',ns)]
        book=ET.fromstring(z.read('xl/workbook.xml'));relations={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheets={}
        for sheet in book.find('x:sheets',ns):
            rid=sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'];target=relations[rid];path=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            rows=[]
            for row in ET.fromstring(z.read(path)).findall('.//x:sheetData/x:row',ns):
                cells={}
                for cell in row:
                    col=''.join(c for c in cell.attrib['r'] if c.isalpha());typ=cell.attrib.get('t');v=cell.find('x:v',ns)
                    if typ=='inlineStr':value=''.join(t.text or '' for t in cell.findall('.//x:t',ns))
                    elif typ=='s':value=strings[int(v.text)]
                    elif v is not None:value=float(v.text) if typ not in ['str','e'] else v.text
                    else:value=None
                    cells[col]=value
                rows.append(tuple(cells.get(c) for c in 'ABCDEFG'))
            sheets[sheet.attrib['name']]=rows
    assert sheets['Помещения']==sheets['Не нужно']
    free=[r for r in sheets['Помещения'][1:] if r[5]=='Квартира' and r[4]=='Свободно']
    for project,v in d['projects'].items():
        prices=sorted(r[1] for r in free if r[6]==project);q=statistics.quantiles(prices,n=4,method='inclusive')
        assert len(prices)==v['n']
        for expected,actual in zip([v['min'],v['q1'],v['median'],v['q3'],v['max']],[min(prices),q[0],statistics.median(prices),q[2],max(prices)]):assert math.isclose(expected,actual,abs_tol=.01)
        for row in d['budget_comparison']:assert sum(p<=row['price'] for p in prices)==row['hart_apartments_at_or_below'][project]
    print('Aggregates reproduced from the exact supplied snapshot. No individual rows printed.')
else:print('Aggregate invariants passed. To verify against source, add --registry /path/to/original.xlsx')
