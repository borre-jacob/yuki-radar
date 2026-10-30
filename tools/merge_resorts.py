"""Merge discovered resorts into data/osm/scandinavia.json and give every resort its county.

Usage: python3 tools/merge_resorts.py data/osm/scandinavia.json data/osm/scandinavia_found.json data/scandinavia_extra.json
Every row gets: id, name, country (Sverige/Norge/Finland), region (county, from Nominatim), lat, lon, base, top.
"""
import json, re, subprocess, sys, time, unicodedata

UA = "YukiRadar/1.0 (personal ski trip app; github.com/borre-jacob/yuki-radar)"
COUNTRY = {"no": "Norge", "se": "Sverige", "fi": "Finland"}
SKIP = re.compile(r"hopp|skiklubb", re.I)


def slug(name):
    s = unicodedata.normalize("NFKD", name.lower().replace("ø", "o").replace("æ", "ae"))
    s = re.sub(r"[^a-z0-9]+", "", s.encode("ascii", "ignore").decode())
    return s[:24] or "resort"


def county(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&zoom=8&format=json&accept-language=sv"
    for attempt in range(4):
        try:
            d = json.loads(subprocess.run(["curl", "-sS", "-m", "30", "-A", UA, url], capture_output=True, text=True).stdout)
            a = d.get("address", {})
            time.sleep(1.2)  # Nominatim allows one request per second
            return COUNTRY.get(a.get("country_code")), re.sub(r"s? län$| fylke$", "", a.get("state") or a.get("county") or a.get("region") or "")
        except Exception:
            time.sleep(5)
    return None, ""


rows = json.load(open(sys.argv[1], encoding="utf-8"))
for r in rows:
    r.setdefault("country", r["region"])
new = [r for r in json.load(open(sys.argv[2], encoding="utf-8")) if not SKIP.search(r["name"])]
new += json.load(open(sys.argv[3], encoding="utf-8"))
ids = {r["id"] for r in rows}
for r in new:
    name = r["name"].title() if r["name"].isupper() else r["name"]
    i = base = slug(name)
    n = 2
    while i in ids:
        i, n = f"{base}{n}", n + 1
    ids.add(i)
    rows.append({"id": i, "name": name, "lat": r["lat"], "lon": r["lon"], "base": r["base"], "top": r["top"]})

for r in rows:
    c, reg = county(r["lat"], r["lon"])
    r["country"] = c or r.get("country")
    r["region"] = reg or r["country"]
    print(r["id"], r["country"], r["region"], file=sys.stderr)

order = {"Sverige": 0, "Norge": 1, "Finland": 2}
rows.sort(key=lambda r: (order.get(r["country"], 9), r["region"], r["name"]))
json.dump(rows, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(rows), "resorts", file=sys.stderr)
