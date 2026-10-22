import json, sys
pois = json.load(open(sys.argv[1])); el = json.load(open(sys.argv[2]))["elements"]
idx = {}
for e in el:
    t = e.get("tags", {}); la = e.get("lat") or e.get("center", {}).get("lat"); lo = e.get("lon") or e.get("center", {}).get("lon")
    if la is None: continue
    web = t.get("website") or t.get("contact:website") or t.get("url") or t.get("contact:facebook") or t.get("contact:instagram") or ""
    if web and not web.startswith("http"): web = "https://" + web.lstrip("/")
    if not web.startswith("https://") and not web.startswith("http://"): web = ""
    phone = (t.get("phone") or t.get("contact:phone") or "").split(";")[0].strip()
    idx[(round(la, 5), round(lo, 5))] = (web, phone)
hit = tot = 0
for rid, rows in pois.items():
    for r in rows:
        while len(r) < 10: r.append("")
        if r[0] != "onsen": continue
        tot += 1
        c = idx.get((r[3], r[4]))
        if c: r[8], r[9] = c; hit += 1
json.dump(pois, open(sys.argv[1], "w"), ensure_ascii=False, separators=(",", ":"))
print(f"{hit} av {tot} onsen-rader fick kontaktuppgifter")
for rid in ["happo", "nozawa", "akakura"]:
    print(rid, sum(1 for r in pois[rid] if r[0]=="onsen" and (r[8] or r[9])), "/", sum(1 for r in pois[rid] if r[0]=="onsen"))
