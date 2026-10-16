"""
Projet Education -- Scores PISA 2022/2025 (saisie manuelle validee)
===================================================================
La Banque mondiale s'arrete a 2018. Les moyennes nationales 2022 et 2025 sont
a recopier depuis les tableaux d'annexe OFFICIELS de l'OCDE
(PISA 2022 Results Vol. I, tables I.B1.2.1 / I.B1.2.2 / I.B1.2.3 ; l'equivalent
dans PISA 2025 Results Vol. I). Rien n'est saisi de memoire par le code.

Usage:
    python code/pisa_extended.py --make-template   # cree data/manual/pisa_means_2022_2025.csv (vide)
    # ... remplir la colonne `mean` (+ `source_table`) ...
    python code/pisa_extended.py --check           # valide le fichier rempli

Format: iso3,subject,cycle,mean,source_table
  subject in {mathematics, reading, science}; cycle in {2022, 2025}
Laisser `mean` vide = donnee absente (le pays sera exclu du panel).
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forecast_rankings import OECD38_ISO3

SUBJECTS = ("mathematics", "reading", "science")
NEW_CYCLES = (2022, 2025)
DEFAULT = Path(__file__).resolve().parent.parent / "data" / "manual" / "pisa_means_2022_2025.csv"
# Verifications croisees avec les chiffres cites par l'auteur du projet
# (maths France: 474 en 2022, 458 en 2025). Avertissement, pas blocage.
SANITY = {("FRA", "mathematics", 2022): 474, ("FRA", "mathematics", 2025): 458}


def make_template(path: Path = DEFAULT) -> None:
    if path.exists():
        sys.exit(f"{path} existe deja: pas ecrase.")
    rows = [dict(iso3=c, subject=s, cycle=y, mean="", source_table="")
            for s in SUBJECTS for y in NEW_CYCLES for c in OECD38_ISO3]
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"Gabarit ecrit: {path} ({len(rows)} lignes a remplir)")


def load_manual(path: Path = DEFAULT, verbose: bool = True) -> pd.DataFrame:
    """Retourne un DataFrame au meme format que load_worldbank_json
    (country, cycle, score), apres validation stricte."""
    if not Path(path).exists():
        sys.exit(f"Fichier absent: {path}\nLancer: python code/pisa_extended.py --make-template")
    df = pd.read_csv(path, dtype={"iso3": str, "subject": str, "source_table": str})
    need = {"iso3", "subject", "cycle", "mean", "source_table"}
    if not need <= set(df.columns):
        sys.exit(f"Colonnes manquantes: {need - set(df.columns)}")
    errs = []
    bad = df[~df["subject"].isin(SUBJECTS)]
    if len(bad):
        errs.append(f"matiere inconnue: {sorted(bad['subject'].unique())}")
    bad = df[~df["cycle"].isin(NEW_CYCLES)]
    if len(bad):
        errs.append(f"cycle hors {NEW_CYCLES}: {sorted(bad['cycle'].unique())}")
    bad = df[~df["iso3"].isin(OECD38_ISO3)]
    if len(bad):
        errs.append(f"code pays hors OCDE-38: {sorted(bad['iso3'].unique())}")
    if df.duplicated(["iso3", "subject", "cycle"]).any():
        errs.append("doublons (iso3, subject, cycle)")
    filled = df.dropna(subset=["mean"]).copy()
    filled["mean"] = pd.to_numeric(filled["mean"], errors="coerce")
    if filled["mean"].isna().any():
        errs.append("valeurs non numeriques dans `mean`")
    out_range = filled[(filled["mean"] < 250) | (filled["mean"] > 650)]
    if len(out_range):
        errs.append(f"scores hors [250, 650] (faute de frappe ?):\n{out_range.to_string(index=False)}")
    nosrc = filled[filled["source_table"].isna() | (filled["source_table"].str.strip() == "")]
    if len(nosrc):
        errs.append(f"{len(nosrc)} lignes remplies SANS source_table (tracabilite obligatoire)")
    if errs:
        sys.exit("ERREURS de validation:\n- " + "\n- ".join(errs))
    for (iso, s, y), ref in SANITY.items():
        row = filled[(filled.iso3 == iso) & (filled.subject == s) & (filled.cycle == y)]
        if len(row) and abs(float(row["mean"].iloc[0]) - ref) > 1.5:
            print(f"[AVERTISSEMENT] {iso} {s} {y}: {row['mean'].iloc[0]} vs {ref} cite dans le projet -- verifier.")
    if verbose:
        for s in SUBJECTS:
            for y in NEW_CYCLES:
                n = len(filled[(filled.subject == s) & (filled.cycle == y)])
                print(f"  {s:12s} {y}: {n}/38 pays renseignes")
    return filled.rename(columns={"iso3": "country", "mean": "score"})[["country", "subject", "cycle", "score"]]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--make-template", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--file", default=str(DEFAULT))
    a = ap.parse_args()
    if a.make_template:
        make_template(Path(a.file))
    elif a.check:
        load_manual(Path(a.file))
        print("Validation OK.")
    else:
        ap.print_help()