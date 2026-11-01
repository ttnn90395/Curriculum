"""Axe 3 (Amendement 21, Precision 23) : taux de reussite en licence par mention du bac, Notes Flash du SIES.
Sorties : data/evidence_sies_mentions.csv, data/processed/sies_axe3.txt ; PDF dans data/raw/exams/sies/"""
import csv, os, re, urllib.request
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
B = "https://www.enseignementsup-recherche.gouv.fr/sites/default/files/"
O = "https://ode.ube.fr/images/stories/composante/Documents/Publication/nationales/2018/"
N = {  # cle : (cohorte attendue, url)
 "2017-18": (2012, B + "imported_files/documents/NF_parcours_et_reussite_licence_paces_2017-18_20112017_850958.pdf"),
 "2018-21": (2013, O + "NF_21_2018_parcours_et_reussite_licence_paces_1040888.pdf"),
 "2019-26": (2014, B + "imported_files/documents/NF26_ReussiteLicence_1214277.pdf"),
 "2020-22": (2015, B + "imported_files/documents/NF22_Reussite_Licence_1343710.pdf"),
 "2021-24": (2016, B + "2021-11/nf-sies-2021-24-15115.pdf"),
 "2022-30": (2017, B + "2022-11/nf-sies-2022-30-25300.pdf"),
 "2023-26": (2018, B + "2023-11/nf-sies-2023-26-30231.pdf"),
 "2024-30": (2019, B + "2024-11/nf-sies-2024-30-35338.pdf"),
 "2025-29": (2020, B + "2025-11/nf-sies-2025-29-38293.pdf"),
}
AG = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
D = "data/raw/exams/sies/"
M = [("TB", r"^Tr.s bien$"), ("B", r"^Bien$"), ("AB", r"^Assez bien$"),
     ("P1", r"^Passable 1er groupe$"), ("P2", r"^Passable 2.{0,3}\s?groupe$")]
V = re.compile(r"^\d{1,3},\d$")
def lire(L):
    t = " ".join(L)
    m = re.search(r"bacheliers (20\d\d) inscrits en (?:1\S* ann\S* de licence|L1)", t)
    coh = int(m.group(1)) if m else None
    i = next(k for k, x in enumerate(L) if x == "Mention obtenue")
    R, c = {}, i + 1
    for cle, rx in M:
        j = next(k for k in range(c, len(L)) if re.match(rx, L[k]))
        v = L[j + 1:j + 4]
        assert all(V.match(x) for x in v), (cle, v)
        a, b, d = [float(x.replace(",", ".")) for x in v]
        assert d >= b and 0 < a < 100, (cle, a, b, d)
        R[cle] = (a, b, d)
        c = j + 4
    return coh, R
os.makedirs(D, exist_ok=True)
rows, rep, G = [], [], {}
for k, (att, u) in N.items():
    p = D + "nf_%s.pdf" % k
    try:
        if not os.path.exists(p):
            b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": AG}), timeout=90).read()
            open(p, "wb").write(b)
        L = [x.replace("\xa0", " ").strip() for pg in fz.open(p) for x in pg.get_text().split("\n") if x.strip()]
        coh, R = lire(L)
        assert coh == att, "cohorte lue %s, attendue %s" % (coh, att)
    except Exception as e:
        rep.append("NF %s (cohorte attendue %d) ABSENTE ou rejetee : %s" % (k, att, str(e)[:90]))
        continue
    for cle, (a, b, d) in R.items():
        rows.append([coh, cle, a, b, d, "SIES Note Flash " + k, "crise sanitaire, controle continu" if coh >= 2020 else ""])
    g = R["TB"][2] - R["P1"][2]
    G[coh] = (g, R["TB"][2] / R["P1"][2])
    f = "cohorte %d : TB %.1f ; B %.1f ; AB %.1f ; P1 %.1f ; P2 %.1f (3 ou 4 ans, %%)"
    f += " ; G = %+.1f pts ; R = %.2f"
    rep.append(f % (coh, R["TB"][2], R["B"][2], R["AB"][2], R["P1"][2], R["P2"][2], g, G[coh][1]))
if len(G) >= 2:
    c0, c1 = min(G), max(G)
    dg = G[c1][0] - G[c0][0]
    rep.append("")
    f = "H3 : G %d = %+.1f ; G %d = %+.1f ; variation %+.1f pts (seuil : inferieure a -5) -> %s"
    rep.append(f % (c0, G[c0][0], c1, G[c1][0], dg, "soutenue" if dg < -5 else "non soutenue"))
    rep.append("cohortes signalees (>= 2020) : %s" % [c for c in sorted(G) if c >= 2020])
w = csv.writer(open("data/evidence_sies_mentions.csv", "w", newline="", encoding="utf-8"))
w.writerow(["cohorte", "mention", "part_entrants_pct", "taux_3ans_pct", "taux_3ou4ans_pct", "source", "remarque"])
w.writerows(sorted(rows))
open("data/processed/sies_axe3.txt", "w").write("\n".join(rep) + "\n")
print("\n".join(rep))
