"""Precision 33 (Amendement 26) : persistance et diplomation au Canada (StatCan 37-10-0136-01), lecture locale.
Sorties : data/evidence_canada_persistence.csv, data/processed/canada_persistence.txt"""
import csv, io
RAW = "data/raw/exams/hors_europe/CA_37100136.csv"
R = list(csv.DictReader(io.StringIO(open(RAW, encoding="utf-8-sig").read())))
IND = ["Persistence rate after one year", "Persistence rate after two years", "Graduation rate after three years",
       "Graduation rate after four years", "Graduation rate after eight years", "Number of students in entry cohort"]
STAT = ["Canadian students", "Canadian and international students"]
def v(c, stat, ind):
    for r in R:
        if (r["GEO"] == "Canada" and r["Educational qualification of first enrolment"] == "Undergraduate degree"
                and r["Status of student in Canada"] == stat and r["Age group"] == "15 to 19 years"
                and r["Gender"] == "Total, gender" and r["Indicators"] == ind and r["REF_DATE"] == c):
            return float(r["VALUE"]) if r["VALUE"] not in ("", "..") else None
    return None
C = sorted(set(r["REF_DATE"] for r in R))
out, rows = [], []
for stat in STAT:
    out.append("\n== %s ; Undergraduate degree ; 15 to 19 ans ; Total genre" % stat)
    out.append("cohorte      " + " ".join("%-9s" % x[:9] for x in ("pers1", "pers2", "grad3", "grad4", "grad8", "effectif")))
    for c in C:
        x = [v(c, stat, i) for i in IND]
        for i, val in zip(IND, x):
            rows.append([stat, c, i, "" if val is None else val])
        out.append("%-12s " % c + " ".join("%-9s" % ("-" if a is None else ("%.1f" % a if a < 1000 else "%d" % a)) for a in x))
    for ind in IND[:4]:
        a, b, c2, d = v("2010/2011", stat, ind), v("2019/2020", stat, ind), v("2020/2021", stat, ind), None
        ser = [(c, v(c, stat, ind)) for c in C if v(c, stat, ind) is not None]
        if ser:
            first, last = ser[0], ser[-1]
            pre = [s for s in ser if s[0] <= "2019/2020"]
            out.append("  %s : premiere %s %.1f ; 2019/2020 %s ; 2020/2021 %s ; derniere %s %.1f" % (
                ind, first[0], first[1], "-" if b is None else "%.1f" % b, "-" if c2 is None else "%.1f" % c2, last[0], last[1]))
w = csv.writer(open("data/evidence_canada_persistence.csv", "w", newline="", encoding="utf-8"))
w.writerow(["statut_etudiant", "cohorte", "indicateur", "valeur"]); w.writerows(rows)
open("data/processed/canada_persistence.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
