import sys, re
# Usage: python3 tools/inject_avalanche.py index.html data/avalanche.json
h, j = sys.argv[1], sys.argv[2]
s = open(h, encoding="utf-8").read(); d = open(j, encoding="utf-8").read().replace("</", "<\\/")
s, n = re.subn(r"/\*AVALANCHE\*/.*?/\*ENDAVALANCHE\*/", lambda m: "/*AVALANCHE*/" + d + "/*ENDAVALANCHE*/", s, flags=re.S)
assert n == 1, "placeholder not found"
open(h, "w", encoding="utf-8").write(s); print("avalanche injected", len(d))
