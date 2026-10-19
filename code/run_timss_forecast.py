"""Projet Education -- Prevision des classements TIMSS 4e annee MATHS (cycle 2027), modele POOLE
==========================================================================================
POURQUOI UN MODELE POOLE (et non le panel fixe de PISA): la France et la Pologne n'ont que 3
cycles G4 maths (2015, 2019, 2023): aucun panel complet de plus de 3 cycles ne les contient.
On estime donc la dynamique sur les TRANSITIONS entre cycles consecutifs, tous pays confondus.

Protocole fige (MODEL_SPEC, hash ecrit dans le verrou; commit AVANT le premier lancement):
  - donnees: data/processed/timss_g4_math_scores_long.csv (fetch_timss_trends.py);
    cycles 2003, 2007, 2011, 2015, 2019, 2023 (pas de 4 ans); 1995 exclu (ecart de 8 ans);
    exclus: participants "benchmarking" et pays evalues en 5e annee (Norvege, Afrique du Sud).
  - transition (a -> b): pays presents aux deux cycles (>= 10); position relative
    d = score - moyenne de CET ensemble au meme cycle.
  - modeles: persistance (d_b = d_a) et AR(1) poole sans constante (d_b = phi * d_a, phi par MCO
    sur toutes les transitions d'entrainement).
  - validation: origine glissante, plis = transitions 2007->2011, 2011->2015, 2015->2019,
    2019->2023 (entrainement: transitions anterieures). Un seul passage (verrou).
  - modele gele pour la prevision: ar1 (comme PISA), choisi AVANT de lire le backtest.
  - prevision TIMSS 2027: pays presents en 2019 ET 2023; rangs CONDITIONNELS a la participation
    de cet ensemble; intervalle par simulation (rangs sur tirages N(pred, sigma^2) independants).
LIMITES ASSUMEES: test non aveugle (l'auteur connait des moyennes 2015-2023 de pays majeurs);
les erreurs de pays d'un meme cycle sont correlees (pas d'inference); 4 plis dont 1 sur 2 pays
d'entrainement seulement; le rang depend de qui participe en 2027.

Usage:
  python code/run_timss_forecast.py            # backtest (1 seul passage) + prevision affichee
  python code/run_timss_forecast.py --freeze   # + ecrit forecasts/timss_g4_math_2027_from_le2023.csv
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forecast_rankings import simulate_ranks, save_frozen_forecast

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed" / "timss_g4_math_scores_long.csv"
CYCLES = [2003, 2007, 2011, 2015, 2019, 2023]
MODEL_SPEC = dict(
    version=1,
    target="position relative d = score - moyenne de l'ensemble des pays presents aux deux cycles de la transition",
    cycles=CYCLES, excluded="benchmarking participants; pays en 5e annee (grade5); 1995",
    min_set_size=10,
    models_compared=["naive", "ar1_pooled_noconst"], frozen_model="ar1_pooled_noconst",
    folds="transitions 2007->2011, 2011->2015, 2015->2019, 2019->2023; entrainement = transitions anterieures",
    interval="rangs sur 2000 (backtest) / 5000 (prevision) tirages N(pred, sigma^2) independants; p10-p90",
    forecast_set="pays presents en 2019 et 2023; rangs conditionnels a leur participation en 2027",
    top_k=10,
)
SPEC_HASH = hashlib.sha256(json.dumps(MODEL_SPEC, sort_keys=True).encode()).hexdigest()[:16]
FOCUS = ["France", "Germany", "Poland", "Finland", "England", "Japan", "Korea, Rep. of", "Singapore"]


def load_scores(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[~df["benchmarking"].astype(bool) & ~df["grade5"].astype(bool) & df["cycle"].isin(CYCLES)]
    return df.pivot_table(index="country", columns="cycle", values="score")


def transitions(wide: pd.DataFrame) -> dict:
    out = {}
    for a, b in zip(CYCLES[:-1], CYCLES[1:]):
        if a in wide.columns and b in wide.columns:
            sub = wide[[a, b]].dropna()
            if len(sub) >= MODEL_SPEC["min_set_size"]:
                out[(a, b)] = (list(sub.index), (sub[a] - sub[a].mean()).to_numpy(),
                               (sub[b] - sub[b].mean()).to_numpy())
    return out


def fit(trans: dict, keys: list):
    d0 = np.concatenate([trans[k][1] for k in keys])
    d1 = np.concatenate([trans[k][2] for k in keys])
    phi = float((d0 * d1).sum() / (d0 * d0).sum())
    return phi, float(np.sqrt(np.mean((d1 - phi * d0) ** 2))), float(np.sqrt(np.mean((d1 - d0) ** 2)))


def backtest(trans: dict, n_sims: int = 2000) -> pd.DataFrame:
    keys = sorted(trans)
    rows = []
    for i in range(1, len(keys)):
        tr, test = keys[:i], keys[i]
        phi, s_ar, s_nv = fit(trans, tr)
        _, d0, d1 = trans[test]
        act_rank = rankdata(-d1, method="min")
        for m, pred, sg in (("naive", d0, s_nv), ("ar1", phi * d0, s_ar)):
            ranks = simulate_ranks(pred, sg, n_sims)
            lo, hi = np.percentile(ranks, [10, 90], axis=0)
            rows.append(dict(test=f"{test[0]}->{test[1]}", n=len(d0), n_train_trans=len(tr), model=m, phi=phi if m == "ar1" else 1.0,
                             mse=float(np.mean((pred - d1) ** 2)),
                             rho=float(spearmanr(pred, d1).correlation),
                             mae_rank=float(np.mean(np.abs(rankdata(-pred, method="min") - act_rank))),
                             cov80=float(np.mean((act_rank >= lo) & (act_rank <= hi)))))
    return pd.DataFrame(rows)


def summarize(res: pd.DataFrame) -> pd.DataFrame:
    base = res[res.model == "naive"]["mse"].mean()
    out = []
    for m, g in res.groupby("model"):
        out.append(dict(model=m, folds=len(g), rmse=np.sqrt(g.mse.mean()), skill_vs_naive=1 - g.mse.mean() / base,
                        spearman=g.rho.mean(), mae_rank=g.mae_rank.mean(), cov80=g.cov80.mean()))
    return pd.DataFrame(out).set_index("model").round(3)


def forecast_2027(wide: pd.DataFrame, trans: dict, n_sims: int = 5000) -> pd.DataFrame:
    phi, sigma, _ = fit(trans, sorted(trans))
    sub = wide[[2019, 2023]].dropna()
    d23 = (sub[2023] - sub[2023].mean()).to_numpy()
    pred = phi * d23
    ranks = simulate_ranks(pred, sigma, n_sims)
    q10, q50, q90 = np.percentile(ranks, [10, 50, 90], axis=0)
    out = pd.DataFrame(dict(country=list(sub.index), score_2023=sub[2023].round(0).to_numpy(),
                            rank_2023=rankdata(-d23, method="min").astype(int),
                            pred_relative=pred.round(1), rank_p10=q10, rank_median=q50, rank_p90=q90,
                            p_top_k=(ranks <= MODEL_SPEC["top_k"]).mean(axis=0).round(3)))
    out.attrs.update(model="ar1_pooled_noconst", sigma=sigma, beta=[phi], top_k=MODEL_SPEC["top_k"])
    return out.sort_values("rank_median").reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--force", action="store_true", help="IGNORE le verrou (a proscrire; journalise)")
    a = ap.parse_args()
    if not DATA.exists():
        sys.exit(f"Absent: {DATA} (python code/fetch_timss_trends.py)")
    lock = ROOT / "forecasts" / "confirmatory_timss_g4_math.lock.json"
    freeze_only = False
    if lock.exists() and not a.force:
        if a.freeze and json.loads(lock.read_text()).get("spec_hash") == SPEC_HASH:
            freeze_only = True
            print("[verrou present, spec identique: backtest non refait, ecriture de la prevision seulement]")
        else:
            sys.exit(f"Verrou present: {lock}\nBacktest deja execute avec cette specification. "
                     f"(--freeze pour n'ecrire que la prevision.)")
    wide = load_scores(DATA)
    trans = transitions(wide)
    print(f"\n=== TIMSS G4 maths: {wide.shape[0]} pays, transitions utilisables: "
          f"{ {f'{a_}->{b_}': len(v[0]) for (a_, b_), v in trans.items()} } ===")
    if len(trans) < 3:
        sys.exit("Trop peu de transitions: verifier timss_g4_math_scores_long.csv.")
    if not freeze_only:
        res = backtest(trans)
        print("\nBacktest (un seul passage):")
        print(res.round(3).to_string(index=False))
        print("\nResume (descriptif; erreurs de pays correlees, pas d'inference):")
        print(summarize(res).to_string())
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(json.dumps(dict(subject="timss_g4_math", run_on=str(datetime.date.today()), spec_hash=SPEC_HASH,
                                        spec=MODEL_SPEC, forced=bool(a.force),
                                        results=res.round(4).to_dict(orient="records")), indent=2, default=float))
        print(f"\nVerrou ecrit: {lock} (spec {SPEC_HASH})")
    tab = forecast_2027(wide, trans)
    print(f"\n=== Prevision TIMSS 2027 (G4 maths) depuis <= 2023: phi = {tab.attrs['beta'][0]:.3f}, "
          f"sigma = {tab.attrs['sigma']:.1f} pts, {len(tab)} pays ===")
    print(tab[tab.country.isin(FOCUS)].to_string(index=False))
    if a.freeze:
        out = ROOT / "forecasts" / "timss_g4_math_2027_from_le2023.csv"
        save_frozen_forecast(tab, out, target="TIMSS 2027 G4 mathematics", train_cycles=CYCLES)
        print(f"\nEcrit: {out}\n-> COMMITER maintenant, avant la publication de TIMSS 2027.")


if __name__ == "__main__":
    main()
