"""Precision 31 (Amendement 26) : transcription controlee de series hors Europe, depuis les PDF deja telecharges.
Sorties : data/evidence_hors_europe_E.csv, data/processed/hors_europe_E.txt"""
import csv, glob, re
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
D = "data/raw/exams/hors_europe/"
def texte(g):
    f = glob.glob(D + g)
    if not f: return None
    return " ".join(x for pg in fz.open(f[0]) for x in pg.get_text().split())
NZ = {
 "NCEA niveau 3 (Year 13)": "51.0 51.4 52.2 53.9 55.4 56.7 59.8 62.6 64.2 65.5 66.1 67.3 72.1 70.5 68.2 67.7",
 "NCEA niveau 2 (Year 12)": "60.9 61.7 63.9 66.2 67.8 71.3 75.0 76.3 78.4 78.5 77.6 77.5 80.1 77.9 74.9 73.2",
 "NCEA niveau 1 (Year 11)": "57.5 60.6 62.8 63.4 65.4 69.9 72.4 74.5 75.3 75.0 72.4 70.6 71.8 69.2 64.9 61.7",
}
US = ("GPA cumulatif ajuste (ACT)", [2010, 2012, 2014, 2016, 2018, 2020, 2021], "3.17 3.20 3.21 3.22 3.26 3.31 3.36")
PH = ["0.10 standard deviation units", "0.29 standard deviation units",
      "did not increase while HSGPA did"]
rows, rep = [], []
T = texte("NZ_*Six-indicators*")
for nom, s in NZ.items():
    v = s.split()
    ok = T is not None and re.search(r"\s+".join(re.escape(x + "%") for x in v), T) is not None
    rep.append("NZ %s : %s" % (nom, "verifie" if ok else "ABSENT"))
    for a, x in zip(range(2008, 2024), v):
        rows.append(["NZ", nom, a, x if ok else "", "NZQA six indicators 2024", "verifie" if ok else "absent"])
T = texte("US_*R2134*")
nom, ans, s = US
v = s.split()
ok = T is not None and re.search(r"\s+".join(re.escape(x) for x in v), T) is not None
rep.append("US %s : %s" % (nom, "verifie" if ok else "ABSENT"))
for a, x in zip(ans, v):
    rows.append(["US", nom, a, x if ok else "", "ACT R2134 figure 6", "verifie" if ok else "absent"])
for p in PH:
    ok = T is not None and p in T
    rep.append("US phrase '%s' : %s" % (p, "retrouvee" if ok else "ABSENTE"))
w = csv.writer(open("data/evidence_hors_europe_E.csv", "w", newline="", encoding="utf-8"))
w.writerow(["pays", "indicateur", "annee", "valeur", "source", "statut"]); w.writerows(rows)
open("data/processed/hors_europe_E.txt", "w").write("\n".join(rep) + "\n")
print("\n".join(rep))
