"""Extraction E1/E3 Espagne selon la Precision 22 (PAU generica, convocatoria Total, Ambos sexos).
Sorties : data/evidence_exams_international.csv (lignes ES), data/processed/exams_es_report.txt"""
import csv, gzip, io, os, urllib.request
R = "data/raw/exams/es/px_pau_matric_sexo_tot.csv"
U = "https://estadisticas.ciencia.gob.es/jaxiPx/files/_px/es/csv_bdsc/Universitaria/PAU/PAU/l0/"
U += "px_pau_matric_sexo_tot.csv_bdsc?nocab=1"
AG = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
if not os.path.exists(R):
    os.makedirs(os.path.dirname(R), exist_ok=True)
    b = urllib.request.urlopen(urllib.request.Request(U, headers={"User-Agent": AG, "Accept-Encoding": "identity"}), timeout=90).read()
    open(R, "wb").write(gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b)
t = open(R, "rb").read().decode("utf-8-sig", "replace")
V = {}
for r in list(csv.reader(io.StringIO(t), delimiter=";"))[1:]:
    if len(r) >= 6 and r[0].startswith("PAU gen") and r[1] == "Total" and r[2] == "Ambos sexos":
        V[(r[3], int(r[4]))] = float(r[5].replace(".", "").replace(",", "."))
yrs = sorted({y for (_, y) in V})
assert yrs and yrs[0] <= 2015 and yrs[-1] >= 2025, yrs
S = "Ministerio de Ciencia, Innovacion y Universidades, Estadistica de la PAU"
D1 = "PAU generica, convocatoria Total : Aprobados / Presentados"
D3 = "PAU generica, convocatoria Total : Presentados"
rows, rep = [], []
for y in yrs:
    a, p = V[("Aprobados", y)], V[("Presentados", y)]
    assert 0 < a <= p and a / p > 0.5, (y, a, p)
    rem = "conditions sanitaires" if y == 2020 else ""
    rows.append(["ES", y, "E1", round(100 * a / p, 4), D1, S, rem])
    rows.append(["ES", y, "E3", int(p), D3, S, rem])
    rep.append("ES %d presentes=%d aprobados=%d E1=%.3f" % (y, p, a, 100 * a / p))
out = "data/evidence_exams_international.csv"
old = [r for r in list(csv.reader(open(out, encoding="utf-8")))[1:] if r[0] != "ES"]
w = csv.writer(open(out, "w", newline="", encoding="utf-8"))
w.writerow(["pays", "annee", "indicateur", "valeur", "definition", "source", "remarque"])
w.writerows(old + rows)
open("data/processed/exams_es_report.txt", "w").write("\n".join(rep) + "\n")
print("\n".join(rep))
print("lignes ecrites : %d (ES), conservees : %d" % (len(rows), len(old)))
