import sys, re
html, pois = sys.argv[1], sys.argv[2]
s = open(html, encoding="utf-8").read(); d = open(pois, encoding="utf-8").read().replace("</", "<\\/")
s = re.sub(r"/\*POIS\*/.*?/\*END\*/", lambda m: "/*POIS*/" + d + "/*END*/", s, flags=re.S)
open(html, "w", encoding="utf-8").write(s)
print("injected", len(d), "bytes")
