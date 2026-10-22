#!/usr/bin/env python3
"""cost_transfers_primaire.py -- cout budgetaire de +1 heure hebdomadaire de mathematiques par classe, ecole elementaire publique (CP-CM2). EXPLORATOIRE, parametrique.
ETP = classes x dh / service hebdomadaire (24 h, circulaire BO n 32 du 28/08/2008); cout = ETP x cout moyen charge de la categorie 'enseignants du 1er degre' (RAP 2025, hors CAS);
avec CAS = cout hors CAS x rapport credits avec/hors CAS du programme 140 (derive). Scenarios de classes: elementaire seul (158 090) ou elementaire + classes mixtes (166 196).
Bornes marginales: cout d'entree et de sortie (RAP 2025). La maternelle est exclue (pas d'horaire disciplinaire). Hypothese: l'heure supplementaire est assuree par un ETP supplementaire."""
import csv
P = {r["id"]: r for r in csv.DictReader(open("data/parameters_teachers_cost.csv", encoding="utf-8"))}
def f(k):
    assert k in P, f"parametre absent: {k}"
    return float(P[k]["value"])
service = f("service_pe_hebdo"); elem = f("classes_elementaire_public_2024"); mixtes = f("classes_mixtes_primaire_public_2024")
c_hc = f("cout_ens1d_hors_CAS"); ratio = f("ratio_avecCAS_sur_horsCAS_P140"); c_in, c_out = f("cout_ens1d_entree"), f("cout_ens1d_sortie")
mission_hc, mission_ac = f("credits_paiement_mission_hors_CAS"), f("mission_CP_avec_CAS")
p140_hc, p140_ac = f("cp_P140_hors_CAS"), f("cp_P140_avec_CAS")
lines = [f"Statut des classes (RERS 2025 fiche 2.02 p.31): {P['classes_elementaire_public_2024']['status']}; statut du cout ens. 1er degre: {P['cout_ens1d_hors_CAS']['status']}.",
         f"Service {service:g} h/semaine; cout moyen charge ens. 1er degre hors CAS {c_hc:,.0f} EUR (entree {c_in:,.0f}, sortie {c_out:,.0f}); rapport avec/hors CAS (P140) {ratio:.4f}.",
         f"{'scenario':32}{'dh':>4}{'classes':>9}{'ETP':>8}{'M EUR hors CAS':>16}{'M EUR avec CAS':>16}{'% P140 hc':>10}{'pt mission hc':>14}{'pt mission ac':>14}"]
for name, cl in (("elementaire", elem), ("elementaire + mixtes", elem + mixtes)):
    for dh in (1, 2):
        etp = cl * dh / service; hc = etp * c_hc / 1e6; ac = hc * ratio
        lines.append(f"{name:32}{dh:4}{cl:9,.0f}{etp:8,.0f}{hc:16,.1f}{ac:16,.1f}{100 * hc / p140_hc:10.2f}{100 * hc / mission_hc:14.2f}{100 * ac / mission_ac:14.2f}")
etp = elem / service
lines.append(f"Bornes marginales (elementaire, +1 h): entree {etp * c_in / 1e6:,.1f} M EUR hors CAS, sortie {etp * c_out / 1e6:,.1f} M EUR hors CAS.")
lines.append("Limites: cout moyen de categorie (RAP 2025, hors CAS); CAS derive par le rapport des credits du P140; classes RERS 2025 (rentree 2024); maternelle exclue; la repartition des classes mixtes entre niveaux n'est pas connue.")
out = "\n".join(lines); print(out)
open("data/processed/cost_transfers_primaire.txt", "w").write(out + "\n")
