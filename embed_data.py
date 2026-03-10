"""
Rebuilds n2_srs.html with the latest n2_data.json.
Run after fetch_english.py to bake updated definitions into the app.
"""
import json, re

with open("n2_srs.html", encoding="utf-8") as f:
    html = f.read()

with open("n2_data.json", encoding="utf-8") as f:
    data = json.load(f)

n2_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
html = re.sub(r'const N2_DATA = \{.*?\};', 'const N2_DATA = ' + n2_json + ';', html, flags=re.DOTALL)

with open("n2_srs.html", "w", encoding="utf-8") as f:
    f.write(html)

filled = sum(1 for v in data['vocabulary'] if v['en'])
print(f"Rebuilt n2_srs.html  ({filled}/{len(data['vocabulary'])} vocab have English)")
