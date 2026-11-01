"""Sonde 22 : lignes de valeurs de la table NCES 326.30 (retention des entrants de premiere annee), lecture locale.
Aucune valeur n'est retenue. Sortie : data/processed/probe_hors_europe22.txt"""
import glob, html, re
b = open(glob.glob("data/raw/exams/hors_europe/US_*dt22_326.30*")[0], "rb").read().decode("utf-8", "ignore")
t = html.unescape(re.sub(r"<[^>]+>", "\n", b).replace("&nbsp;", " "))
L = [re.sub(r"\s+", " ", x).strip() for x in t.split("\n") if x.strip()]
i0 = next(i for i, x in enumerate(L) if x.startswith("Percent of first-time undergraduates"))
out = ["lignes %d a %d de la table :" % (i0, i0 + 140)] + ["  [%d] %s" % (i, L[i][:140]) for i in range(i0, min(len(L), i0 + 140))]
open("data/processed/probe_hors_europe22.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
