#!/usr/bin/env python3
"""cost_transfers_lycee.py -- extension de cost_transfers.py au lycee general et technologique public (EXPLORATOIRE).
Transfert: +dh heure hebdomadaire de maths par classe de lycee GT (41 206 classes, seconde + premiere + terminale).
Hypothese (declaree): classes reparties en tiers egaux entre seconde, premiere, terminale; ponderation 1.1 (decret 2014-940 art.6)
appliquee aux heures de premiere et terminale, ce qui augmente le besoin en ETP d'un facteur (1 + 2*1.1)/3, borne haute car seules
les 10 premieres heures d'un service sont ponderees. Aucune grille horaire de maths du lycee n'est utilisee: le calcul est un cout
marginal par heure ajoutee, independant de l'horaire existant. Cout = moyenne P141 (voir parameters_teachers_cost.csv)."""
import csv
from pathlib import Path
P = {r["id"]: r["value"] for r in csv.DictReader(open("data/parameters_teachers_cost.csv"))}
f = lambda k: float(P[k])
classes = f("classes_lycee_GT_public")
pond = (1 + 2 * f("ponderation_cycle_terminal")) / 3
mission_hc, mission_ac = f("credits_paiement_mission_hors_CAS"), f("mission_CP_avec_CAS")
costs = {"hors_CAS": (f("cout_ens2d_hors_CAS"), mission_hc), "avec_CAS": (f("cout_ens2d_avec_CAS"), mission_ac)}
print(f"Lycee GT public: {classes:,.0f} classes; facteur de ponderation (hypothese tiers egaux) {pond:.4f}")
print(f"\n{'dh':>4} {'service':>8} {'pond':>5} {'ETP':>8} {'cout M hCAS':>12} {'part % hCAS':>12} {'cout M avecCAS':>15} {'part % avecCAS':>15}")
out = []
for dh in (-1.0, 0.5, 1.0):
    for sv_name in ("service_certifies", "service_agreges"):
        for pw in (1.0, pond):
            sv = f(sv_name); etp = classes * dh * pw / sv
            row = dict(dh=dh, service=sv, ponderation=round(pw, 4), etp=round(etp))
            for k, (c, m) in costs.items():
                row[f"cout_M_{k}"] = round(etp * c / 1e6); row[f"part_pct_{k}"] = round(100 * etp * c / 1e6 / m, 2)
            out.append(row)
            print(f"{dh:+4.1f} {sv:8.0f} {pw:5.2f} {etp:8,.0f} {row['cout_M_hors_CAS']:12,} {row['part_pct_hors_CAS']:12.2f} {row['cout_M_avec_CAS']:15,} {row['part_pct_avec_CAS']:15.2f}")
Path("data/processed").mkdir(exist_ok=True, parents=True)
with open("data/processed/cost_transfers_lycee.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print("\nLimites: classes constantes; moyenne de programme P141, pas un cout enseignant; pas d'heures supplementaires; options et"
      " specialites non modelisees; le nombre de classes (41 206) est lu par extraction et reste a recouper.")
print("Ecritures: data/processed/cost_transfers_lycee.csv")
