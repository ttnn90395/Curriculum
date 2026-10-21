#!/usr/bin/env python3
"""cost_transfers.py -- modules C et D, comptabilite parametrique (EXPLORATOIRE, aucune estimation causale).
Transfert: +dh heures hebdomadaires de maths par classe de college (public hors SEGPA), toutes classes concernees.
ETP = classes * dh / service (heures taillees dans le service, sans complements ni heures sup, sans ponderation REP+).
Cout = ETP * cout_ETP; deux bornes derivees (hors CAS Pensions / avec CAS), NON primaires (voir parameters_teachers_cost.csv).
Part = cout / credits de paiement de la mission (hors CAS pour la borne hors CAS; hors CAS + contribution CAS pour l'autre)."""
import csv
from pathlib import Path
P = {r["id"]: r["value"] for r in csv.DictReader(open("data/parameters_teachers_cost.csv"))}
f = lambda k: float(P[k])
classes = f("classes_college_public_hors_segpa")
mission_hc, mission_ac = f("credits_paiement_mission_hors_CAS"), f("mission_CP_avec_CAS")
# cout principal: moyenne du programme P141 (CP / plafond ETPT, source primaire); cout "mixte" (titre 2 / ETPT+ETP non ens.) conserve comme borne basse
costs = {"hors_CAS": (f("cout_ETPT_P141_hors_CAS"), mission_hc), "avec_CAS": (f("cout_ETPT_P141_avec_CAS"), mission_ac),
         "mixte_hors_CAS": (f("cout_ETP_derive_hors_CAS"), mission_hc), "mixte_avec_CAS": (f("cout_ETP_derive_avec_CAS"), mission_ac)}
base_h = (f("heures_maths_6e") + 3 * f("heures_maths_5e_4e_3e")) / 4   # hypothese: classes egalement reparties entre niveaux
print(f"Reference: heures de maths moyennes par classe de college {base_h:.2f} h/semaine (hypothese 4 niveaux egaux)")
print(f"ETP maths college (certifies, 18 h): {classes * base_h / f('service_certifies'):,.0f}  ~ {classes * base_h / f('service_certifies') / f('ETP_enseignants_public_2nd_degre'):.1%} des ETP du 2nd degre public")
out = []
print("Cout par ETPT (EUR/an): "+", ".join(f"{k} {c:,.0f}" for k, (c, m) in costs.items()))
print(f"\n{'dh':>4} {'service':>9} {'ETP':>8} {'ETP/1000cl':>11} {'cout M (hCAS)':>14} {'part % (hCAS)':>14} {'cout M (avecCAS)':>17} {'part % (avecCAS)':>17} {'% heures maths':>15}")
print("(colonnes cout/part: cout P141 hors CAS puis avec CAS; bornes mixtes dans le CSV)")
for dh in (-1.0, -0.5, 0.5, 1.0):
    for sv_name in ("service_certifies", "service_agreges"):
        sv = f(sv_name)
        etp = classes * dh / sv
        row = dict(dh=dh, service=sv, etp=round(etp), etp_par_1000_classes=round(1000 * dh / sv, 1),
                   pct_heures_maths=round(100 * dh / base_h, 1))
        for k, (c, m) in costs.items():
            row[f"cout_M_{k}"] = round(etp * c / 1e6)
            row[f"part_pct_{k}"] = round(100 * etp * c / 1e6 / m, 2)
        out.append(row)
        print(f"{dh:+4.1f} {sv:9.0f} {etp:8,.0f} {row['etp_par_1000_classes']:11.1f} {row['cout_M_hors_CAS']:14,} {row['part_pct_hors_CAS']:14.2f} {row['cout_M_avec_CAS']:17,} {row['part_pct_avec_CAS']:17.2f} {row['pct_heures_maths']:15.1f}")
Path("data/processed").mkdir(exist_ok=True, parents=True)
with open("data/processed/cost_transfers_college.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print("\nLimites: transferts a classes constantes; couts DERIVES (bornes), pas primaires; chaque heure ajoutee est supposee pourvue en ETP"
      " (pas d'heures supplementaires, pas de ponderation REP+); un transfert entre matieres compense en partie (ETP libres = ETP requis ailleurs).")
print("Ecritures: data/processed/cost_transfers_college.csv")
