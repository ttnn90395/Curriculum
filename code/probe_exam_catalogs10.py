"""Sonde 10 : (a) contexte de la Tabela 1 du PDF polonais 2021 ; (b) structure de la table espagnole PAU (csv_bdsc).
Sortie : data/processed/probe_exam_catalogs10.txt"""
import csv, gzip, io, re, urllib.request
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
out = []
d = fz.open("data/raw/exams/pl/pl_2021.pdf")
L = [x.replace("\xa0", " ").strip() for pg in d for x in pg.get_text().split("\n") if x.strip()]
out.append("== PL 2021 : %d lignes" % len(L))
K = re.compile(r"^Tabela 1\b|^Liczba zdaj", re.I)
for k, x in enumerate(L):
    if K.search(x):
        out.append("  -- ligne %d" % k)
        out += ["  " + y[:110] for y in L[k:k + 34]]
        break
AG = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
u = "https://estadisticas.ciencia.gob.es/jaxiPx/files/_px/es/csv_bdsc/Universitaria/PAU/PAU/l0/px_pau_matric_sexo_tot.csv_bdsc?nocab=1"
b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": AG, "Accept-Encoding": "identity"}), timeout=90).read()
t = (gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b).decode("utf-8", "replace")
R = list(csv.reader(io.StringIO(t), delimiter=";"))
out.append("== ES : %d lignes, entete %s" % (len(R), R[0]))
for j in range(4):
    out.append("  %s : %s" % (R[0][j], sorted({r[j] for r in R[1:] if len(r) > j})[:12]))
S = {}
for r in R[1:]:
    if len(r) >= 6:
        S.setdefault((r[0], r[1], r[2], r[3]), []).append(r[4])
for k, v in sorted(S.items()):
    if k[2] == "Ambos sexos":
        out.append("  %s : %s-%s (%d periodes)" % ("|".join(k[:2] + k[3:]), min(v), max(v), len(v)))
open("data/processed/probe_exam_catalogs10.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
