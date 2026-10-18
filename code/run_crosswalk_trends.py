"""Projet Education -- Tendances de couverture curriculaire G4 maths par SUJET COMMUN
===================================================================================
Utilise le tableau explicite data/crosswalk_g4_math.csv (niveaux de confiance
high/medium/low) et l'encodage valide (2019: 1->1.0, 2->0.5, 3->0.0, soutenu par le
controle interne de la grille des grades).

Specification (a figer AVANT de lire les tendances, cf. crosswalk_topics.py):
  - analyse PRIMAIRE : sujets "high" ; ROBUSTESSE : high + medium ; "low" exclus.
  - un pays n'a de valeur pour un sujet que si tous les items agreges sont renseignes.
  - valeur = couverture "intended" declaree par le coordinateur national (NRC),
    PAS ce qui est enseigne ni appris. Echelle 0 / 0.5 / 1 (equidistance supposee).
BRUIT: ~11 % des reponses basculent d'un cycle a l'autre pour un meme pays/sujet
(reponses de coordinateurs differents): les ecarts par pays sont a lire comme
descriptifs; on regarde surtout la position de la France par rapport a la
distribution des pays.

Usage: python code/run_crosswalk_trends.py
Sorties: data/processed/crosswalk_topic_values.csv, crosswalk_topic_trends.csv
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import extract_multicycle_coverage as emc
except ImportError:
    import extract_multi_coverage as emc
from crosswalk_topics import load_crosswalk, topic_panel, topic_trend

FOCUS = ["France", "Germany", "Poland"]
PAIRS = [(2015, 2019), (2019, 2023), (2015, 2023)]
MIN_TOPICS = 3


def load_items(data_dir: Path) -> dict:
    files = {
        2015: emc.CycleFile(2015, data_dir / "timss2015_curriculum_g4.zip", "T15_G4_Mathematics Module"),
        2019: emc.CycleFile(2019, data_dir / "timss2019_curriculum_g4.zip", "T19_G4_Mathematics Module"),
        2023: emc.CycleFile(2023, data_dir / "timss2023_curriculum_g4.xlsx", "T23_G4_Mathematics Module"),
    }
    out = {}
    for y, cf in files.items():
        if not cf.path.exists():
            sys.exit(f"MANQUANT: {cf.path}")
        out[y] = emc.read_items(cf)
    return out


def analyse(items_by_cycle: dict, cw: pd.DataFrame, tiers, label: str, outdir: Path | None):
    panel = topic_panel(items_by_cycle, cw, tiers=tiers)
    print("\n" + "=" * 72)
    print(f"{label}: sujets {sorted(panel['topic_id'].unique())}")
    print("=" * 72)
    mat = panel[panel["country"].isin(FOCUS)].pivot_table(index=["topic_id", "topic"], columns=["country", "cycle"], values="value")
    print("\nValeurs par sujet (0 = hors programme, 0.5 = eleves avances, 1 = tous):")
    print(mat.round(2).to_string())
    allc = sorted(panel["country"].unique())
    rows = []
    for c1, c2 in PAIRS:
        tr = topic_trend(panel, allc, c1, c2)
        tr = tr[tr["n_topics"] >= MIN_TOPICS].copy()
        if tr.empty:
            continue
        tr["pair"] = f"{c1}->{c2}"
        tr["rank_diff"] = tr["diff"].rank(ascending=False, method="min")
        tr["country"] = tr.index
        rows.append(tr.reset_index(drop=True))
        f = tr.loc[tr.index.isin(FOCUS)].drop(columns=["pair", "country"])
        print(f"\n{c1} -> {c2}: {len(tr)} pays avec >= {MIN_TOPICS} sujets communs; "
              f"mediane des ecarts = {tr['diff'].median():+.3f}")
        print(f.to_string())
        if "France" in tr.index:
            fr = tr.loc["France"]
            print(f"   France: ecart {fr['diff']:+.3f}, rang {int(fr['rank_diff'])}/{len(tr)} "
                  f"(1 = plus forte hausse de couverture)")
    trends = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if outdir is not None:
        outdir.mkdir(parents=True, exist_ok=True)
        tag = label.split()[0].lower()
        panel.to_csv(outdir / f"crosswalk_topic_values_{tag}.csv", index=False)
        trends.to_csv(outdir / f"crosswalk_topic_trends_{tag}.csv", index=False)
    return panel, trends


def main(data_dir: Path | None = None, outdir: Path | None = None):
    root = Path(__file__).resolve().parent.parent
    data_dir = data_dir or root / "data" / "raw"
    outdir = outdir or root / "data" / "processed"
    cw = load_crosswalk(root / "data" / "crosswalk_g4_math.csv")
    items = load_items(data_dir)
    analyse(items, cw, ("high",), "PRIMAIRE (high)", outdir)
    analyse(items, cw, ("high", "medium"), "ROBUSTESSE (high+medium)", outdir)
    print("\nRappel: couverture declaree (curriculum prevu), pas enseignee ni apprise; "
          "ces tendances sont descriptives et ne sont pas un test causal.")


if __name__ == "__main__":
    main()