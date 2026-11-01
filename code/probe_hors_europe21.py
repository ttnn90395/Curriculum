"""Sonde 21 (Amendement 26) : relecture locale des fichiers deja telecharges (sans reseau), autour des chiffres cibles.
Aucune valeur n'est retenue ici. Sorties : data/processed/probe_hors_europe21.txt"""
import glob, html, os, re
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
D = "data/raw/exams/hors_europe"
CIB = [
 ("NZ_NCEA", "NZ_*Six-indicators*", r"Merit or Excellence|endorse|per ?cent|\d+(?:\.\d+)? ?%", 40),
 ("ACT_2022", "US_*R2134*", r"3\.17|3\.36|3\.0\d|average HSGPA|mean HSGPA|Table 2|Figure 2|Figure 3", 40),
 ("NCES_311_33", "US_*dt23_311.33*", r"returning|retention|persist", 30),
 ("NCES_326_30", "US_*dt22_326.30*", r"[Rr]etention|[Pp]ersist|[Rr]eturn|Percent", 30),
]
out = []
def pr(s=""):
    print(s); out.append(s)
for nom, g, pat, cap in CIB:
    F = glob.glob(os.path.join(D, g))
    if not F:
        pr("== %s : fichier absent (%s)" % (nom, g)); continue
    p = F[0]
    b = open(p, "rb").read()
    if b[:4] == b"%PDF":
        L = [x.strip() for pg in fz.open(p) for x in pg.get_text().split("\n") if x.strip()]
    else:
        t = html.unescape(re.sub(r"<[^>]+>", "\n", b.decode("utf-8", "ignore")).replace("&nbsp;", " "))
        L = [re.sub(r"\s+", " ", x).strip() for x in t.split("\n") if x.strip()]
    pr("== %s : %d lignes (%s)" % (nom, len(L), os.path.basename(p)))
    R = re.compile(pat); n = 0; last = -99
    for i, x in enumerate(L):
        if R.search(x) and i > last + 3:
            pr("   [%d] " % i + " | ".join(L[max(0, i - 2):i + 5])[:330]); n += 1; last = i
            if n >= cap: break
os.makedirs("data/processed", exist_ok=True)
open("data/processed/probe_hors_europe21.txt", "w").write("\n".join(out) + "\n")
