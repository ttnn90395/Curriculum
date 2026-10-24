"""Hausse CIBLEE sur les entrants, Amendement 10 (pre-enregistre). France, exploratoire.
T1 : hausse de x % du salaire d'entree pendant Y annees de carriere pour chaque nouvelle cohorte (regime permanent : Y cohortes presentes).
Cout hors CAS = admis par an x cout moyen charge d'entree (RAP 2025) x x % x Y ; avec CAS 2026 : x (1 + taux 2026).
Variante L2 : baisse de retenue equivalente en net (x % x net/brut), avec financement du compte pensions.
Effet : candidats = epsilon x x % x candidats presents (l'estimation anglaise porte sur le salaire de DEBUT relatif), admis au taux moyen
(sensibilite : moitie), plafonnes aux postes non pourvus observes. Ignore l'attrition des cohortes (borne haute du cout).
Sorties : data/processed/attractivite_cible.csv et .txt"""
import csv, os
root = os.environ.get("ROOT", ".")
P = {}
for row in csv.reader(open(os.path.join(root, "data/parameters_teachers_cost.csv"))):
    if len(row) >= 2 and row[0] != "id" and row[1].strip() != "":
        P[row[0]] = float(row[1])
def need(k):
    if k not in P:
        raise SystemExit(f"parametre manquant : {k} (scenario non calcule, aucune imputation)")
    return P[k]
A = {r["id"]: r for r in csv.DictReader(open(os.path.join(root, "data/evidence_attractivite_fr.csv")))}
def ev(i): return float(A[i]["value"])
fra = [r for r in csv.DictReader(open(os.path.join(root, "data/processed/cross_country_net_cost.csv"))) if r["pays"] == "FRA"][0]
nsb = float(fra["net_sur_brut"])
tau26 = need("taux_contribution_employeur_pensions_civils_2026") / 100
deg = {
    "1er degre": dict(entree=need("cout_moyen_charge_HCAS_ens1d_entree_RAP2025"), cand=ev("A02"), adm=ev("A04"), posts=ev("A01")),
    "2nd degre": dict(entree=need("cout_moyen_charge_HCAS_ens2d_entree_RAP2025"), cand=ev("A10"), adm=ev("A12"), posts=ev("A09")),
}
res = []
for dname, d in deg.items():
    rate = d["adm"] / d["cand"]; unfilled = d["posts"] - d["adm"]
    for x in (5.0, 10.0, 20.0):
        for Y in (1, 5):
            base = d["adm"] * d["entree"] / 1e6 * Y            # M EUR : masse d'entree concernee
            c_hors, c_cas = base * x / 100, base * x / 100 * (1 + tau26)
            c_l2 = base * x / 100 * nsb
            for eps in (0.3, 1.0, 2.0):
                dc = eps * x / 100 * d["cand"]
                for tag, share in (("admission_moyenne", 1.0), ("candidats_marginaux_moitie", 0.5)):
                    extra = dc * rate * share; filled = min(unfilled, extra)
                    res.append(dict(degre=dname, hausse_entree_pct=x, annees=Y, epsilon=eps, hypothese=tag, masse_entrants_Meur=round(base, 1),
                                    cout_hors_CAS=round(c_hors, 1), cout_avec_CAS_2026=round(c_cas, 1), cout_L2_avec_financement=round(c_l2, 1),
                                    candidats_supp=round(dc), admis_supp=round(extra), non_pourvus_observes=round(unfilled), pourvus_supp=round(filled),
                                    Meur_par_poste_pourvu_hors_CAS=(round(c_hors / filled, 3) if filled > 0 else None)))
os.makedirs(os.path.join(root, "data/processed"), exist_ok=True)
with open(os.path.join(root, "data/processed/attractivite_cible.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(res[0].keys())); w.writeheader(); w.writerows(res)
txt = [f"net_sur_brut FRA = {nsb}; CAS 2026 {tau26:.4f}"]
for r in res:
    if r["hypothese"] == "admission_moyenne":
        txt.append(f"{r['degre']} entree +{r['hausse_entree_pct']:.0f} % pendant {r['annees']} an(s), eps {r['epsilon']}: masse entrants {r['masse_entrants_Meur']} M EUR, cout hors CAS {r['cout_hors_CAS']}, "
                   f"avec CAS 2026 {r['cout_avec_CAS_2026']}, L2 {r['cout_L2_avec_financement']}; candidats +{r['candidats_supp']}, admis +{r['admis_supp']} (non pourvus {r['non_pourvus_observes']}, pourvus en plus {r['pourvus_supp']}); "
                   f"M EUR par poste pourvu {r['Meur_par_poste_pourvu_hors_CAS']}")
open(os.path.join(root, "data/processed/attractivite_cible.txt"), "w").write("\n".join(txt) + "\n")
print("\n".join(txt))
