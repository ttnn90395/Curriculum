"""Axe 3 et Amendement 22 (Precisions 23 et 25) : reussite en licence par mention et par serie de bac,
Notes Flash du SIES. Sorties : data/evidence_sies_mentions.csv, data/evidence_sies_licence.csv,
data/processed/sies_axe3.txt ; PDF dans data/raw/exams/sies/"""
import csv, os, re, urllib.request
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
B = "https://www.enseignementsup-recherche.gouv.fr/sites/default/files/"
N = {  # cle : (cohorte attendue, url ; None = fichier deja present)
 "2017-18": (2012, B + "imported_files/documents/NF_parcours_et_reussite_licence_paces_2017-18_20112017_850958.pdf"),
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
     ("P1", r"^Passable 1\s?er\s?groupe$"), ("P2", r"^Passable 2\s?(.{0,3}me|nd|e)\s?groupe$")]
SER = [("general", r"^Ens(emble|\.) bac g.n.ral\.?$"), ("techno", r"^Ens(emble|\.) bac techno\.?$"),
       ("pro", r"^Ens(emble|\.) bac pro\.?$")]
V = re.compile(r"^\d{1,3}(,\d)?$")
def nb(L, j):
    v = L[j:j + 3]
    assert all(V.match(x) for x in v), v
    return [float(x.replace(",", ".")) for x in v]
def trouve(L, rx, c, fin):
    for k in range(c, fin):
        if re.match(rx, L[k]):
            return k, k + 1
        if k + 1 < fin and re.match(rx, L[k] + " " + L[k + 1]):
            return k, k + 2
    raise StopIteration(rx)
def lire(L):
    t = " ".join(L)
    m = re.search(r"bacheliers (20\d\d) inscrits en (?:1\S* ann\S* de licence|L1)", t)
    coh = int(m.group(1)) if m else None
    i = next(k for k, x in enumerate(L) if x == "Mention obtenue")
    R, c = {}, i + 1
    for cle, rx in M:
        k, j = trouve(L, rx, c, len(L))
        a, b, d = nb(L, j)
        assert d >= b and 0 < a < 100, (cle, a, b, d)
        R[cle] = (a, b, d)
        c = j + 3
    S = {}
    for cle, rx in SER:
        k = next(k for k in range(max(0, i - 45), i) if re.match(rx, L[k]))
        a, b, d = nb(L, k + 1)
        assert d >= b, (cle, a, b, d)
        S[cle] = (a, b, d)
    e = next(k for k in range(c, min(len(L) - 3, c + 60)) if L[k] == "Ensemble" and V.match(L[k + 1]))
    S["ensemble"] = tuple(nb(L, e + 1))
    return coh, R, S
os.makedirs(D, exist_ok=True)
rows, rows2, rep, G, LS = [], [], [], {}, {}
for k, (att, u) in N.items():
    p = D + "nf_%s.pdf" % k
    try:
        if not os.path.exists(p):
            b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": AG}), timeout=90).read()
            open(p, "wb").write(b)
        L = [x.replace("\xa0", " ").strip() for pg in fz.open(p) for x in pg.get_text().split("\n") if x.strip()]
        coh, R, S = lire(L)
        assert coh == att, "cohorte lue %s, attendue %s" % (coh, att)
    except Exception as e:
        rep.append("NF %s (cohorte attendue %d) ABSENTE ou rejetee : %s" % (k, att, repr(e)[:90]))
        continue
    rem = "crise sanitaire, controle continu" if coh >= 2020 else ""
    for cle, (a, b, d) in R.items():
        rows.append([coh, cle, a, b, d, "SIES Note Flash " + k, rem])
    for cle, (a, b, d) in S.items():
        rows2.append([coh, cle, a, b, d, "SIES Note Flash " + k, rem])
    LS[coh] = S
    g = R["TB"][2] - R["P1"][2]
    G[coh] = (g, R["TB"][2] / R["P1"][2])
    f = "cohorte %d : TB %.1f ; B %.1f ; AB %.1f ; P1 %.1f ; P2 %.1f (3 ou 4 ans, %%)"
    f += " ; G = %+.1f pts ; R = %.2f"
    rep.append(f % (coh, R["TB"][2], R["B"][2], R["AB"][2], R["P1"][2], R["P2"][2], g, G[coh][1]))
    f = "   parts des entrants (%%) : TB %.1f ; B %.1f ; AB %.1f ; P1 %.1f ; P2 %.1f"
    rep.append(f % tuple(R[c][0] for c in ("TB", "B", "AB", "P1", "P2")))
    f = "   L %.1f ; Ls general %.1f (part %.1f) ; techno %.1f (part %.1f) ; pro %.1f (part %.1f)"
    rep.append(f % (S["ensemble"][2], S["general"][2], S["general"][0], S["techno"][2], S["techno"][0],
                    S["pro"][2], S["pro"][0]))
if len(G) >= 2:
    c0, c1 = min(G), max(G)
    dg = G[c1][0] - G[c0][0]
    rep.append("")
    f = "H3 : G %d = %+.1f ; G %d = %+.1f ; variation %+.1f pts (seuil : inferieure a -5) -> %s"
    rep.append(f % (c0, G[c0][0], c1, G[c1][0], dg, "soutenue" if dg < -5 else "non soutenue"))
    rep.append("cohortes signalees (>= 2020) : %s" % [c for c in sorted(G) if c >= 2020])
    E = {}
    for r in csv.DictReader(open("data/evidence_bac_reussite_ensemble.csv", encoding="utf-8")):
        if r["taux_general"].strip():
            E[int(r["annee"])] = float(r["taux_general"])
    for nom, c1x in (("lecture principale", c1), ("lecture de controle", max(c for c in LS if c < 2020))):
        ls0, ls1 = LS[c0]["general"][2], LS[c1x]["general"][2]
        e0, e1 = E[c0], E[c1x]
        h6 = ls1 < ls0 and e1 > e0
        f = "H6 (%s) : Ls general %d = %.1f, %d = %.1f ; E1 general %d = %.1f, %d = %.1f -> %s"
        rep.append(f % (nom, c0, ls0, c1x, ls1, c0, e0, c1x, e1, "vraie" if h6 else "fausse"))
H1 = ["cohorte", "mention", "part_entrants_pct", "taux_3ans_pct", "taux_3ou4ans_pct", "source", "remarque"]
H2 = ["cohorte", "serie"] + H1[2:]
for nom, rr, hd in (("evidence_sies_mentions.csv", rows, H1), ("evidence_sies_licence.csv", rows2, H2)):
    w = csv.writer(open("data/" + nom, "w", newline="", encoding="utf-8"))
    w.writerow(hd)
    w.writerows(sorted(rr))
open("data/processed/sies_axe3.txt", "w").write("\n".join(rep) + "\n")
print("\n".join(rep))
