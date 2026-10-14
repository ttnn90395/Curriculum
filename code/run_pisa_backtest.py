"""
Projet Education -- Backtest de prevision des classements PISA (donnees reelles)
================================================================================
Lit data/raw/worldbank_pisa_<matiere>.json (telecharge par
`python code/download_data.py --pisa-wb`), construit un panel FIXE de pays
OCDE (cas complet), affiche la trajectoire de rang de quelques pays, lance le
backtest rolling-origin et prevoit le cycle suivant avec intervalles.

GARDE-FOU: les cycles > 2018 sont ecartes ici par construction (zone
confirmatoire, cf. SCOPE.md). Ce script ne sert qu'a l'exploration.

Usage:
    python code/run_pisa_backtest.py mathematics
    python code/run_pisa_backtest.py reading
    python code/run_pisa_backtest.py science
    python code/run_pisa_backtest.py mathematics --freeze   # ecrit la prevision horodatee

STATUT: teste de bout en bout sur de FAUX JSON au format de l'API (pipeline),
jamais sur les vraies donnees: ce premier passage reel dira ce qui differe.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forecast_rankings import (OECD38_ISO3, MIN_CYCLE, load_worldbank_json, build_panel,
                               relative_positions, backtest, summarize, forecast_next,
                               save_frozen_forecast)

EXPLORATORY_MAX = 2018
FOCUS = ["FRA", "DEU", "POL", "EST", "FIN"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("subject", choices=list(MIN_CYCLE))
    ap.add_argument("--data-dir", default=str(Path(__file__).resolve().parent.parent / "data" / "raw"))
    ap.add_argument("--freeze", action="store_true",
                    help="Ecrit la prevision du cycle suivant dans forecasts/ (a COMMITER avant publication)")
    args = ap.parse_args()

    path = Path(args.data_dir) / f"worldbank_pisa_{args.subject}.json"
    if not path.exists():
        sys.exit(f"Fichier absent: {path}\nLancer d'abord: python code/download_data.py --pisa-wb")

    df = load_worldbank_json(path)
    n_late = int((df["cycle"] > EXPLORATORY_MAX).sum())
    df = df[df["cycle"] <= EXPLORATORY_MAX]
    if n_late:
        print(f"[garde-fou] {n_late} observations > {EXPLORATORY_MAX} ecartees (zone confirmatoire)")

    cycles = sorted(int(c) for c in df["cycle"].unique() if c >= MIN_CYCLE[args.subject])
    oecd = df[df["country"].isin(OECD38_ISO3)]
    print(f"\n=== PISA {args.subject}: cycles retenus {cycles} (premier cycle comparable: {MIN_CYCLE[args.subject]}) ===")
    print("Pays OCDE disponibles par cycle:", {c: int(oecd[oecd.cycle == c]["country"].nunique()) for c in cycles})

    wide = build_panel(df, cycles)
    dropped = sorted(set(oecd["country"].unique()) - set(wide.index))
    print(f"\nPanel FIXE (cas complet): {len(wide)} pays x {len(cycles)} cycles")
    print(f"Pays OCDE exclus (donnee manquante a >= 1 cycle): {dropped}")
    print("ATTENTION: le rang depend du panel; il n'a de sens que dans CE panel.")
    if len(cycles) < 4 or len(wide) < 15:
        sys.exit("Panel trop petit pour un backtest: verifier les donnees telechargees.")

    ranks = wide.rank(ascending=False, method="min").astype(int)
    rel = wide - wide.mean(axis=0)
    focus = [c for c in FOCUS if c in wide.index]
    traj = pd.DataFrame({c: [f"{ranks.loc[k, c]} ({rel.loc[k, c]:+.1f})" for k in focus] for c in cycles}, index=focus)
    print("\nTrajectoire: rang dans le panel (position relative en points):")
    print(traj.to_string())

    d = relative_positions(wide)
    res = backtest(d, models=("naive", "ar1", "ar1_mom"))
    print(f"\n=== Backtest rolling-origin ({res['origin'].nunique()} plis) ===")
    print(summarize(res).to_string())
    print("\nDetail par pli (origin = indice du cycle de depart):")
    print(res.round(3).to_string(index=False))
    print("\nLecture: skill_vs_naive > 0 = bat la persistance; spearman = ordre des pays; "
          "cov80 proche de 0.8 = intervalles de rang calibres. Avec si peu de plis, "
          "de petits ecarts entre modeles ne sont PAS significatifs.")

    tab = forecast_next(d, list(wide.index), "ar1")
    nxt = cycles[-1] + (4 if cycles[-1] == 2018 else 3)
    print(f"\n=== Prevision du cycle suivant (~{nxt}) depuis les cycles <= {cycles[-1]}, modele ar1 ===")
    print(f"sigma de prevision = {tab.attrs['sigma']:.1f} points ; top_k = {tab.attrs['top_k']}")
    print(tab[tab["country"].isin(focus)].to_string(index=False))

    if args.freeze:
        out = Path(__file__).resolve().parent.parent / "forecasts" / f"pisa_{args.subject}_{nxt}_from_le{cycles[-1]}.csv"
        save_frozen_forecast(tab, out, target=f"PISA {nxt} {args.subject}", train_cycles=cycles)
        print(f"\nPrevision gelee ecrite: {out}\n-> la COMMITER dans git AVANT de telecharger les resultats {nxt}.")


if __name__ == "__main__":
    main()