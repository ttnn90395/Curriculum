#!/usr/bin/env python3
"""impute_class_size.py -- Amendement 4: imputation de la taille de classe (ISCED11_2) par N_hat = STR x m, m = mediane de N/STR sur les pays complets.
Validation leave-one-out; critere fixe a l'avance: mediane des erreurs relatives <= 15 % ET 90e centile (rang le plus proche, ceil(0.9 n)) <= 30 %.
Pays imputables: NLD, NOR, NZL uniquement. Ecrit data/processed/class_size_imputed.csv seulement si le critere est satisfait."""
import csv, math, os, statistics as st
D = "data/raw/oecd/"; AGG = {"OECD", "EU25", "G20", "OECD_REP"}; TARGETS = ["NLD", "NOR", "NZL"]
def latest(path, flt, period):
    best = {}
    for r in csv.DictReader(open(D + path, encoding="utf-8-sig")):
        if any(r.get(k) != v for k, v in flt.items()) or r["OBS_VALUE"] == "": continue
        a = r["REF_AREA"]
        if a in AGG or not (len(a) == 3 and a.isalpha()) or r["INST_TYPE_EDU"] not in ("INST_EDU_PUB", "INST_EDU"): continue
        key = (0 if r["INST_TYPE_EDU"] == "INST_EDU_PUB" else 1, -int(r[period]))
        if a not in best or key < best[a][0]: best[a] = (key, float(r["OBS_VALUE"]), r[period], r["INST_TYPE_EDU"])
    return {a: v[1:] for a, v in best.items()}
N = latest("DSD_EAG_UOE_NON_FIN_PERS_DF_UOE_NF_PERS_CLS.csv", {"MEASURE": "CLS", "EDUCATION_LEV": "ISCED11_2"}, "TIME_PERIOD")
STR = latest("str.csv", {"MEASURE": "STU_PERS", "EDUCATION_LEV": "ISCED11_2", "UNIT_MEASURE": "ST_TCHR"}, "TIME_PERIOD")
full = [r["pays"] for r in csv.DictReader(open("data/processed/cross_country_net_cost.csv"))]
ref = [a for a in full if a in N and a in STR]
print(f"pays complets: {len(full)}, avec N et STR: {len(ref)}; ratio N/STR (mediane): ", end="")
ratio = {a: N[a][0] / STR[a][0] for a in ref}; m = st.median(ratio.values()); print(f"{m:.3f}")
errs = {}
for a in ref:
    m_ = st.median(v for b, v in ratio.items() if b != a)
    errs[a] = abs(STR[a][0] * m_ - N[a][0]) / N[a][0]
print(f"{'pays':5}{'N':>7}{'STR':>7}{'N/STR':>7}{'err LOO':>9}")
for a in sorted(ref, key=lambda x: errs[x]): print(f"{a:5}{N[a][0]:7.1f}{STR[a][0]:7.1f}{ratio[a]:7.2f}{100 * errs[a]:8.1f}%")
e = sorted(errs.values()); med = st.median(e); p90 = e[math.ceil(0.9 * len(e)) - 1]
ok = med <= 0.15 and p90 <= 0.30
print(f"\nmediane des erreurs {100 * med:.1f} % (seuil 15), 90e centile {100 * p90:.1f} % (seuil 30) -> critere {'SATISFAIT' if ok else 'ECHOUE'}")
if ok:
    rows = [dict(pays=a, taille_classe_imputee=round(STR[a][0] * m, 2), str=round(STR[a][0], 2), annee_str=STR[a][1], destination_str=STR[a][2]) for a in TARGETS if a in STR and a not in N]
    with open("data/processed/class_size_imputed.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["pays", "taille_classe_imputee", "str", "annee_str", "destination_str"]); w.writeheader(); w.writerows(rows)
    print("imputations:", rows)
else:
    print("aucune imputation ecrite; resultat non concluant (Amendement 4)")
print("sans STR parmi les cibles:", [a for a in TARGETS if a not in STR])
