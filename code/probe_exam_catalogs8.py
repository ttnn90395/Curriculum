"""Sonde 8 : catalogues des offices statistiques DK, NO, SE ; nouvel essai du site irlandais (SEC).
Sortie : data/processed/probe_exam_catalogs8.txt"""
import gzip, json, re, urllib.parse, urllib.request
AG = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
UA = {"User-Agent": AG, "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
      "Accept-Language": "en", "Accept-Encoding": "identity"}
def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90)
    b = r.read()
    return (gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b).decode("utf-8", "replace")
K = re.compile(r"upper secondary|gymnas|examination|exam|graduat|certificate|grade", re.I)
out = []
out.append("== DK catalogue")
try:
    T = json.loads(get("https://api.statbank.dk/v1/tables?lang=en&format=JSON"))
    S = [t for t in T if K.search(t.get("text", ""))]
    out.append("  %d tables sur %d" % (len(S), len(T)))
    for t in S[:45]:
        p = "%s-%s" % (t.get("firstPeriod"), t.get("latestPeriod"))
        out.append("  %s | %s | %s" % (t["id"], t["text"][:75], p))
except Exception as e:
    out.append("  ERREUR %s" % str(e)[:90])
out.append("== NO catalogue")
for u in ("https://data.ssb.no/api/pxwebapi/v2/tables?lang=en&pageSize=40&query=upper%20secondary",
          "https://data.ssb.no/api/v0/en/table/?query=upper%20secondary"):
    try:
        t = get(u)
        j = json.loads(t)
        L = j.get("tables", j if isinstance(j, list) else [])
        out.append("  OK %s : %d entrees" % (u[-60:], len(L)))
        for x in L[:30]:
            out.append("  %s | %s | %s" % (x.get("id"), str(x.get("label", x.get("title")))[:75], x.get("lastPeriod", "")))
        break
    except Exception as e:
        out.append("  ERREUR %s : %s" % (u[-50:], str(e)[:70]))
out.append("== SE catalogue UF")
try:
    B = "https://api.scb.se/OV0104/v1/doris/en/ssd/UF"
    for n in json.loads(get(B)):
        out.append("  %s | %s" % (n["id"], n["text"][:70]))
        if K.search(n["text"]) or n["id"] in ("UF0506", "UF0505", "UF0536"):
            try:
                for m in json.loads(get(B + "/" + n["id"]))[:12]:
                    out.append("      %s | %s | %s" % (m["id"], m["text"][:60], m.get("type")))
            except Exception as e:
                out.append("      ERREUR %s" % str(e)[:50])
except Exception as e:
    out.append("  ERREUR %s" % str(e)[:90])
out.append("== IE SEC (en-tetes navigateur)")
try:
    t = get("https://www.examinations.ie/statistics/")
    L = sorted(set(re.findall(r'href="([^"#]+\.(?:xlsx?|pdf|csv))"', t, re.I)))
    out.append("  %d car., %d fichiers" % (len(t), len(L)))
    out += ["  " + x[:150] for x in L[:30]]
except Exception as e:
    out.append("  ERREUR %s" % str(e)[:90])
open("data/processed/probe_exam_catalogs8.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
