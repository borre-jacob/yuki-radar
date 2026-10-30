import sys, re
# Usage: python3 tools/inject_lifts.py index.html data/osm/lifts.json
h, j = sys.argv[1], sys.argv[2]
s = open(h, encoding="utf-8").read(); d = open(j, encoding="utf-8").read().replace("</", "<\\/")
s = re.sub(r"/\*LIFTS\*/.*?/\*ENDLIFTS\*/", lambda m: "/*LIFTS*/" + d + "/*ENDLIFTS*/", s, flags=re.S)
open(h, "w", encoding="utf-8").write(s); print("lifts injected", len(d))
