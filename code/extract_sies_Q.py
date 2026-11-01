"""Q (Amendement 23 partie B, Precision 28) : taux de passage L1 -> L2 des neo-bacheliers,
transcrit des Notes Flash SIES et controle comme chaine dans les PDF (sans reseau).
Sorties : data/evidence_sies_passage_L2.csv, data/processed/sies_passage_L2.txt"""
import csv, re
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
# cohorte : (note, valeur, motif de la valeur)
Q = {
 2019: ("2021-24", "53,5", r"53,5 ?%"),
 2020: ("2022-30", "48", r"48(?:,0)? ?%"),
 2021: ("2023-26", "44", r"44(?:,0)? ?%"),
 2022: ("2024-30", "47,8", r"47,8 ?%"),
 2023: ("2025-29", "49,1", r"49,1 ?%"),
}
PASS = re.compile(r"passage|L2|2(?:e|.me) ann.e|deuxi.me ann.e|seconde ann.e|r.inscri", re.I)
def rem(c):
    r = []
    if c == 2019: r.append("definition anterieure aux licences acces sante")
    if c in (2019, 2020): r.append("crise sanitaire")
    if c >= 2021: r.append("apres reforme du bac")
    if c == 2023: r.append("champ incluant des reinscrits en sante (a confirmer par le contexte)")
    return "; ".join(r)
rows, rep = [], []
for c, (k, v, pat) in sorted(Q.items()):
    p = "data/raw/exams/sies/nf_%s.pdf" % k
    try:
        T = " ".join(x for pg in fz.open(p) for x in pg.get_text().split())
    except Exception as e:
        rep.append("cohorte %d : PDF %s illisible (%s) -> absent" % (c, p, e)); 
        rows.append([c, c + 1, "", "SIES Note Flash " + k, "absent", "", rem(c)]); continue
    T = T.replace("\xa0", " ")
    ok, ctx, an = False, "", False
    for m in re.finditer(pat, T):
        avant = T[max(0, m.start() - 250):m.end() + 150]
        if PASS.search(avant):
            ok = True
            ctx = T[max(0, m.start() - 250):m.end() + 150]
            an = str(c) in T[max(0, m.start() - 400):m.end() + 150]
            break
    rows.append([c, c + 1, v if ok else "", "SIES Note Flash " + k, "verifie" if ok else "absent", ctx, rem(c)])
    rep.append("cohorte %d NF %s : Q %s %s ; annee de cohorte dans le contexte : %s\n   ...%s" % (
        c, k, v if ok else "-", "verifie" if ok else "ABSENT", "oui" if an else "non", ctx))
w = csv.writer(open("data/evidence_sies_passage_L2.csv", "w", newline="", encoding="utf-8"))
w.writerow(["cohorte_neobacheliers", "session", "Q_pct", "source", "statut", "contexte", "remarque"])
w.writerows(rows)
open("data/processed/sies_passage_L2.txt", "w").write("\n".join(rep) + "\n")
print("\n".join(rep))
