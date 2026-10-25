"""Extraction E1/E3 Pologne (CKE) selon la Precision 19.
Sorties : data/evidence_exams_international.csv (lignes PL), data/processed/exams_pl_report.txt"""
import csv, os, re, urllib.parse, urllib.request
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
D = "data/raw/exams/pl/"
U21 = "http://cke.gov.pl/images/_EGZAMIN_MATURALNY_OD_2015/Informacje_o_wynikach/2021/sprawozdanie/"
U21 += "EM_Ogólne_sprawozdanie_2021.pdf"
NB = re.compile(r"^\d{1,3}(?: \d{3})+$")
def lignes(p):
    d = fz.open(p)
    L = []
    for pg in d:
        L += [x.replace("\xa0", " ").strip() for x in pg.get_text().split("\n") if x.strip()]
    return L
def lire(p):
    L = lignes(p)
    i = next(k for k, x in enumerate(L) if x.startswith("Tabela 1"))
    t = next(k for k in range(i, len(L)) if NB.match(L[k]))
    z = next(k for k in range(t, len(L) - 1) if re.match(r"^os.{1,4}, kt.{1,4}re zda", L[k] + " " + L[k + 1]))
    r = next(k for k in range(z, len(L)) if NB.match(L[k]))
    pct = L[r + 1] if r + 1 < len(L) else ""
    return int(L[t].replace(" ", "")), int(L[r].replace(" ", "")), pct
if not os.path.exists(D + "pl_2021.pdf"):
    try:
        rq = urllib.request.Request(urllib.parse.quote(U21, safe=":/%?&=@"), headers={"User-Agent": "Mozilla/5.0"})
        b = urllib.request.urlopen(rq, timeout=120).read()
        open(D + "pl_2021.pdf", "wb").write(b)
    except Exception as e:
        print("2021 non telecharge :", str(e)[:80])
rem = {2020: "conditions sanitaires", 2023: "tegoroczni absolwenci elargi aux absolvants anterieurs"}
rem[2024] = rem[2025] = rem[2023]
dfn = {"E1": "reussite / passage de tous les examens obligatoires, Tabela 1, Wszyscy zdajacy (CKE)",
       "E3": "passage de tous les examens obligatoires, Tabela 1 (CKE)"}
rows, rep = [], []
for y in range(2016, 2026):
    p = D + "pl_%d.pdf" % y
    try:
        tot, ok, pct = lire(p)
    except Exception as e:
        rep.append("PL %d ERREUR %s" % (y, str(e)[:70]))
        continue
    rep.append("PL %d total=%d reussis=%d E1=%.3f (source : %s)" % (y, tot, ok, 100 * ok / tot, pct))
    for ind, v in (("E1", round(100 * ok / tot, 4)), ("E3", tot)):
        rows.append(["PL", y, ind, v, dfn[ind], "CKE Informacja o wynikach egzaminu maturalnego", rem.get(y, "")])
out = "data/evidence_exams_international.csv"
old = []
if os.path.exists(out):
    old = [r for r in csv.reader(open(out, encoding="utf-8"))][1:]
    old = [r for r in old if r[0] != "PL"]
w = csv.writer(open(out, "w", newline="", encoding="utf-8"))
w.writerow(["pays", "annee", "indicateur", "valeur", "definition", "source", "remarque"])
w.writerows(old + rows)
open("data/processed/exams_pl_report.txt", "w").write("\n".join(rep) + "\n")
print("\n".join(rep))
print("lignes ecrites : %d (PL), conservees : %d" % (len(rows), len(old)))
