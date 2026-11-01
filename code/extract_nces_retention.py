"""Precision 32 (Amendement 26) : retention des entrants americains (NCES 326.30), controle de chaine dans la page locale.
Sorties : data/evidence_nces_retention.csv, data/processed/nces_retention.txt"""
import csv, glob, html, re
b = open(glob.glob("data/raw/exams/hors_europe/US_*dt22_326.30*")[0], "rb").read().decode("utf-8", "ignore")
t = html.unescape(re.sub(r"<[^>]+>", "\n", b).replace("&nbsp;", " "))
T = " ".join(x.strip() for x in t.split("\n") if x.strip())
C = [2006, 2009, 2016, 2017, 2018, 2019, 2020]
V = "71.0 71.9 75.5 75.6 76.2 75.9 75.7".split()
ok = re.search(r"Full-time students All institutions(?: [\d,]+){14} " + r" ".join(re.escape(v) for v in V), T) is not None
rows = [["US", c, v if ok else "", "NCES Digest 2022 table 326.30", "verifie" if ok else "absent"] for c, v in zip(C, V)]
w = csv.writer(open("data/evidence_nces_retention.csv", "w", newline="", encoding="utf-8"))
w.writerow(["pays", "cohorte_entree", "retention_pct", "source", "statut"]); w.writerows(rows)
msg = "US retention temps plein, tous etablissements : %s" % ("verifie (" + " ".join(V) + ")" if ok else "ABSENT")
open("data/processed/nces_retention.txt", "w").write(msg + "\n"); print(msg)
