"""Sonde 20 (Amendement 26) : lecture des PDF et tables hors Europe retenus apres la sonde 19.
Imprime les lignes de chaque document contenant des annees et des taux ou des moyennes. Aucune valeur n'est retenue.
Sorties : data/raw/exams/hors_europe/*, data/processed/probe_hors_europe20.txt"""
import os, re, urllib.request
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
D = "data/raw/exams/hors_europe"
os.makedirs(D, exist_ok=True)
U = [
 ("NZ", "https://www2.nzqa.govt.nz/assets/About-us/Publications/Insights-papers/NCEA-Achievement-Six-indicators-showing-change-over-time.pdf", r"Achieved|Merit|Excellence|attainment|indicator|20[012]\d"),
 ("US", "https://www.act.org/content/dam/act/unsecured/documents/2022/R2134-Grade-Inflation-Continues-to-Grow-in-the-Past-Decade-Final-Accessible.pdf", r"HSGPA|GPA|20[12]\d"),
 ("US", "https://nces.ed.gov/programs/digest/d22/tables/dt22_326.30.asp", r"retention|20[012]\d"),
 ("US", "https://nces.ed.gov/programs/digest/d23/tables/dt23_311.33.asp", r"retention|20[012]\d"),
]
out = []
def pr(s=""):
    print(s); out.append(s)
for pays, u, pat in U:
    p = os.path.join(D, pays + "_" + re.sub(r"[^A-Za-z0-9._-]", "_", u.split("//")[1])[-80:])
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read()
        open(p, "wb").write(b)
    except Exception as e:
        pr("== %s %s\n   ECHEC : %s" % (pays, u, str(e)[:150])); continue
    if b[:4] == b"%PDF":
        lines = [x.strip() for pg in fz.open(p) for x in pg.get_text().split("\n") if x.strip()]
    else:
        h = b.decode("utf-8", "ignore")
        lines = [x.strip() for x in re.sub(r"<[^>]+>", "\n", h).split("\n") if x.strip()]
    pr("== %s %s : %d lignes" % (pays, u[-60:], len(lines)))
    R = re.compile(pat, re.I); n = 0
    for x in lines:
        if R.search(x) and re.search(r"\d", x) and len(x) < 200:
            pr("   " + x); n += 1
            if n >= 60: break
os.makedirs("data/processed", exist_ok=True)
open("data/processed/probe_hors_europe20.txt", "w").write("\n".join(out) + "\n")
