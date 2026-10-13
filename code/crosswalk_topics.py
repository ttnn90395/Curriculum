"""
Projet Education -- Appariement manuel des items entre cycles (G4 maths)
===========================================================================
Remplace le matching approche par libelle (1 seul item apparie entre 2019
et 2023) par un tableau EXPLICITE et AUDITABLE: data/crosswalk_g4_math.csv.

Chaque "sujet commun" agrege, par cycle, un ou plusieurs items (moyenne).
Le niveau de confiance (high/medium/low) est une decision de
SPECIFICATION a figer AVANT de regarder les tendances: analyse primaire =
sujets "high"; robustesse = high+medium; "low" exclus.
ATTENTION: ce tableau est un jugement (le mien, a relire). Il doit etre
valide par l'auteur puis commite avant lecture des tendances.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

CROSSWALK = Path(__file__).resolve().parent.parent / "data" / "crosswalk_g4_math.csv"


def load_crosswalk(path: Path = CROSSWALK) -> pd.DataFrame:
    cw = pd.read_csv(path)
    cw["code_list"] = cw["codes"].str.split(";")
    return cw


def check_against_labels(labels_csv: Path, cw: pd.DataFrame) -> list[str]:
    """Verifie que chaque code du tableau existe dans l'export des libelles
    du cycle correspondant, et signale les items jamais utilises."""
    lab = pd.read_csv(labels_csv)
    known = {(r.cycle, r.code) for r in lab.itertuples()}
    problems, used = [], set()
    for r in cw.itertuples():
        for code in r.code_list:
            if (r.cycle, code) not in known:
                problems.append(f"code inconnu: {code} ({r.cycle}) dans {r.topic_id}")
            used.add((r.cycle, code))
    for key in sorted(known - used):
        problems.append(f"item jamais utilise ni classe: {key}")
    return problems


def topic_panel(items_by_cycle: dict, cw: pd.DataFrame, tiers=("high",)) -> pd.DataFrame:
    """Valeur par (sujet, cycle, pays) = moyenne des items du sujet; un
    pays n'a de valeur que si TOUS les items du sujet sont renseignes."""
    rows = []
    for r in cw[cw["confidence"].isin(tiers)].itertuples():
        its = {i.code: i for i in items_by_cycle.get(r.cycle, []) if i.kept}
        if not all(c in its for c in r.code_list):
            continue
        countries = set.intersection(*[set(its[c].values) for c in r.code_list])
        for country in countries:
            vals = [its[c].values[country] for c in r.code_list]
            if all(v is not None for v in vals):
                rows.append(dict(topic_id=r.topic_id, topic=r.topic, confidence=r.confidence,
                                 cycle=r.cycle, country=country,
                                 value=sum(vals) / len(vals), n_codes=len(vals)))
    return pd.DataFrame(rows)


def topic_trend(panel: pd.DataFrame, countries: list[str], c1: int, c2: int) -> pd.DataFrame:
    """Sujets presents aux deux cycles, par pays: moyenne a c1, a c2, difference."""
    sub = panel[panel["cycle"].isin([c1, c2]) & panel["country"].isin(countries)]
    pv = sub.pivot_table(index=["country", "topic_id"], columns="cycle", values="value")
    pv = pv.dropna()
    g = pv.groupby("country").agg(n_topics=(c1, "size"), **{str(c1): (c1, "mean"), str(c2): (c2, "mean")})
    g["diff"] = g[str(c2)] - g[str(c1)]
    return g.round(3)


if __name__ == "__main__":
    import sys
    cw = load_crosswalk()
    print(f"Tableau: {cw['topic_id'].nunique() - 1} sujets communs + non apparies, {len(cw)} lignes")
    print(cw.groupby("confidence")["topic_id"].nunique().to_string())
    lab = Path(sys.argv[1]) if len(sys.argv) > 1 else CROSSWALK.parent / "processed" / "item_labels_g4_math.csv"
    if lab.exists():
        problems = check_against_labels(lab, cw)
        print("\nVerification contre les libelles:", "OK, aucun probleme" if not problems else "")
        for p in problems:
            print("  -", p)