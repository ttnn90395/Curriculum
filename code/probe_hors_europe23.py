"""Sonde 23 (Amendement 26) : sources hors Europe, resultats a l'examen de fin de secondaire (E) et abandon en premiere annee (M).
Telecharge des pages et fichiers candidats, imprime taille, type, liens de donnees et contextes de mots-cles.
Aucune valeur n'est retenue ici. Sorties : data/raw/exams/hors_europe/*, data/processed/probe_hors_europe23.txt"""
import os, re, sys, urllib.request, urllib.parse
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
D = "data/raw/exams/hors_europe"
os.makedirs(D, exist_ok=True)
U = [
 ("AU", "https://www.education.gov.au/node/19501"),
 ("AU", "https://www.education.gov.au/higher-education-statistics/resources/2024-section-15-attrition-success-and-retention"),
 ("CA", "https://www150.statcan.gc.ca/n1/daily-quotidien/231219/dq231219g-eng.pdf"),
 ("CA", "https://www150.statcan.gc.ca/n1/daily-quotidien/220606/dq220606b-eng.pdf"),
 ("CA", "https://www150.statcan.gc.ca/n1/daily-quotidien/210609/dq210609d-eng.pdf"),
]
KW = re.compile(r"retention|attrition|persist|dropout|leav|first.year", re.I)
out = []
def pr(s=""):
    print(s); out.append(s)
for pays, u in U:
    nom = re.sub(r"[^A-Za-z0-9._-]", "_", u.split("//")[1])[-90:]
    p = os.path.join(D, pays + "_" + nom)
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=180)
        b = r.read(); ct = r.headers.get("Content-Type", "")
        open(p, "wb").write(b)
    except Exception as e:
        pr("== %s %s\n   ECHEC : %s" % (pays, u, str(e)[:150])); continue
    pr("== %s %s\n   %d octets ; %s" % (pays, u, len(b), ct))
    txt, links = "", []
    if b[:4] == b"%PDF":
        txt = " ".join(x for pg in fz.open(p) for x in pg.get_text().split())
    elif b[:2] == b"PK":
        pr("   fichier xlsx/zip : a lire a part (feuilles non listees ici)")
    else:
        h = b.decode("utf-8", "ignore")
        links = sorted(set(re.findall(r'href="([^"]+\.(?:csv|xlsx?|pdf|zip)[^"]*)"', h, re.I)))
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))
    for l in links[:12]:
        pr("   lien : " + urllib.parse.urljoin(u, l))
    n = 0
    for m in KW.finditer(txt):
        if n >= 5: break
        pr("   ..." + txt[max(0, m.start() - 90):m.end() + 130])
        n += 1
    pr("   mots-cles : %d contextes imprimes" % n)
os.makedirs("data/processed", exist_ok=True)
open("data/processed/probe_hors_europe23.txt", "w").write("\n".join(out) + "\n")
