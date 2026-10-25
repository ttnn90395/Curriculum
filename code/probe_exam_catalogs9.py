"""Sonde 9 : (a) PDF polonais 2021-2022 ; (b) export des tables PxWeb espagnoles ; (c) DK, NO, SE, mots-cles larges.
Sortie : data/processed/probe_exam_catalogs9.txt"""
import gzip, json, re, urllib.parse, urllib.request
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
AG = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
UA = {"User-Agent": AG, "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
      "Accept-Language": "en", "Accept-Encoding": "identity"}
out = []
def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90)
    b = r.read()
    return (gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b).decode("utf-8", "replace")
def lignes(y):
    d = fz.open("data/raw/exams/pl/pl_%d.pdf" % y)
    out.append("== PL %d : %d pages" % (y, len(d)))
    return [x.replace("\xa0", " ").strip() for pg in d for x in pg.get_text().split("\n") if x.strip()]
L = lignes(2022)
i = next((k for k, x in enumerate(L) if x.startswith("Tabela 1")), None)
out += ["  " + x[:110] for x in L[i:i + 46]] if i is not None else ["  Tabela 1 absente"]
L = lignes(2021)
K = re.compile(r"^Tabela|zda[lł]|przyst[aą]pi", re.I)
out += ["  " + x[:130] for x in [y for y in L if K.search(y)][:16]]
B = "https://estadisticas.ciencia.gob.es/jaxiPx/"
T = "Universitaria/PAU/PAU/l0/px_pau_matric_sexo_tot"
U = [B + "files/_px/es/csv_bdsc/" + T + ".csv_bdsc?nocab=1", B + "files/_px/es/csv_sc/" + T + ".csv_sc?nocab=1",
     B + "files/_px/es/px/" + T + ".px?nocab=1", B + "files/_px/es/xlsx/" + T + ".xlsx?nocab=1",
     B + "dlgExport.htm?path=/Universitaria/PAU/PAU/l0/&file=px_pau_matric_sexo_tot.px"]
for u in U:
    out.append("== ES %s" % u[len(B):][:95])
    try:
        t = get(u)
        out.append("  %d car." % len(t))
        if "dlgExport" in u:
            out += ["  form : " + x[:150] for x in re.findall(r"<form[^>]*>", t)[:3]]
            out += ["  input : " + x[:120] for x in re.findall(r"<input[^>]*>", t)[:14]]
        else:
            out += ["  " + x[:150] for x in t.split("\n")[:8]]
    except Exception as e:
        out.append("  ERREUR %s" % str(e)[:80])
W = re.compile(r"complet|dropout|drop-out|grade|mark|pass|exam|studentereks|certificate|diploma|leaving|result", re.I)
out.append("== DK (periode debut <= 2012, fin >= 2022)")
try:
    for t in json.loads(get("https://api.statbank.dk/v1/tables?lang=en&format=JSON")):
        if W.search(t.get("text", "")) and str(t.get("firstPeriod"))[:4] <= "2012" and str(t.get("latestPeriod"))[:4] >= "2022":
            out.append("  %s | %s | %s-%s" % (t["id"], t["text"][:70], t["firstPeriod"], t["latestPeriod"]))
except Exception as e:
    out.append("  ERREUR %s" % str(e)[:90])
out.append("== NO (requetes)")
for q in ("completion%20rates", "examination%20results", "final%20exams", "grades%20upper%20secondary"):
    try:
        j = json.loads(get("https://data.ssb.no/api/pxwebapi/v2/tables?lang=en&pageSize=25&query=" + q))
        E = j.get("tables", [])
        if E and q == "completion%20rates":
            out.append("  cles : %s" % list(E[0])[:12])
        for x in E:
            out.append("  %s | %s | %s-%s" % (x.get("id"), str(x.get("label"))[:62], x.get("firstPeriod"), x.get("lastPeriod")))
    except Exception as e:
        out.append("  ERREUR %s %s" % (q, str(e)[:60]))
out.append("== SE (sous-arbres UF)")
for n in ("UF0550", "UF0549", "UF0507", "UF0521"):
    try:
        for m in json.loads(get("https://api.scb.se/OV0104/v1/doris/en/ssd/UF/" + n))[:14]:
            out.append("  %s/%s | %s | %s" % (n, m["id"], m["text"][:62], m.get("type")))
    except Exception as e:
        out.append("  ERREUR %s %s" % (n, str(e)[:60]))
open("data/processed/probe_exam_catalogs9.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
