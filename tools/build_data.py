#!/usr/bin/env python3
"""
Turns the huge tossups.json (one JSON object per line) into small per-subject files
the game loads on demand.

  python3 tools/build_data.py path/to/tossups.json

Writes data/index.json plus one data/<category>-<subject>.json per subject.
Each file is {"0":[...],"1":[...],"2":[...],"3":[...]} = Rookie..Nationals tossups.
"""
import json, os, random, re, sys

CAP_MAIN, CAP_ALT = 100, 60   # tossups kept per subject per difficulty band
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
band = lambda d: 0 if d <= 3 else 1 if d <= 5 else 2 if d <= 7 else 3
nv = lambda v: v.get("$numberInt", v.get("$numberLong")) if isinstance(v, dict) else v

def main(src):
    random.seed(7)
    R = {}
    def push(key, b, it, cap):
        r = R.setdefault(key, {}).setdefault(b, [0, []])
        r[0] += 1
        if len(r[1]) < cap: r[1].append(it)
        else:
            j = random.randint(0, r[0] - 1)
            if j < cap: r[1][j] = it
    with open(src, encoding="utf-8") as f:
        for line in f:
            if "(*)" not in line or '"standard":true' not in line.replace(": ", ":"):
                continue
            try: o = json.loads(line)
            except Exception: continue
            q = re.sub(r"\s+", " ", (o.get("question_sanitized") or "").replace("(+)", " ").replace("(*)", " (*) ")).strip()
            try: d = int(nv(o.get("difficulty")))
            except Exception: continue
            if not o.get("answer") or not 40 <= len(q.split(" ")) <= 190 or d < 1: continue
            it = {"q": q, "r": o["answer"], "d": d,
                  "c": f"{(o.get('set') or {}).get('name','')} Pkt {nv((o.get('packet') or {}).get('name')) or '?'} Q{nv(o.get('number'))}"}
            b = band(d)
            push(f"{o['category']}|{o['subcategory']}", b, it, CAP_MAIN)
            if o.get("alternate_subcategory"):
                push(f"{o['category']}|{o['alternate_subcategory']}", b, it, CAP_ALT)
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT): os.remove(os.path.join(OUT, old))
    index = {}
    for key, bands in R.items():
        n = sum(len(v[1]) for v in bands.values())
        if n < 30: continue
        fn = re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-") + ".json"
        with open(os.path.join(OUT, fn), "w", encoding="utf-8") as g:
            json.dump({str(b): v[1] for b, v in sorted(bands.items())}, g, ensure_ascii=False, separators=(",", ":"))
        index[key] = {"n": n, "f": fn}
    with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as g:
        json.dump(index, g, ensure_ascii=False, separators=(",", ":"))
    print(len(index), "subjects,", sum(v["n"] for v in index.values()), "tossups")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "tossups.json")
