#!/usr/bin/env python3
"""check_note_numbers.py -- verifie que les chiffres cites dans docs/NOTE_COMPARAISON_INTERNATIONALE.tex correspondent aux CSV (recalcul independant)."""
import csv, statistics as st, sys
A = list(csv.DictReader(open("data/processed/cross_country_net_cost.csv"))); S = list(csv.DictReader(open("data/processed/cross_country_shares.csv")))
fr = next(r for r in A if r["pays"] == "FRA"); sf = next(r for r in S if r["pays"] == "FRA")
brut = sorted(float(r["cout_eleve_brut_ppp"]) for r in A); dep = sorted(float(r["pct_depense_brut"]) for r in S); pib = sorted(float(r["pct_pib_hab_brut"]) for r in S)
net = sorted((float(r["net_ens_sur_net_moyen"]) for r in A), reverse=True)
checks = [
 ("nombre de pays (tableau principal)", len(A), 22, 0), ("nombre de pays (parts de depense)", len(S), 21, 0),
 ("cout brut France ($ PPA)", float(fr["cout_eleve_brut_ppp"]), 125.8, 0.05), ("rang brut France (croissant)", brut.index(float(fr["cout_eleve_brut_ppp"])) + 1, 8, 0),
 ("mediane brute", st.median(brut), 137.9, 0.05), ("% salaire moyen national", float(fr["cout_eleve_pct_sal_moy_nat"]), 0.200, 0.0005),
 ("% depense par eleve France", float(sf["pct_depense_brut"]), 0.957, 0.0005), ("rang % depense (croissant)", dep.index(float(sf["pct_depense_brut"])) + 1, 4, 0),
 ("mediane % depense", st.median(dep), 1.32, 0.005), ("% PIB/hab France", float(sf["pct_pib_hab_brut"]), 0.2309, 0.00005),
 ("rang % PIB/hab (croissant)", pib.index(float(sf["pct_pib_hab_brut"])) + 1, 3, 0), ("net ens./net moyen France", float(fr["net_ens_sur_net_moyen"]), 1.016, 0.0005),
 ("rang net (decroissant)", net.index(float(fr["net_ens_sur_net_moyen"])) + 1, 16, 0),
 ("variante 18 h ($ PPA)", float(fr["cout_eleve_brut_ppp"]) * (1 / 18) / float(fr["etp_par_classe"]), 139.8, 0.1),
]
bad = 0
for name, got, exp, tol in checks:
    ok = abs(got - exp) <= tol; bad += not ok
    print(f"{'OK ' if ok else 'ECART'}  {name}: obtenu {got:.4g}, cite {exp:g}")
print(f"\n{len(checks) - bad}/{len(checks)} verifications satisfaites"); sys.exit(1 if bad else 0)
