"""Partie A de l'Amendement 23 (Precision 27) : mentions des admis neo-bacheliers par groupe de formation,
jeux Parcoursup 2018-2025 deja telecharges (sonde 15). Sans reseau.
Sorties : data/evidence_parcoursup_mentions.csv, data/processed/parcoursup_mentions.txt"""
import csv, glob, os, re, unicodedata
csv.field_size_limit(10**8)
G = ["Tous", "Licence", "BTS", "BUT_DUT", "Sante_1re_annee", "CPGE", "Ecole_ingenieur", "Ecole_commerce", "Autres"]
def groupe(fili):
    k = unicodedata.normalize("NFKD", fili).encode("ascii", "ignore").decode().strip().lower()
    if k in ("licence", "licence_las"):
        return "Licence"
    if k == "bts":
        return "BTS"
    if k in ("dut", "but"):
        return "BUT_DUT"
    if k in ("paces", "pass"):
        return "Sante_1re_annee"
    if k == "cpge":
        return "CPGE"
    if k.startswith("ecole d'ing"):
        return "Ecole_ingenieur"
    if k.startswith("ecole de commerce"):
        return "Ecole_commerce"
    return "Autres"
def f(x):
    try:
        return float(x)
    except Exception:
        return 0.0
F = ["acc_neobac", "acc_tb", "acc_tbf", "acc_b", "acc_ab", "acc_sansmention", "acc_mention_nonrenseignee",
     "acc_bg", "acc_bt", "acc_bp"]
out, rows = [], []
for p in sorted(glob.glob("data/raw/parcoursup/*.csv")):
    y = int(os.path.basename(p)[:4])
    t = open(p, "rb").read().decode("utf-8-sig", "replace")
    R = list(csv.DictReader(t.splitlines(), delimiter=";"))
    cols = {c.lower(): c for c in R[0]}
    A = {g: {k: 0.0 for k in F} for g in G}
    for r in R:
        g = groupe(r[cols["fili"]])
        for k in F:
            if k in cols:
                A[g][k] += f(r[cols[k]])
                A["Tous"][k] += f(r[cols[k]])
    T = A["Tous"]
    s = sum(T[k] for k in ("acc_tb", "acc_tbf", "acc_b", "acc_ab", "acc_sansmention", "acc_mention_nonrenseignee"))
    if abs(s - T["acc_neobac"]) > 0.005 * T["acc_neobac"]:
        out.append("%d REJETEE : somme des mentions %d, acc_neobac %d" % (y, s, T["acc_neobac"]))
        continue
    for g in G:
        a = A[g]
        n = a["acc_neobac"]
        if n <= 0:
            continue
        m = n - a["acc_mention_nonrenseignee"]
        tb = a["acc_tb"] + a["acc_tbf"]
        bacs = a["acc_bg"] + a["acc_bt"] + a["acc_bp"]
        bac = [round(100 * a[k] / bacs, 3) if bacs else "" for k in ("acc_bg", "acc_bt", "acc_bp")]
        rows.append([y, g, int(n), round(100 * tb / m, 3), round(100 * a["acc_b"] / m, 3),
                     round(100 * a["acc_ab"] / m, 3), round(100 * a["acc_sansmention"] / m, 3),
                     round(100 * a["acc_mention_nonrenseignee"] / n, 3)] + bac)
H = ["session", "groupe", "n_neobacheliers", "part_TB", "part_B", "part_AB", "part_sans_mention",
     "part_mention_non_renseignee", "part_bac_general", "part_bac_techno", "part_bac_pro"]
w = csv.writer(open("data/evidence_parcoursup_mentions.csv", "w", newline="", encoding="utf-8"))
w.writerow(H)
w.writerows(rows)
Y = sorted({r[0] for r in rows})
for nom, ix in (("Part de Tres bien (%) parmi les admis a mention renseignee", 3),
                ("Part sans mention (%)", 6), ("Part de bacs generaux (%)", 8)):
    out.append(nom)
    out.append("  %-16s" % "groupe" + " ".join("%6d" % y for y in Y))
    for g in G:
        v = {r[0]: r[ix] for r in rows if r[1] == g}
        if v:
            out.append("  %-16s" % g + " ".join(("%6.1f" % v[y]) if y in v and v[y] != "" else "     -" for y in Y))
out.append("")
out.append("Effectifs n (admis neo-bacheliers) :")
for g in G:
    v = {r[0]: r[2] for r in rows if r[1] == g}
    out.append("  %-16s" % g + " ".join(("%6d" % (v[y] // 1000)) if y in v else "     -" for y in Y) + "  (milliers)")
open("data/processed/parcoursup_mentions.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
