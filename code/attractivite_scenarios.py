"""Scenarios d'attractivite, Amendement 9 (pre-enregistre). France, exploratoire, jamais une prediction ponctuelle.
Leviers : L1 hausse du brut de x % ; L2 baisse de la retenue salariale (net equivalent a L1) ; L3 (taux CAS) sans effet sur le net.
Assiette de cout : cout moyen charge hors CAS par categorie (RAP 2025) x ETP (traite comme proxy du brut, conformement a 9.3 :
borne haute du cout, car il inclut des charges patronales hors pension ; la retenue s'applique au seul traitement indiciaire,
traite ici comme egal au brut, borne haute de l'effet de L2).
Effet : variation des candidats = epsilon x variation relative du net ; admis supplementaires au taux moyen d'admission (sensibilite : moitie),
plafonnes aux postes non pourvus. Sorties : data/processed/attractivite_scenarios.csv et .txt"""
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
net_sur_brut = float(fra["net_sur_brut"])
tau25, tau26 = need("taux_contribution_employeur_pensions_civils_2025") / 100, need("taux_contribution_employeur_pensions_civils_2026") / 100
retenue = need("taux_retenue_pension_agent_etat") / 100
deg = {
    "1er degre": dict(etp=need("ETP_enseignants_public_1er_degre"), cout=need("cout_ens1d_hors_CAS"), cand=ev("A02"), adm=ev("A04"), posts=ev("A01")),
    "2nd degre": dict(etp=need("ETP_enseignants_public_2nd_degre"), cout=need("cout_ens2d_hors_CAS"), cand=ev("A10"), adm=ev("A12"), posts=ev("A09")),
}
res = []
for dname, d in deg.items():
    masse = d["etp"] * d["cout"] / 1e6        # M EUR hors CAS
    rate = d["adm"] / d["cand"]
    unfilled = d["posts"] - d["adm"]
    for x in (1.0, 5.0, 10.0):
        gain_net = masse * x / 100 * net_sur_brut     # M EUR de net par an
        d_points = x / 100 * net_sur_brut             # baisse de retenue equivalente (fraction du brut)
        assert d_points <= retenue, "baisse de retenue superieure a la retenue"
        costs = {
            "L1_hors_CAS": masse * x / 100,
            "L1_avec_CAS_2025": masse * x / 100 * (1 + tau25),
            "L1_avec_CAS_2026": masse * x / 100 * (1 + tau26),
            "L2_hors_CAS": 0.0,
            "L2_avec_financement_pensions": masse * d_points,
        }
        for eps in (0.3, 1.0, 2.0):
            dc = eps * x / 100 * d["cand"]
            for tag, share in (("admission_moyenne", 1.0), ("candidats_marginaux_moitie", 0.5)):
                extra = dc * rate * share
                filled = min(unfilled, extra)
                res.append(dict(degre=dname, hausse_net_pct=x, epsilon=eps, hypothese=tag, masse_hors_CAS_Meur=round(masse, 1),
                                gain_net_Meur=round(gain_net, 1), candidats_supp=round(dc), admis_supp=round(extra), postes_non_pourvus_observes=round(unfilled),
                                postes_pourvus_supp=round(filled), **{k: round(v, 1) for k, v in costs.items()},
                                net_par_euro_L1_hors_CAS=round(gain_net / costs["L1_hors_CAS"], 3),
                                net_par_euro_L1_avec_CAS_2026=round(gain_net / costs["L1_avec_CAS_2026"], 3),
                                net_par_euro_L2_avec_financement=round(gain_net / costs["L2_avec_financement_pensions"], 3),
                                Meur_par_poste_pourvu_L1_hors_CAS=(round(costs["L1_hors_CAS"] / filled, 2) if filled > 0 else None)))
os.makedirs(os.path.join(root, "data/processed"), exist_ok=True)
with open(os.path.join(root, "data/processed/attractivite_scenarios.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(res[0].keys())); w.writeheader(); w.writerows(res)
txt = [f"net_sur_brut FRA = {net_sur_brut}; CAS 2025 {tau25:.4f}, 2026 {tau26:.4f}; retenue {retenue:.4f}"]
for r in res:
    if r["hypothese"] == "admission_moyenne":
        txt.append(f"{r['degre']} +{r['hausse_net_pct']:.0f} % net, eps {r['epsilon']}: masse {r['masse_hors_CAS_Meur']} M EUR, cout L1 hors CAS {r['L1_hors_CAS']}, "
                   f"avec CAS 2026 {r['L1_avec_CAS_2026']}, L2 avec financement {r['L2_avec_financement_pensions']}; candidats +{r['candidats_supp']}, admis +{r['admis_supp']} "
                   f"(non pourvus observes {r['postes_non_pourvus_observes']}, pourvus en plus {r['postes_pourvus_supp']}); net/euro L1 {r['net_par_euro_L1_hors_CAS']}/{r['net_par_euro_L1_avec_CAS_2026']}, L2 {r['net_par_euro_L2_avec_financement']}; "
                   f"M EUR par poste pourvu (L1 hors CAS) {r['Meur_par_poste_pourvu_L1_hors_CAS']}")
open(os.path.join(root, "data/processed/attractivite_scenarios.txt"), "w").write("\n".join(txt) + "\n")
print("\n".join(txt))
