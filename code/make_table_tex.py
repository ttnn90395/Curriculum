#!/usr/bin/env python3
"""make_table_tex.py -- genere docs/table_comparaison.tex a partir des CSV (aucune valeur recopiee a la main)."""
import csv
A = {r["pays"]: r for r in csv.DictReader(open("data/processed/cross_country_net_cost.csv"))}
S = {r["pays"]: r for r in csv.DictReader(open("data/processed/cross_country_shares.csv"))}
rows = sorted(A.values(), key=lambda r: float(r["cout_eleve_brut_ppp"]))
L = [r"\begin{tabular}{lrrrrrrrr}", r"\toprule",
     r"Pays & Salaire & \% sal. & Net ens./ & \$/élève & \$/élève & \% dép. & \% PIB/ & \% sal. \\",
     r" & PPA & moyen & net moyen & brut & employeur & par élève & hab. & nat. \\", r"\midrule"]
for r in rows:
    s = S.get(r["pays"]); fra = r["pays"] == "FRA"; b = (r"\textbf{%s}" if fra else "%s")
    cells = [r["pays"], f"{int(float(r['salaire_ppp'])):,}".replace(",", r"\,"), f"{float(r['pct_salaire_moyen']):.1f}", f"{float(r['net_ens_sur_net_moyen']):.3f}",
             f"{float(r['cout_eleve_brut_ppp']):.1f}", f"{float(r['cout_eleve_employeur_ppp']):.1f}",
             f"{float(s['pct_depense_brut']):.2f}" if s else "--", f"{float(s['pct_pib_hab_brut']):.3f}" if s else "--", f"{float(r['cout_eleve_pct_sal_moy_nat']):.3f}"]
    L.append(" & ".join(b % c for c in cells) + r" \\")
L += [r"\bottomrule", r"\end{tabular}"]
open("docs/table_comparaison.tex", "w").write("\n".join(L) + "\n")
print(f"{len(rows)} lignes ecrites dans docs/table_comparaison.tex")
