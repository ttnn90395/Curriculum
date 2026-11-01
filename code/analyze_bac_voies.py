"""Taux de reussite au bac par voie (Precision 24), depuis les fichiers DEPP du depot (sans reseau).
Sorties : data/processed/bac_voies.txt, data/processed/bac_voies.csv"""
import csv
R = list(csv.DictReader(open("data/evidence_bac_reussite_ensemble.csv", encoding="utf-8")))
M = list(csv.DictReader(open("data/evidence_bac_mentions_academie.csv", encoding="utf-8")))
V = {"general": "taux_general", "techno": "taux_techno", "pro": "taux_pro", "ensemble": "taux_ensemble"}
S = {k: {} for k in V}
for r in R:
    y = int(r["annee"])
    for k, c in V.items():
        if r.get(c, "").strip() not in ("", "nan"):
            S[k][y] = float(r[c])
out, tab = [], []
yrs = sorted({y for k in S for y in S[k] if y >= 2010})
out.append("E1 (taux de reussite, %) par voie :")
out.append("  annee   " + "  ".join("%8s" % k for k in V))
for y in yrs:
    out.append("  %d   " % y + "  ".join("%8s" % ("%.1f" % S[k][y] if y in S[k] else "-") for k in V))
    for k in V:
        if y in S[k]:
            tab.append([k, y, "E1", S[k][y]])
out.append("")
out.append("Variations E1 (points de pourcentage) :")
for k in V:
    z = max(S[k]) if S[k] else None
    for nom, a, b in (("2010->2019", 2010, 2019), ("2019->derniere", 2019, z)):
        ok = a in S[k] and b in S[k]
        out.append("  %-8s %-15s %s" % (k, nom if nom != "2019->derniere" else "2019->%s" % z,
                                       "%+.2f" % (S[k][b] - S[k][a]) if ok else "non calculee"))
nm = {"BAC GENERAL": "general", "BAC TECHNOLOGIQUE": "techno", "BAC PROFESSIONNEL": "pro"}
T = {}
for m in M:
    v = nm.get(m["voie"].strip().upper())
    if not v:
        continue
    d = T.setdefault((int(m["session"]), v), [0.0, 0.0])
    d[0] += float(m["admis"] or 0)
    d[1] += float(m["tb_felicitations"] or 0) + float(m["tb"] or 0)
ses = sorted({s for s, _ in T})
out.append("")
out.append("E2 (mention Tres bien / admis, %) et part de la voie parmi les admis (%) :")
for s in ses:
    tot = sum(T[(s, v)][0] for v in nm.values() if (s, v) in T)
    cell = []
    for v in ("general", "techno", "pro"):
        if (s, v) in T and T[(s, v)][0] > 0:
            a, t = T[(s, v)]
            cell.append("%s E2 %.2f part %.1f" % (v, 100 * t / a, 100 * a / tot))
            tab.append([v, s, "E2", round(100 * t / a, 4)])
            tab.append([v, s, "part_admis", round(100 * a / tot, 4)])
    out.append("  %d : %s" % (s, " ; ".join(cell)))
w = csv.writer(open("data/processed/bac_voies.csv", "w", newline=""))
w.writerow(["voie", "annee", "indicateur", "valeur"])
w.writerows(tab)
open("data/processed/bac_voies.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
