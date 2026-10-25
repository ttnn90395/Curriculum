"""Extraction E1/E2/E3 France selon la Precision 21, a partir des fichiers DEPP deja dans le depot (sans reseau).
Sorties : data/evidence_exams_international.csv (lignes FR), data/processed/exams_fr_report.txt"""
import csv, os
R = list(csv.DictReader(open("data/evidence_bac_reussite_ensemble.csv", encoding="utf-8")))
M = list(csv.DictReader(open("data/evidence_bac_mentions_academie.csv", encoding="utf-8")))
rem = {2020: "controle continu integral (conditions sanitaires)", 2021: "reforme du bac, controle continu a 40 %"}
S = "DEPP data.education.gouv.fr"
D1 = "taux_ensemble : admis / presents, toutes voies (age = Ensemble)"
D3 = "presents derives : admis_ensemble / taux_ensemble"
D2 = "mention tres bien (avec ou sans felicitations) / admis, toutes voies"
rows, rep = [], []
for r in R:
    y = int(r["annee"])
    if y < 2010:
        continue
    t, a = float(r["taux_ensemble"]), float(r["admis_ensemble"])
    assert 40 < t < 100, "taux hors plage %s %s" % (y, t)
    rows.append(["FR", y, "E1", round(t, 4), D1, S, rem.get(y, "")])
    rows.append(["FR", y, "E3", round(a / (t / 100)), D3, S, rem.get(y, "")])
    rep.append("FR %d E1=%.2f admis=%d presents derives=%d" % (y, t, a, round(a / (t / 100))))
voies = sorted({m["voie"] for m in M})
rep.append("voies presentes dans le fichier des mentions : %s" % voies)
tot = {}
for m in M:
    if m["voie"].strip().lower() in ("ensemble", "total"):
        continue
    d = tot.setdefault(int(m["session"]), [0.0, 0.0])
    d[0] += float(m["admis"] or 0)
    d[1] += float(m["tb_felicitations"] or 0) + float(m["tb"] or 0)
for y in sorted(tot):
    adm, tb = tot[y]
    rep.append("FR %d E2 (TB / admis) = %.3f  admis=%d tb=%d" % (y, 100 * tb / adm, adm, tb))
    rows.append(["FR", y, "E2", round(100 * tb / adm, 4), D2, S, rem.get(y, "")])
out = "data/evidence_exams_international.csv"
old = []
if os.path.exists(out):
    old = [r for r in csv.reader(open(out, encoding="utf-8"))][1:]
    old = [r for r in old if r[0] != "FR"]
w = csv.writer(open(out, "w", newline="", encoding="utf-8"))
w.writerow(["pays", "annee", "indicateur", "valeur", "definition", "source", "remarque"])
w.writerows(old + rows)
open("data/processed/exams_fr_report.txt", "w").write("\n".join(rep) + "\n")
print("\n".join(rep))
print("lignes ecrites : %d (FR), conservees : %d" % (len(rows), len(old)))
