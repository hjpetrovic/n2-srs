"""
Fetch English definitions for N2 vocabulary from Jisho API.
Saves progress incrementally — safe to interrupt and re-run.
Run with:  .venv/bin/python3 fetch_english.py
"""
import json, urllib.request, urllib.parse, time, sys

DATA_PATH = "n2_data.json"

def jisho_lookup(word):
    url = f"https://jisho.org/api/v1/search/words?keyword={urllib.parse.quote(word)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    results = data.get('data', [])
    if not results:
        return ''
    # Prefer result where Japanese slug exactly matches the word
    for result in results[:3]:
        jwords = result.get('japanese', [])
        if any(j.get('word') == word or j.get('reading') == word for j in jwords):
            senses = result.get('senses', [])
            if senses:
                return '; '.join(senses[0].get('english_definitions', []))
    # Fallback: first result
    senses = results[0].get('senses', [])
    return '; '.join(senses[0].get('english_definitions', [])) if senses else ''

with open(DATA_PATH, encoding="utf-8") as f:
    data = json.load(f)

vocab = data['vocabulary']
total = len(vocab)
missing = [v for v in vocab if not v['en']]
print(f"Total vocab: {total}  |  Need lookup: {len(missing)}")

errors = 0
for i, v in enumerate(missing):
    try:
        en = jisho_lookup(v['word'])
        v['en'] = en
        if i % 50 == 0 or i == len(missing) - 1:
            with open(DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            filled = sum(1 for x in vocab if x['en'])
            print(f"  [{i+1}/{len(missing)}] {v['word']} → {en[:40] if en else '(empty)'}   ({filled}/{total} filled)")
        else:
            sys.stdout.write(f"\r  {i+1}/{len(missing)} — {v['word'][:12]:<12}         ")
            sys.stdout.flush()
        time.sleep(0.25)
    except Exception as e:
        errors += 1
        print(f"\n  ERROR on {v['word']}: {e}")
        if errors > 10:
            print("Too many errors, saving and stopping.")
            break
        time.sleep(1)

# Final save
with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

filled = sum(1 for v in vocab if v['en'])
print(f"\nDone. {filled}/{total} words have English definitions.")
print("Run embed_data.py to rebuild n2_srs.html with updated definitions.")
