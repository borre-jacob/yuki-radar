"""Fetch the latest Japan Avalanche Network (JAN) bulletin for each forecast area.

Usage: python3 tools/fetch_avalanche.py data/avalanche.json
Writes {areaId: {date, url, levels:[alpine, treeline, belowTreeline], advice, problems:[...], summary:{...}}}.
Levels: 0 = no rating, 1 = low ... 5 = extreme.
"""
import html, json, re, subprocess, sys, time

AREAS = [2, 3, 4, 6, 7, 1]  # Hakuba, Myoko, Kagura/Tanigawa/Hotaka, SW Hokkaido, Central Hokkaido, Tateyama
BASE = "https://data.nadare.jp"
LEVEL = {"No rating": 0, "Low": 1, "Moderate": 2, "Considerable": 3, "High": 4, "Extreme": 5}
UA = "YukiRadar/1.0 (personal ski trip app; github.com/borre-jacob/yuki-radar)"


def get(url):
    # curl instead of urllib: works the same on macOS and on GitHub Actions
    r = subprocess.run(["curl", "-sSfL", "-m", "30", "-A", UA, url], capture_output=True, check=True)
    return r.stdout.decode("utf-8")


def lines(page):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)
    t = re.sub(r'<img[^>]*alt="([^"]+)"[^>]*>', r"\n[IMG:\1]\n", t)
    return [l.strip() for l in html.unescape(re.sub(r"<[^>]+>", "\n", t)).split("\n") if l.strip()]


def section(L, start, stops):
    if start not in L:
        return []
    out = []
    for l in L[L.index(start) + 1:]:
        if l in stops:
            break
        out.append(l)
    return out


def latest(area):
    page = get(f"{BASE}/avalanche_informations?area_id={area}&locale=en")
    row = re.search(r'href="/avalanche_informations/(\d+)">\s*([\d/]+ [\d:]+)\s*</a>.*?<td>([^<]+)</td>(.*?)</tr>', page, re.S)
    if not row:
        return None
    bid, date, name, cells = row.groups()
    levels = [LEVEL.get(a, 0) for a in re.findall(r'alt="([^"]+)"', cells)][:3]

    L = lines(get(f"{BASE}/avalanche_informations/{bid}?locale=en"))
    advice = " ".join(section(L, "Travel and Terrain Advice", {"Avalanche Problem", "概要"}))
    problems, cur = [], None
    for l in section(L, "Avalanche Problem", {"概要"}):
        if l.startswith("[IMG:"):
            continue
        if cur is None or (cur.get("text") is not None):
            # A short line without a full stop starts a new problem; the next line is its description
            if len(l) < 40 and not l.endswith("."):
                cur = {"name": l, "text": None}
                problems.append(cur)
                continue
        if cur is not None and cur["text"] is None:
            cur["text"] = l
    summary = {k: " ".join(section(L, k, {"Avalanche", "Snowpack", "Weather", "Print/PDF"})) for k in ("Avalanche", "Snowpack", "Weather")}
    return {"name": name.strip(), "date": date.replace("/", "-"), "url": f"{BASE}/avalanche_informations/{bid}?locale=en",
            "levels": levels, "advice": advice, "problems": problems, "summary": summary}


def main(out):
    result = {}
    for a in AREAS:
        try:
            b = latest(a)
            if b:
                result[str(a)] = b
                print(a, b["name"], b["date"], b["levels"], len(b["problems"]), "problems", file=sys.stderr)
        except Exception as e:  # keep the other areas if one fails
            print(a, "failed:", e, file=sys.stderr)
        time.sleep(1)
    result["_fetched"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    json.dump(result, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv[1])
