"""Analyses A et B de l'Amendement 17, mises en oeuvre selon la Precision 21, sur data/evidence_exams_international.csv.
Sorties : data/processed/exams_analysis_A.txt, data/processed/exams_analysis_A.csv"""
import csv
V = {}
for r in csv.DictReader(open("data/evidence_exams_international.csv", encoding="utf-8")):
    V[(r["pays"], r["indicateur"], int(r["annee"]))] = float(r["valeur"])
pays = sorted({k[0] for k in V})
START = {"PL": 2016}
def derniere(p, ind):
    ys = [k[2] for k in V if k[0] == p and k[1] == ind]
    return max(ys) if ys else None
out = []
for ind in ("E1", "E2"):
    out.append("Valeurs %s (annee : valeur) pour les annees 2010, 2012, 2016, 2018, 2019, 2020, 2021, derniere :" % ind)
    for p in pays:
        ys = sorted(k[2] for k in V if k[0] == p and k[1] == ind)
        if not ys:
            out.append("  %s : non realise" % p)
            continue
        sel = [y for y in (2010, 2012, 2016, 2018, 2019, 2020, 2021) if y in ys] + [ys[-1]]
        out.append("  %s : %s" % (p, " ; ".join("%d : %.2f" % (y, V[(p, ind, y)]) for y in sorted(set(sel)))))
D = []
for ind in ("E1", "E2"):
    for p in pays:
        a, b = START.get(p, 2010), 2019
        z = derniere(p, ind)
        if z is None:
            continue
        for nom, y0, y1 in (("W1", a, b), ("W2", b, z)):
            k0, k1 = (p, ind, y0), (p, ind, y1)
            if k0 in V and k1 in V:
                D.append([p, ind, nom, y0, y1, round(V[k1] - V[k0], 3)])
            else:
                D.append([p, ind, nom, y0, y1, None])
out.append("")
out.append("Variations (points de pourcentage) :")
for d in D:
    out.append("  %s %s %s %d->%d : %s" % (d[0], d[1], d[2], d[3], d[4], "non calculee" if d[5] is None else "%+.2f" % d[5]))
out.append("")
out.append("Lecture France (Precision 21) :")
for ind in ("E1", "E2"):
    for nom in ("W1", "W2"):
        f = [d for d in D if d[0] == "FR" and d[1] == ind and d[2] == nom]
        if not f or f[0][5] is None:
            out.append("  %s %s : France non calculee, non evaluable" % (ind, nom))
            continue
        f = f[0]
        autres = [d for d in D if d[0] != "FR" and d[1] == ind and d[2] == nom and d[3] == f[3] and d[5] is not None]
        if len(autres) < 3:
            m = "  %s %s : France %+.2f ; %d autre(s) pays, meme fenetre : non evaluable"
            out.append(m % (ind, nom, f[5], len(autres)))
            continue
        lo, hi = min(x[5] for x in autres), max(x[5] for x in autres)
        lect = "atypique" if (f[5] < lo or f[5] > hi) else "dans la plage observee"
        m = "  %s %s : France %+.2f ; autres [%+.2f ; %+.2f] (%s) -> %s"
        out.append(m % (ind, nom, f[5], lo, hi, ", ".join(x[0] for x in autres), lect))
B = [p for p in pays if (p, "E2", 2012) in V and (p, "E2", 2018) in V]
out.append("")
suite = "non calculee (n < 6)" if len(B) < 6 else "n >= 6 : calcul a faire avec les moyennes PISA"
out.append("Analyse B : pays avec E2 en 2012 et 2018 : %s (n = %d) ; %s" % (B, len(B), suite))
w = csv.writer(open("data/processed/exams_analysis_A.csv", "w", newline=""))
w.writerow(["pays", "indicateur", "fenetre", "debut", "fin", "variation_points"])
w.writerows(D)
open("data/processed/exams_analysis_A.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
