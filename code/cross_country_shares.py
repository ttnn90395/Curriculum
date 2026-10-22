#!/usr/bin/env python3
"""cross_country_shares.py -- rapporte le cout d'une heure hebdomadaire supplementaire par classe (data/processed/cross_country_net_cost.csv)
a la depense par eleve et au PIB par habitant. EXPLORATOIRE. Regles fixees AVANT le calcul:
 - depense par eleve: EAG UOE FIN PERSTUD, niveau ISCED11_2, EXP_SOURCE _T, EXPENDITURE_TYPE DIR_EXP; destination INST_EDU_PUB (ligne N1) si disponible, sinon INST_EDU (N5);
   unite USD_PPP_ST, base de prix Q (constants), comme le salaire; annee = annee du salaire si disponible, sinon la plus recente.
 - PIB par habitant (USD PPA, prix constants) = depense par eleve / (part en % du PIB par habitant / 100), meme ligne, meme annee (unite PT_B1GQ_POP).
 - ratios: cout brut/depense par eleve (%), cout employeur/depense par eleve (%), cout brut/PIB par habitant (%).
Limites: la depense par eleve inclut tous les postes (investissement, personnels non enseignants); le PIB par habitant derive est celui de la base de l'OCDE."""
import csv
A = "data/processed/cross_country_net_cost.csv"; F = "data/raw/oecd/fin_perstud_lowsec.csv"
base = {r["pays"]: r for r in csv.DictReader(open(A))}
fin = {}
for r in csv.DictReader(open(F)):
    if r["EDUCATION_LEV"] != "ISCED11_2" or r["EXPENDITURE_TYPE"] != "DIR_EXP" or r["PRICE_BASE"] not in ("Q", "_Z"): continue
    fin.setdefault((r["REF_AREA"], r["EXP_DESTINATION"], r["TIME_PERIOD"]), {})[r["UNIT_MEASURE"]] = float(r["OBS_VALUE"])
def get(a, ys):
    for dest in ("INST_EDU_PUB", "INST_EDU"):
        c = {y: v for (b, d, y), v in fin.items() if b == a and d == dest and "USD_PPP_ST" in v and "PT_B1GQ_POP" in v}
        if c:
            y = str(ys) if str(ys) in c else max(c)
            return dest, y, c[y]
    return None
out = []
for a, r in base.items():
    g = get(a, r["annee_salaire"])
    if not g: continue
    dest, y, v = g
    dep, pct = v["USD_PPP_ST"], v["PT_B1GQ_POP"]; gdp = dep / (pct / 100)
    cb, ce = float(r["cout_eleve_brut_ppp"]), float(r["cout_eleve_employeur_ppp"])
    out.append(dict(pays=a, destination=dest, annee_depense=y, depense_eleve_ppp=round(dep), pib_hab_ppp=round(gdp), cout_brut_ppp=cb, cout_employeur_ppp=ce,
                    pct_depense_brut=round(100 * cb / dep, 3), pct_depense_employeur=round(100 * ce / dep, 3), pct_pib_hab_brut=round(100 * cb / gdp, 4)))
out.sort(key=lambda r: r["pct_depense_brut"])
print(f"{len(out)} pays sur {len(base)}. Cout d'une heure hebdomadaire supplementaire par classe, en % de la depense par eleve et du PIB par habitant:")
print(f"{'pays':5}{'dest.':>13}{'an':>6}{'dep./el':>9}{'PIB/hab':>9}{'%dep brut':>11}{'%dep empl':>11}{'%PIB/h':>9}")
for r in out: print(f"{r['pays']:5}{r['destination']:>13}{r['annee_depense']:>6}{r['depense_eleve_ppp']:9}{r['pib_hab_ppp']:9}{r['pct_depense_brut']:11}{r['pct_depense_employeur']:11}{r['pct_pib_hab_brut']:9}")
miss = sorted(set(base) - {r["pays"] for r in out})
if miss: print("sans depense par eleve:", miss)
if out:
    with open("data/processed/cross_country_shares.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print("Ecritures: data/processed/cross_country_shares.csv")
