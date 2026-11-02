#!/usr/bin/env python3
"""Reads the user's project list (xlsx, sheet 'Все проекты') and writes cores/xlsx_items.json.
Only the standard library is used; the workbook is treated as untrusted data.
usage: import_xlsx.py FPGA_MiSTer_MISTang_all_projects.xlsx cores/xlsx_items.json"""
import zipfile, re, html, json, sys
z = zipfile.ZipFile(sys.argv[1])
x = z.read('xl/worksheets/sheet1.xml').decode()
rows = []
for r in re.findall(r'<x:row\b.*?</x:row>', x, re.S):
    row = {}
    for a, b in re.findall(r'<x:c\b([^>]*?)(?:/>|>(.*?)</x:c>)', r, re.S):
        ref = re.search(r'r="([A-Z]+)\d+"', a).group(1)
        t = ''.join(re.findall(r'<x:t[^>]*>(.*?)</x:t>', b or '', re.S)); v = re.search(r'<x:v>(.*?)</x:v>', b or '', re.S)
        val = html.unescape(t if t else (v.group(1) if v else ''))
        if val: row[ref] = val
    rows.append(row)
items = [dict(name=r['B'], group=r.get('C', ''), kind=r.get('D', ''), status=r.get('E', ''), url=r.get('F', ''),
              url_kind=r.get('G', ''), origin=r.get('H', '')) for r in rows[1:] if r.get('B')]
json.dump(items, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
print(len(items), 'items')
