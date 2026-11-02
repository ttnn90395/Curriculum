"""Sonde 24 (Amendement 26) : tableaux Statistique Canada de persistance et diplomation (enquete 5017, tableaux 37-10-013x a 0146).
Telecharge les csv complets, imprime titre, colonnes et valeurs distinctes des dimensions. Aucune valeur de taux n'est imprimee.
Sorties : data/raw/exams/hors_europe/CA_*.csv, data/processed/probe_canada24.txt"""
import csv, io, os, urllib.request, zipfile
D = "data/raw/exams/hors_europe"
os.makedirs(D, exist_ok=True)
T = ["37100136", "37100138", "37100139", "37100140", "37100143", "37100145", "37100146"]
out = []
def pr(s=""):
    print(s); out.append(s)
for t in T:
    u = "https://www150.statcan.gc.ca/n1/tbl/csv/%s-eng.zip" % t
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read()
        z = zipfile.ZipFile(io.BytesIO(b))
        nom = [n for n in z.namelist() if n.endswith(".csv") and "MetaData" not in n][0]
        raw = z.read(nom)
        open(os.path.join(D, "CA_%s.csv" % t), "wb").write(raw)
        R = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig", "ignore"))))
    except Exception as e:
        pr("== %s ECHEC : %s" % (t, str(e)[:160])); continue
    pr("== %s : %d lignes ; colonnes %s" % (t, len(R), list(R[0].keys())))
    for c in R[0].keys():
        if c in ("VALUE", "SYMBOL", "STATUS", "TERMINATED", "DECIMALS", "VECTOR", "COORDINATE", "UOM_ID", "SCALAR_ID", "SCALAR_FACTOR"): continue
        V = sorted(set(r[c] for r in R))
        pr("   %s : %d valeurs ; %s" % (c, len(V), [v[:60] for v in V[:14]]))
os.makedirs("data/processed", exist_ok=True)
open("data/processed/probe_canada24.txt", "w").write("\n".join(out) + "\n")
