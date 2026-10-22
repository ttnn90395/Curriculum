#!/usr/bin/env python3
"""cross_country_net_cost.py -- cout d'une heure hebdomadaire supplementaire par classe, 1er cycle du secondaire public, par pays,
en trois niveaux: brut (EAG), cout employeur (brut + cotisations patronales) et net (apres impot et cotisations salariales). EXPLORATOIRE.
Donnees: OECD EAG (salaire reel moyen des enseignants ISCED11_24 25-64 ans, heures statutaires, semaines, taille de classe) et OECD Taxing Wages
(decomposition du coin fiscal, personne seule sans enfant, en monnaie nationale, par niveau de salaire = % du salaire moyen AW).
Pour chaque pays: niveau k = salaire moyen d'enseignant / salaire moyen national (arrondi, borne 50..250); lecture a ce niveau de LC (cout du travail),
GWE (brut), NWE (net). ATTENTION: taux d'un salarie moyen du regime general; ils ne tiennent PAS compte des regimes speciaux de retraite des fonctionnaires
(pour la France, le CAS Pensions n'est pas inclus). Formule du cout par eleve: (dh*semaines/heures_statutaires) * salaire / taille_classe."""
import csv, sys, os, re, statistics as st
D = "data/raw/oecd/"; DH = 1.0; FR_COST_LOADED = 52248.0
AGG = {"OECD", "EU25", "G20", "OECD_REP"}
def load(name):
    p = D + name
    if not os.path.exists(p):
        print(f"ABSENT: {p}"); return []
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def fnum(x):
    try: return float(x)
    except (TypeError, ValueError): return None
def pick(rows, period, flt, prefer=None):
    best = {}
    for r in rows:
        if any(r.get(k) != v for k, v in flt.items()): continue
        a, v = r.get("REF_AREA", ""), fnum(r.get("OBS_VALUE"))
        if v is None or a in AGG or not (len(a) == 3 and a.isalpha()): continue
        rank = (prefer[1].index(r.get(prefer[0])) if prefer and r.get(prefer[0]) in prefer[1] else 99)
        key = (rank, -int(r.get(period) or 0))
        if a not in best or key < best[a][0]: best[a] = (key, v, r.get(period))
    return {a: (v, p) for a, (k, v, p) in best.items()}
TWM = {"GWE", "LC", "ERSSC", "EESSC", "IT_CG", "IT_LG", "NWE", "PT", "CB"}
def load_tw():
    p = D + "DSD_TAX_WAGES_DECOMP_DF_TW_DECOMP.csv"
    if not os.path.exists(p): print(f"ABSENT: {p}"); return {}
    tw = {}
    with open(p, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if r["HOUSEHOLD_TYPE"] != "S_C0" or r["UNIT_MEASURE"] != "XDC" or r["MEASURE"] not in TWM or r["OBS_VALUE"] == "": continue
            if int(r["TIME_PERIOD"]) < 2022: continue
            m = re.sub(r"\D", "", r["INCOME_PRINCIPAL"])
            if not m: continue
            tw.setdefault((r["REF_AREA"], int(r["TIME_PERIOD"]), int(m)), {})[r["MEASURE"]] = abs(float(r["OBS_VALUE"]))
    return tw
pub = ("INST_TYPE_EDU", ["INST_EDU_PUB", "INST_EDU"])
act = load("DSD_EAG_SAL_ACT_DF_ALL.csv"); wt = load("DSD_EAG_WT_DF_ALL.csv"); cls = load("DSD_EAG_UOE_NON_FIN_PERS_DF_UOE_NF_PERS_CLS.csv")
base = {"EDUCATION_LEV": "ISCED11_24", "AGE": "Y25T64", "SEX": "_T", "PERS_TYPE": "TE"}
S_ppp = pick(act, "REF_PERIOD", dict(base, MEASURE="SAL_ACT", UNIT_MEASURE="USD_PPP", PRICE_BASE="Q"), pub)
S_xdc = pick(act, "REF_PERIOD", dict(base, MEASURE="SAL_ACT", UNIT_MEASURE="XDC", PRICE_BASE="V"), pub)
REL = pick(act, "REF_PERIOD", dict(base, MEASURE="SAL_ACT_REL_TER"), pub)
T = pick(wt, "REF_PERIOD", dict(MEASURE="WKT_STA_TCH", UNIT_MEASURE="H_Y", EDUCATION_LEV="ISCED11_24", PERS_TYPE="TE"), pub)
WK = pick(wt, "REF_PERIOD", dict(MEASURE="WKT_STA_TCH", UNIT_MEASURE="WK_Y", EDUCATION_LEV="ISCED11_24", PERS_TYPE="TE"), pub)
DY = pick(wt, "REF_PERIOD", dict(MEASURE="WKT_STA_TCH", UNIT_MEASURE="D_Y", EDUCATION_LEV="ISCED11_24", PERS_TYPE="TE"), pub)
N = pick(cls, "TIME_PERIOD", {"MEASURE": "CLS", "EDUCATION_LEV": "ISCED11_2"}, pub)
tw = load_tw()
twy = {}
for (a, y, k) in tw: twy.setdefault(a, set()).add(y)
print(f"couverture: salaire PPA {len(S_ppp)}, salaire XDC {len(S_xdc)}, heures {len(T)}, taille classe {len(N)}, pays Taxing Wages {len(twy)}")
out, lost = [], []
for a in sorted(set(S_ppp) & set(S_xdc) & set(T) & set(N)):
    ys = sorted(twy.get(a, []))
    if not ys: lost.append((a, "absent de Taxing Wages")); continue
    y0 = int(S_xdc[a][1]); y = y0 if y0 in ys else max(ys)
    g100 = tw.get((a, y, 100), {}).get("GWE")
    if not g100: lost.append((a, "pas de niveau AW100")); continue
    k_raw = 100 * S_xdc[a][0] / g100; k = int(min(250, max(50, round(k_raw))))
    rec, rec100 = tw.get((a, y, k)), tw[(a, y, 100)]
    if not rec or not all(m in rec for m in ("GWE", "LC", "NWE")): lost.append((a, f"niveau AW{k} incomplet")); continue
    w, wsrc = (WK[a][0], "sem") if a in WK else ((DY[a][0] / 5, "jours/5") if a in DY else (38.0, "38 suppose"))
    etp = DH * w / T[a][0]; gross_pp = etp * S_ppp[a][0] / N[a][0]
    uplift = rec["LC"] / rec["GWE"]; net_ratio = rec["NWE"] / rec["GWE"]
    rel = REL.get(a, (None,))[0]
    out.append(dict(pays=a, salaire_ppp=round(S_ppp[a][0]), pct_salaire_moyen=round(k_raw, 1), borne="oui" if k != round(k_raw) else "", facteur_employeur=round(uplift, 3),
                    net_sur_brut=round(net_ratio, 3), net_ens_sur_net_moyen=round(rec["NWE"] / rec100["NWE"], 3), net_ppp=round(S_ppp[a][0] * net_ratio),
                    ratio_dipl_sup=round(rel, 3) if rel else "", heures_an=round(T[a][0]), semaines=round(w, 1), src_semaines=wsrc, taille_classe=round(N[a][0], 1),
                    etp_par_classe=round(etp, 4), cout_eleve_pct_sal_moy_nat=round(100*gross_pp/(S_ppp[a][0]/(k_raw/100)), 3), cout_eleve_brut_ppp=round(gross_pp, 1), cout_eleve_employeur_ppp=round(gross_pp * uplift, 1),
                    annee_salaire=S_xdc[a][1], annee_fiscale=y))
out.sort(key=lambda r: r["cout_eleve_employeur_ppp"])
print(f"\n{len(out)} pays complets. Cout d'une heure hebdomadaire supplementaire par classe, par eleve et par an (dollars PPA):")
print(f"{'pays':5}{'sal.PPA':>9}{'%sal.moy':>9}{'fact.empl':>10}{'net/brut':>9}{'net/net moy':>12}{'net PPA':>9}{'ETP/cl':>8}{'$/el brut':>10}{'$/el empl':>10}{'%sal.nat':>9}")
for r in out:
    print(f"{r['pays']:5}{r['salaire_ppp']:9}{r['pct_salaire_moyen']:9}{r['facteur_employeur']:10}{r['net_sur_brut']:9}{r['net_ens_sur_net_moyen']:12}{r['net_ppp']:9}{r['etp_par_classe']:8}{r['cout_eleve_brut_ppp']:10}{r['cout_eleve_employeur_ppp']:10}{r['cout_eleve_pct_sal_moy_nat']:9}")
if lost: print("ecartes:", lost)
def rank(key, rev=False):
    s = sorted(out, key=lambda r: r[key], reverse=rev); return [r["pays"] for r in s].index("FRA") + 1 if any(r["pays"] == "FRA" for r in out) else None
if any(r["pays"] == "FRA" for r in out):
    fr = next(r for r in out if r["pays"] == "FRA")
    print(f"\n== France: rang cout/eleve brut {rank('cout_eleve_brut_ppp')}/{len(out)}, cout employeur {rank('cout_eleve_employeur_ppp')}/{len(out)}, salaire net en PPA {rank('net_ppp', True)}/{len(out)} (1 = plus eleve), net ens./net moyen {rank('net_ens_sur_net_moyen', True)}/{len(out)}")
    print(f"   variante France a 18 h de service: cout brut/eleve {fr['cout_eleve_brut_ppp']*(1/18)/fr['etp_par_classe']:.1f} $ PPA, soit +{100*((1/18)/fr['etp_par_classe']-1):.1f} % (OCDE: {fr['heures_an']} h sur {fr['semaines']} semaines)")
    print(f"   ETP par classe {fr['etp_par_classe']} (calcul national: {1/18:.4f}); classe {fr['taille_classe']} (RERS: 25.4); facteur employeur Taxing Wages (regime general) {fr['facteur_employeur']}")
    if "FRA" in S_xdc: print(f"   rapport implicite du calcul national: cout complet hors CAS {FR_COST_LOADED:,.0f} / salaire brut EAG {S_xdc['FRA'][0]:,.0f} = {FR_COST_LOADED / S_xdc['FRA'][0]:.3f} (a comparer au facteur ci-dessus)")
for key, lab in (("cout_eleve_brut_ppp", "brut"), ("cout_eleve_employeur_ppp", "employeur")):
    v = [r[key] for r in out]
    if not v: continue
    print(f"   cout/eleve {lab}: mediane {st.median(v):.1f}, min {min(v):.1f}, max {max(v):.1f}")
if out:
    with open("data/processed/cross_country_net_cost.csv", "w", newline="") as fh:
        w_ = csv.DictWriter(fh, fieldnames=list(out[0])); w_.writeheader(); w_.writerows(out)
print("\nLimites: facteurs employeur et nets = personne seule sans enfant au niveau de salaire moyen d'enseignant, regime general; les retraites specifiques des fonctionnaires"
      " (CAS Pensions en France, Beamte en Allemagne...) ne sont pas incluses; salaires EAG et fiscalite de la meme annee si disponible; BEL et GBR ecartes si codes differents.")
print("Ecritures: data/processed/cross_country_net_cost.csv")
