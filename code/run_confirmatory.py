"""
Projet Education -- Test confirmatoire UNIQUE du modele gele + prevision PISA 2028
==================================================================================
Protocole (SCOPE.md / Plan.txt):
  1. Modele et panel geles AVANT lecture de 2022/2025: voir MODEL_SPEC (ci-dessous),
     dont l'empreinte (hash) est ecrite dans le verrou. Le commit git de ce
     fichier, fait AVANT le premier lancement, sert de pre-enregistrement.
  2. Panel = pays OCDE complets sur les cycles <= 2018 (defini sans 2022/2025),
     puis on exige 2022 et 2025 pour tous ces pays (sinon arret, liste affichee).
  3. Test A: entrainement <= 2018 -> 2022.  Test B: entrainement <= 2022 -> 2025.
     Compare a la persistance (naive). Chaque test est execute UNE fois par
     matiere: un verrou forecasts/confirmatory_<matiere>.lock.json empeche de
     relancer et de "ajuster" ensuite (--force existe mais est journalise et a
     proscrire).
  4. Prevision PISA 2028 depuis <= 2025 (--freeze l'ecrit, a commiter avant
     publication de PISA 2028).

LIMITE ASSUMEE: l'auteur connait deja les grandes lignes de 2022/2025; ce test
n'est donc pas aveugle. Il reste informatif (on ne peut plus changer le modele
sans le declarer), mais seule la prevision 2028 est veritablement prospective.
Autre limite: le pas 2018->2022 vaut 4 ans (COVID), les autres 3 ans.

Usage:
    python code/run_confirmatory.py mathematics
    python code/run_confirmatory.py mathematics --freeze
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forecast_rankings import (OECD38_ISO3, MIN_CYCLE, load_worldbank_json, build_panel,
                               relative_positions, backtest, summarize, forecast_next,
                               save_frozen_forecast)
from pisa_extended import load_manual

MODEL_SPEC = dict(
    version=2,
    target="position relative d = score - moyenne du panel fixe au cycle",
    models_compared=["naive", "ar1"],          # ar1_mom ecarte: gain indiscernable de ar1, parcimonie
    frozen_model="ar1",
    ridge=1e-3, interval="Monte Carlo p10-p90, 2000 sims (backtest) / 5000 (prevision)",
    panel="OCDE complets sur cycles <= 2018, MIN_CYCLE par matiere; puis retrait des pays "
          "n'ayant pas participe a 2022 ou 2025 (ex.: le Luxembourg n'a pas participe a PISA 2022)",
    max_nonparticipants_dropped=3,
    train_limit_for_exploration=2018,
)
SPEC_HASH = hashlib.sha256(json.dumps(MODEL_SPEC, sort_keys=True).encode()).hexdigest()[:16]
ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("subject", choices=list(MIN_CYCLE))
    ap.add_argument("--freeze", action="store_true", help="ecrit la prevision 2028 dans forecasts/")
    ap.add_argument("--force", action="store_true", help="IGNORE le verrou (a proscrire; journalise)")
    a = ap.parse_args()

    wb_path = ROOT / "data" / "raw" / f"worldbank_pisa_{a.subject}.json"
    if not wb_path.exists():
        sys.exit(f"Absent: {wb_path} (python code/download_data.py --pisa-wb)")
    lock = ROOT / "forecasts" / f"confirmatory_{a.subject}.lock.json"
    freeze_only = False
    if lock.exists() and not a.force:
        same = json.loads(lock.read_text()).get("spec_hash") == SPEC_HASH
        if a.freeze and same:
            freeze_only = True      # test deja fait avec CETTE spec: on ne refait que la prevision 2028
            print(f"[verrou present, spec identique: tests non refaits, ecriture de la prevision 2028 seulement]")
        else:
            sys.exit(f"Verrou present: {lock}\nLe test confirmatoire de {a.subject} a deja ete execute "
                     f"(voir ce fichier). Pas de relance (ajouter --freeze pour n'ecrire que la prevision 2028).")

    wb = load_worldbank_json(wb_path)
    wb = wb[wb["cycle"] <= 2018]
    man = load_manual(verbose=False)
    man = man[man["subject"] == a.subject][["country", "cycle", "score"]]
    full = pd.concat([wb[["country", "cycle", "score"]], man], ignore_index=True)

    old_cycles = sorted(int(c) for c in wb["cycle"].unique() if c >= MIN_CYCLE[a.subject])
    all_cycles = old_cycles + [2022, 2025]
    panel_old = build_panel(wb, old_cycles)                    # panel defini SANS 2022/2025
    wide = build_panel(full, all_cycles, countries=list(panel_old.index))
    lost = sorted(set(panel_old.index) - set(wide.index))
    print(f"\n=== {a.subject}: panel fixe {len(panel_old)} pays (defini <= 2018); cycles {all_cycles} ===")
    if len(lost) > MODEL_SPEC["max_nonparticipants_dropped"]:
        sys.exit(f"Trop de pays du panel sans donnee 2022/2025: {lost} (max "
                 f"{MODEL_SPEC['max_nonparticipants_dropped']}). Completer data/manual/pisa_means_2022_2025.csv.")
    if lost:
        print(f"Retrait PREVU AU PROTOCOLE (non-participation a 2022 et/ou 2025): {lost}")
        wide = build_panel(full, all_cycles, countries=[c for c in panel_old.index if c not in lost])
        print(f"Panel du test: {len(wide)} pays")

    d = relative_positions(wide)
    iA, iB = len(old_cycles) - 1, len(old_cycles)             # origines: dernier <=2018, puis 2022
    if not freeze_only:
        res = backtest(d, models=("naive", "ar1"), origins=[iA, iB])
        res["test"] = res["origin"].map({iA: "A: <=2018 -> 2022", iB: "B: <=2022 -> 2025"})
        print("\nTest confirmatoire (un seul passage):")
        print(res.round(3).to_string(index=False))
        print("\nResume (2 plis, descriptif; aucune inference sur 2 plis):")
        print(summarize(res).to_string())

    focus = [c for c in ["FRA", "DEU", "POL", "FIN"] if c in wide.index]
    ranks = wide.rank(ascending=False, method="min").astype(int)
    rel = wide - wide.mean(axis=0)
    print("\nTrajectoire (rang dans le panel, position relative):")
    print(pd.DataFrame({c: [f"{ranks.loc[k, c]} ({rel.loc[k, c]:+.1f})" for k in focus] for c in all_cycles},
                       index=focus).to_string())

    if not freeze_only:
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(json.dumps(dict(subject=a.subject, run_on=str(datetime.date.today()), spec_hash=SPEC_HASH,
                                        spec=MODEL_SPEC, forced=bool(a.force),
                                        results=res.round(4).to_dict(orient="records")), indent=2, default=float))
        print(f"\nVerrou ecrit: {lock} (spec {SPEC_HASH})")

    tab = forecast_next(d, list(wide.index), MODEL_SPEC["frozen_model"])
    print(f"\n=== Prevision PISA 2028 depuis <= 2025, modele {MODEL_SPEC['frozen_model']} ===")
    print(f"sigma = {tab.attrs['sigma']:.1f} points ; top_k = {tab.attrs['top_k']}")
    print(tab[tab["country"].isin(focus)].to_string(index=False))
    if a.freeze:
        out = ROOT / "forecasts" / f"pisa_{a.subject}_2028_from_le2025.csv"
        save_frozen_forecast(tab, out, target=f"PISA 2028 {a.subject}", train_cycles=all_cycles)
        print(f"\nEcrit: {out}\n-> COMMITER maintenant (git add forecasts/ && git commit), avant PISA 2028.")


if __name__ == "__main__":
    main()
