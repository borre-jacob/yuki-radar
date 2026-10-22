import json, re, sys, subprocess, time, math
html = open(sys.argv[1], encoding="utf-8").read()
resorts = [(i, float(a), float(b)) for i, a, b in re.findall(r'\{id:"(\w+)",name:"[^"]+",jp:"[^"]*",region:"[^"]+",lat:([\d.]+),lon:([\d.]+)', html)]
KINDS = "chair_lift|gondola|cable_car|mixed_lift|drag_lift|t-bar|j-bar|platter|rope_tow|magic_carpet"
q = "[out:json][timeout:170];(" + "".join(f'way["aerialway"~"^({KINDS})$"](around:7000,{la},{lo});' for _, la, lo in resorts) + ");out geom tags;"
for attempt in range(5):
    url = ["https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass-api.de/api/interpreter"][attempt % 2]
    r = subprocess.run(["curl", "-s", "-m", "200", "-A", "YukiRadar/1.0 (personal ski trip planner)", url, "--data-urlencode", "data=" + q], capture_output=True, text=True)
    try: data = json.loads(r.stdout); break
    except Exception: print("retry", r.stdout[:80], file=sys.stderr); time.sleep(15)
else: sys.exit("failed")
def dist(a, b, c, d):
    t = math.radians; h = math.sin(t(c-a)/2)**2 + math.cos(t(a))*math.cos(t(c))*math.sin(t(d-b)/2)**2
    return 2*6371*math.asin(math.sqrt(h))
out = {i: [] for i, _, _ in resorts}
for w in data["elements"]:
    g = w.get("geometry") or []
    if len(g) < 2: continue
    t = w.get("tags", {})
    pts = [[round(p["lat"], 5), round(p["lon"], 5)] for p in g]
    name = t.get("name:en") or t.get("name") or ""
    mid = pts[len(pts)//2]
    for rid, la, lo in resorts:
        if dist(la, lo, mid[0], mid[1]) <= 7.5:
            out[rid].append([t["aerialway"], name, pts])
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, separators=(",", ":"))
print(len(data["elements"]), "liftar totalt;", {k: len(v) for k, v in out.items()})
