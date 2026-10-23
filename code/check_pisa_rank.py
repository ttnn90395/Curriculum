"""Rang de la France dans PISA 2025 a partir de data/manual/pisa_means_2022_2025.csv (source secondaire :
Wikipedia 2022, eduscores.org 2025 ancre sur la France) et recoupement des sciences 2025 avec la page OCDE
(data/evidence_pisa2025_science_oecd_page.csv). Descriptif, exploratoire.
Rang = 1 + nombre de pays strictement meilleurs. Sorties : data/processed/check_pisa_rank.txt"""
import csv, os, statistics as st
root = os.environ.get("ROOT", ".")
rows = list(csv.DictReader(open(os.path.join(root, "data/manual/pisa_means_2022_2025.csv"))))
m = {}
missing = []
for r in rows:
    if r["mean"].strip() == "":
        missing.append((r["iso3"], r["subject"], r["cycle"]))
        continue
    m[(r["iso3"], r["subject"], r["cycle"])] = float(r["mean"])
isos = sorted({r["iso3"] for r in rows})
subjects = ["mathematics", "reading", "science"]
def rank(iso, cyc, vals):
    v = vals[iso]
    return 1 + sum(1 for k, x in vals.items() if x > v), len(vals)
out = [f"pays dans le fichier : {len(isos)}"]
out.append(f"moyennes manquantes (ignorees, non imputees) : {len(missing)} {missing}")
rk = {}
for cyc in ["2022", "2025"]:
    allv = {}
    for s in subjects:
        vals = {i: m[(i, s, cyc)] for i in isos if (i, s, cyc) in m}
        allv[s] = vals
        r_, n_ = rank("FRA", cyc, vals)
        rk[(s, cyc)] = r_
        out.append(f"{cyc} {s}: France {vals['FRA']:.0f}, rang {r_}/{n_}, moyenne simple pays {st.mean(vals.values()):.1f}, ecart-type entre pays {st.pstdev(vals.values()):.1f}")
    both = [i for i in isos if all(i in allv[s] for s in subjects)]
    avg = {i: sum(allv[s][i] for s in subjects) / 3 for i in both}
    r_, n_ = rank("FRA", cyc, avg)
    rk[("moy3", cyc)] = r_
    out.append(f"{cyc} moyenne des 3 domaines: France {avg['FRA']:.1f}, rang {r_}/{n_}")
out.append("Variation de rang 2022 -> 2025 (positif = recul) : " + "; ".join(f"{s} {rk[(s,'2025')]-rk[(s,'2022')]:+d}" for s in subjects + ["moy3"]))
out.append("Reference DEPP (variation de places publiee, signe DEPP : - = recul) : sciences -1, mathematiques -8, lecture +1 (a comparer en inversant le signe)")
page = {r["iso3"]: float(r["science_2025"]) for r in csv.DictReader(open(os.path.join(root, "data/evidence_pisa2025_science_oecd_page.csv")))}
diff = [(i, page[i], m[(i, "science", "2025")]) for i in sorted(page) if (i, "science", "2025") in m and abs(page[i] - m[(i, "science", "2025")]) > 0.5]
only_page = sorted(set(page) - set(isos)); only_file = sorted(set(isos) - set(page))
out.append(f"Recoupement sciences 2025 page OCDE / fichier : {len(page)} pays page, ecarts > 0.5 : {len(diff)}")
out += [f"  {i}: page {a:.0f}, fichier {b:.0f}" for i, a, b in diff]
out.append(f"Pays seulement dans la page : {only_page}; seulement dans le fichier : {only_file}")
os.makedirs(os.path.join(root, "data/processed"), exist_ok=True)
open(os.path.join(root, "data/processed/check_pisa_rank.txt"), "w").write("\n".join(out) + "\n")
print("\n".join(out))
