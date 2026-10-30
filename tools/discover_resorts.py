"""Find ski resorts in Norway, Sweden and Finland from OpenStreetMap.

Usage: python3 tools/discover_resorts.py data/osm/scandinavia.json data/osm/scandinavia_found.json

A resort is a named ski area (landuse=winter_sports) with lifts. Each lift is assigned to the
nearest named ski area within 2.5 km. Base/top come from the lowest/highest lift station
(Open-Meteo elevation data). Small hills are dropped: at least 150 m vertical or 4 lifts.
Areas within 3 km of a resort already in data/osm/scandinavia.json are skipped.
"""
import json, math, subprocess, sys, time

UA = "YukiRadar/1.0 (personal ski trip app; github.com/borre-jacob/yuki-radar)"
OVERPASS = ["https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass-api.de/api/interpreter"]
KINDS = "chair_lift|gondola|cable_car|mixed_lift|drag_lift|t-bar|j-bar|platter"
COUNTRIES = {"NO": "Norge", "SE": "Sverige", "FI": "Finland"}


def curl(url, data=None):
    cmd = ["curl", "-sS", "-m", "300", "-A", UA, url]
    if data:
        cmd += ["--data-urlencode", "data=" + data]
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def overpass(q):
    for attempt in range(6):
        try:
            return json.loads(curl(OVERPASS[attempt % 2], q))["elements"]
        except Exception:
            print("overpass retry", attempt, file=sys.stderr)
            time.sleep(15 * (attempt + 1))
    raise SystemExit("Overpass failed")


def km(a, b, c, d):
    t = math.radians
    h = math.sin(t(c - a) / 2) ** 2 + math.cos(t(a)) * math.cos(t(c)) * math.sin(t(d - b) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def elevations(points):
    out = []
    for i in range(0, len(points), 100):
        chunk = points[i:i + 100]
        url = ("https://api.open-meteo.com/v1/elevation?latitude=" + ",".join(f"{p[0]:.5f}" for p in chunk)
               + "&longitude=" + ",".join(f"{p[1]:.5f}" for p in chunk))
        for attempt in range(8):
            data = json.loads(curl(url) or "{}")
            if "elevation" in data:
                out += data["elevation"]
                break
            time.sleep(5 * (attempt + 1))
        else:
            raise SystemExit("elevation API failed")
        time.sleep(1.2)
    return out


existing = json.load(open(sys.argv[1], encoding="utf-8"))
areas_q = "[out:json][timeout:280];(" + "".join(
    f'area["ISO3166-1"="{c}"][admin_level=2]->.c{c};nwr["landuse"="winter_sports"]["name"](area.c{c});' for c in COUNTRIES) + ");out center tags;"
lifts_q = "[out:json][timeout:280];(" + "".join(
    f'area["ISO3166-1"="{c}"][admin_level=2]->.c{c};way["aerialway"~"^({KINDS})$"](area.c{c});' for c in COUNTRIES) + ");out geom;"

areas = []
for e in overpass(areas_q):
    c = e.get("center") or e
    if "lat" in c:
        areas.append({"name": e["tags"]["name"], "lat": c["lat"], "lon": c["lon"], "lifts": []})
print(len(areas), "named ski areas", file=sys.stderr)
lifts = [w["geometry"] for w in overpass(lifts_q) if len(w.get("geometry", [])) >= 2]
print(len(lifts), "lifts", file=sys.stderr)

for g in lifts:
    m = g[len(g) // 2]
    best = min(areas, key=lambda a: km(a["lat"], a["lon"], m["lat"], m["lon"]), default=None)
    if best and km(best["lat"], best["lon"], m["lat"], m["lon"]) <= 2.5:
        best["lifts"].append(g)

# Several OSM areas can share a name (e.g. two slopes of one resort): merge same-name areas within 5 km
merged = []
for a in sorted((a for a in areas if a["lifts"]), key=lambda a: -len(a["lifts"])):
    twin = next((b for b in merged if b["name"] == a["name"] and km(a["lat"], a["lon"], b["lat"], b["lon"]) < 5), None)
    if twin:
        twin["lifts"] += a["lifts"]
    else:
        merged.append(a)

found = []
for a in merged:
    ends = [(g[0]["lat"], g[0]["lon"]) for g in a["lifts"]] + [(g[-1]["lat"], g[-1]["lon"]) for g in a["lifts"]]
    lat, lon = sum(p[0] for p in ends) / len(ends), sum(p[1] for p in ends) / len(ends)
    if any(km(lat, lon, r["lat"], r["lon"]) < 3 for r in existing + found):
        continue
    a.update(lat=round(lat, 3), lon=round(lon, 3), ends=ends, liftCount=len(a["lifts"]))
    found.append(a)
print(len(found), "new candidate areas, fetching elevations", file=sys.stderr)

flat = [p for a in found for p in a["ends"]]
el = iter(elevations(flat))
out = []
for a in found:
    e = [next(el) for _ in a["ends"]]
    base, top = int(round(min(e), -1)), int(round(max(e), -1))
    if top - base < 150 and a["liftCount"] < 4:
        continue
    out.append({"name": a["name"], "lat": a["lat"], "lon": a["lon"], "base": base, "top": top, "liftCount": a["liftCount"]})
out.sort(key=lambda r: -(r["top"] - r["base"]))
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "resorts kept", file=sys.stderr)
