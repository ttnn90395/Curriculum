"""Assemble TOUS les scores PISA disponibles dans data/processed/pisa_scores_long.csv.

  * 2000-2018 : Banque mondiale (EdStats), TOUS les pays/economies, 3 matieres
                (data/raw/worldbank_pisa_<matiere>.json, via download_data.py --pisa-wb)
  * 2022, 2025 : data/manual/pisa_means_2022_2025.csv (38 pays OCDE seulement)
                (remplir via fetch_pisa_web.py)

Sortie longue: iso3, matiere, cycle, score, source. Un controle de coherence est
affiche (nombre de pays par cycle). Limite assumee: 2022/2025 = OCDE seulement.
Comparabilite des echelles: voir MIN_CYCLE (maths >= 2003, lecture >= 2000,
sciences >= 2006); les cycles anterieurs sont conserves mais marques comparable=False.

Usage: python code/build_pisa_history.py
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, "code")
from forecast_rankings import load_worldbank_json, MIN_CYCLE

ROOT = Path(".")
rows = []
for s in ("mathematics", "reading", "science"):
    p = ROOT / "data/raw" / f"worldbank_pisa_{s}.json"
    if not p.exists():
        sys.exit(f"Absent: {p} -> python code/download_data.py --pisa-wb")
    d = load_worldbank_json(p)
    d["subject"], d["source"] = s, "World Bank EdStats (OECD PISA)"
    rows.append(d.rename(columns={"country": "iso3"})[["iso3", "name", "subject", "cycle", "score", "source"]])

man_path = ROOT / "data/manual/pisa_means_2022_2025.csv"
if man_path.exists():
    m = pd.read_csv(man_path).dropna(subset=["mean"])
    m = m.rename(columns={"mean": "score", "source_table": "source"})
    m["name"] = None
    rows.append(m[["iso3", "name", "subject", "cycle", "score", "source"]])
else:
    print("[note] pas de fichier 2022/2025 (fetch_pisa_web.py).")

al = pd.concat(rows, ignore_index=True)
al["cycle"] = al["cycle"].astype(int)
al["comparable"] = al.apply(lambda r: r["cycle"] >= MIN_CYCLE[r["subject"]], axis=1)
dup = al.duplicated(["iso3", "subject", "cycle"], keep=False)
if dup.any():
    print(f"[ATTENTION] {int(dup.sum())} lignes en double (iso3, matiere, cycle):")
    print(al[dup].sort_values(["iso3", "subject", "cycle"]).head(20).to_string(index=False))
al = al.sort_values(["subject", "iso3", "cycle"])
out = ROOT / "data/processed/pisa_scores_long.csv"
out.parent.mkdir(parents=True, exist_ok=True)
al.to_csv(out, index=False)
print(f"\nEcrit: {out}  ({len(al)} lignes)")
print("\nNombre de pays par matiere et cycle:")
print(al.pivot_table(index="subject", columns="cycle", values="iso3", aggfunc="nunique").fillna(0).astype(int).to_string())
print("\nFrance:")
print(al[al.iso3 == "FRA"].pivot_table(index="subject", columns="cycle", values="score").round(0).to_string())