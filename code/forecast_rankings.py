"""
Projet Education -- Prevision des classements (Partie 3, volet prospectif)
===========================================================================
On NE prevoit PAS le rang directement. On prevoit la position relative
d_{i,t} = score_{i,t} - moyenne du panel fixe au cycle t (ce qui elimine les
chocs communs a tous les pays, ex. COVID), puis on derive le rang par
simulation Monte Carlo, avec un intervalle.

Modeles (tous sur d, panel poole sur les pays):
  naive      : d_{t+1} = d_t                         (persistance)
  ar1        : d_{t+1} = a + b d_t                   (retour vers la moyenne)
  ar1_mom    : d_{t+1} = a + b d_t + c (d_t - d_{t-1})   (+ elan)
  ar1_mom_x  : ar1_mom + variables explicatives (ex: curriculum)

Evaluation: rolling-origin (on n'utilise a l'origine t que les transitions
connues a t), comparee a la persistance; calibration des intervalles de rang.

DISCIPLINE (SCOPE.md / Plan.txt): n'entrainer et ne comparer les modeles que
sur les cycles <= 2018. Les cycles 2022/2025 ne servent qu'au test unique
d'un modele GELE; la vraie prevision prospective (PISA 2028) est ecrite dans
un fichier horodate avant que le resultat n'existe (save_frozen_forecast).

STATUT: teste sur donnees SYNTHETIQUES uniquement. Non branche a de vraies
donnees PISA (voir load_worldbank_json + download_data.py --pisa-wb).
"""
from __future__ import annotations
import json
import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata

OECD38_ISO3 = [
    "AUS", "AUT", "BEL", "CAN", "CHL", "COL", "CRI", "CZE", "DNK", "EST", "FIN",
    "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ISR", "ITA", "JPN", "KOR", "LVA",
    "LTU", "LUX", "MEX", "NLD", "NZL", "NOR", "POL", "PRT", "SVK", "SVN", "ESP",
    "SWE", "CHE", "TUR", "GBR", "USA",
]
# Premier cycle comparable par matiere (convention OCDE, A CONFIRMER dans les
# notes techniques): echelle de maths re-ancree en 2003, sciences en 2006.
MIN_CYCLE = {"mathematics": 2003, "reading": 2000, "science": 2006}
MODELS = ("naive", "ar1", "ar1_mom", "ar1_mom_x")


# ---------------------------------------------------------------- donnees
def load_worldbank_json(path: str | Path) -> pd.DataFrame:
    """Lit un JSON de l'API World Bank (format [meta, [enregistrements]])."""
    data = json.loads(Path(path).read_text())
    if not (isinstance(data, list) and len(data) == 2 and isinstance(data[1], list)):
        raise ValueError(f"Format World Bank inattendu: {str(data)[:200]}")
    if data[0].get("pages", 1) > 1:
        raise ValueError("Resultat pagine: relancer avec per_page plus grand")
    rows = [dict(country=r.get("countryiso3code") or r["country"]["id"],
                 name=r["country"]["value"], cycle=int(r["date"]), score=float(r["value"]))
            for r in data[1] if r.get("value") is not None]
    return pd.DataFrame(rows)


def build_panel(df: pd.DataFrame, cycles: list[int], countries=OECD38_ISO3) -> pd.DataFrame:
    """Panel FIXE (cas complet): pays presents a tous les cycles demandes."""
    sub = df[df["cycle"].isin(cycles) & df["country"].isin(countries)]
    wide = sub.pivot_table(index="country", columns="cycle", values="score")
    wide = wide.reindex(columns=sorted(cycles)).dropna()
    return wide


def relative_positions(wide: pd.DataFrame) -> np.ndarray:
    return (wide - wide.mean(axis=0)).to_numpy()


# ---------------------------------------------------------------- modeles
def _design(d: np.ndarray, t: int, use_mom: bool, x_t=None) -> np.ndarray:
    cols = [np.ones(d.shape[0]), d[:, t]]
    if use_mom:
        cols.append(d[:, t] - d[:, t - 1])
    if x_t is not None:
        cols.extend(list(np.asarray(x_t).T))
    return np.column_stack(cols)


def fit_predict(d: np.ndarray, origin: int, model: str, ridge: float = 1e-3, extra=None):
    """Prevoit d[:, origin+1] avec les seules transitions connues a l'origine.
    extra: dict {indice_de_cycle: tableau (n, k)} de variables explicatives."""
    if model == "naive":
        diffs = [d[:, tp + 1] - d[:, tp] for tp in range(origin)]
        if not diffs:
            raise ValueError("aucune transition d'entrainement")
        return d[:, origin].copy(), float(np.sqrt(np.mean(np.concatenate(diffs) ** 2))), None
    use_mom = model in ("ar1_mom", "ar1_mom_x")
    use_x = model == "ar1_mom_x"
    Xs, ys = [], []
    for tp in range(1 if use_mom else 0, origin):          # tp + 1 <= origin
        if use_x and (extra is None or tp not in extra):
            continue
        Xs.append(_design(d, tp, use_mom, extra[tp] if use_x else None))
        ys.append(d[:, tp + 1])
    if not Xs:
        raise ValueError("aucune transition d'entrainement")
    X, y = np.vstack(Xs), np.concatenate(ys)
    p = X.shape[1]
    pen = ridge * np.eye(p)
    pen[0, 0] = 0.0
    beta = np.linalg.solve(X.T @ X + pen, X.T @ y)
    resid = y - X @ beta
    sigma = float(np.sqrt(resid @ resid / max(len(y) - p, 1)))
    if use_x and (extra is None or origin not in extra):
        raise ValueError("variables explicatives absentes a l'origine")
    pred = _design(d, origin, use_mom, extra[origin] if use_x else None) @ beta
    return pred, sigma, beta


def simulate_ranks(pred: np.ndarray, sigma: float, n_sims: int = 3000, seed: int = 0) -> np.ndarray:
    """Rangs simules (1 = meilleur): tirages independants N(pred, sigma^2)."""
    rng = np.random.default_rng(seed)
    draws = pred[None, :] + sigma * rng.standard_normal((n_sims, len(pred)))
    return 1 + (draws[:, None, :] > draws[:, :, None]).sum(axis=2)


# ---------------------------------------------------------------- evaluation
def backtest(d: np.ndarray, models=MODELS, origins=None, extra=None, n_sims: int = 2000) -> pd.DataFrame:
    n, T = d.shape
    origins = range(2, T - 1) if origins is None else origins
    rows = []
    for t in origins:
        actual = d[:, t + 1]
        act_rank = rankdata(-actual, method="min")
        for m in models:
            try:
                pred, sigma, _ = fit_predict(d, t, m, extra=extra)
            except ValueError:
                continue
            ranks = simulate_ranks(pred, sigma, n_sims)
            lo, hi = np.percentile(ranks, [10, 90], axis=0)
            rows.append(dict(
                origin=t, model=m, mse=float(np.mean((pred - actual) ** 2)),
                rho=float(spearmanr(pred, actual).correlation),
                mae_rank=float(np.mean(np.abs(rankdata(-pred, method="min") - act_rank))),
                cov80=float(np.mean((act_rank >= lo) & (act_rank <= hi)))))
    return pd.DataFrame(rows)


def summarize(res: pd.DataFrame) -> pd.DataFrame:
    naive = res[res["model"] == "naive"].set_index("origin")["mse"]
    out = []
    for m, g in res.groupby("model"):
        base = naive.reindex(g["origin"]).mean()
        out.append(dict(model=m, folds=len(g), rmse=np.sqrt(g["mse"].mean()),
                        skill_vs_naive=1 - g["mse"].mean() / base,
                        spearman=g["rho"].mean(), mae_rank=g["mae_rank"].mean(),
                        cov80=g["cov80"].mean()))
    return pd.DataFrame(out).set_index("model").round(3)


# ---------------------------------------------------------------- prevision
def forecast_next(d: np.ndarray, countries: list[str], model: str, extra=None,
                  n_sims: int = 5000, top_k: int = 10) -> pd.DataFrame:
    """Prevision du cycle suivant: position relative, rang median, intervalle
    a 80 %, probabilite d'etre dans le top_k."""
    origin = d.shape[1] - 1
    pred, sigma, beta = fit_predict(d, origin, model, extra=extra)
    ranks = simulate_ranks(pred, sigma, n_sims)
    q10, q50, q90 = np.percentile(ranks, [10, 50, 90], axis=0)
    out = pd.DataFrame(dict(country=countries, pred_relative=pred.round(1),
                            rank_p10=q10, rank_median=q50, rank_p90=q90,
                            p_top_k=(ranks <= top_k).mean(axis=0).round(3)))
    out.attrs.update(model=model, sigma=sigma, beta=None if beta is None else beta.tolist(), top_k=top_k)
    return out.sort_values("rank_median").reset_index(drop=True)


def _py(o):
    """Convertit les types numpy pour json.dumps."""
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"type non serialisable: {type(o).__name__}")


def save_frozen_forecast(table: pd.DataFrame, path: str | Path, target: str, train_cycles: list[int]) -> None:
    """Ecrit la prevision + ses metadonnees. A COMMITER dans git AVANT la
    publication du resultat cible: l'horodatage du commit sert de
    pre-enregistrement verifiable. Les metadonnees sont serialisees AVANT toute
    ecriture: une erreur ne laisse jamais une prevision sans ses metadonnees."""
    path = Path(path)
    meta = dict(target=target, train_cycles=[int(c) for c in train_cycles],
                written_on=str(datetime.date.today()), model=table.attrs.get("model"),
                sigma=table.attrs.get("sigma"), beta=table.attrs.get("beta"),
                n_countries=len(table))
    meta_text = json.dumps(meta, indent=2, default=_py)      # echoue ici, avant d'ecrire
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(path, index=False)
    path.with_suffix(".meta.json").write_text(meta_text)


def incremental_feature_test(d: np.ndarray, F: dict, k: int, base_model: str = "ar1_mom") -> dict:
    """Test a deux etages, adapte au cas ou la variable n'existe que sur
    quelques cycles (ex: curriculum TIMSS 2015/2019/2023).
    Etage 1: prevision de base entrainee sur tout l'historique de scores.
    Etage 2: regression (1 seul parametre) de l'ERREUR de cette prevision sur
    la variable a l'origine k, puis application a la transition suivante.
    F: {indice_de_cycle: vecteur (n,)} defini en k et k+1. Evalue sur d[:, k+2]."""
    n, T = d.shape
    if k + 2 > T - 1:
        raise ValueError("pas assez de cycles apres l'origine k")
    pred_k, _, _ = fit_predict(d, k, base_model)
    e = d[:, k + 1] - pred_k
    x = F[k] - F[k].mean()
    s = float(x @ e / (x @ x))
    resid = e - s * x
    se = float(np.sqrt(resid @ resid / (n - 2) / (x @ x)))
    base_next, _, _ = fit_predict(d, k + 1, base_model)
    x_next = F[k + 1] - F[k + 1].mean()
    mse_base = float(np.mean((base_next - d[:, k + 2]) ** 2))
    mse_x = float(np.mean((base_next + s * x_next - d[:, k + 2]) ** 2))
    return dict(slope=s, t=s / se, mse_base=mse_base, mse_x=mse_x, wins=mse_x < mse_base)


# ---------------------------------------------------------------- test synthetique
def synthetic_scores(n=30, T=9, seed=0, phi=0.85, mom=0.25, noise=6.0, meas=3.0,
                     global_sd=10.0, feat_effect=0.0):
    rng = np.random.default_rng(seed)
    L = np.zeros((n, T))
    L[:, 0] = rng.normal(0, 25, n)
    L[:, 1] = phi * L[:, 0] + rng.normal(0, noise, n)
    F = rng.standard_normal((n, T))
    for t in range(1, T - 1):
        L[:, t + 1] = phi * L[:, t] + mom * (L[:, t] - L[:, t - 1]) + feat_effect * F[:, t] + rng.normal(0, noise, n)
    G = rng.normal(0, global_sd, T)
    return 500 + G[None, :] + L + rng.normal(0, meas, (n, T)), F


if __name__ == "__main__":
    print(__doc__)
    for feat in (0.0, 4.0):
        frames = []
        for seed in range(20):
            S, F = synthetic_scores(seed=seed, feat_effect=feat)
            d = relative_positions(pd.DataFrame(S))
            extra = {t: F[:, [t]] for t in range(S.shape[1])}
            frames.append(backtest(d, extra=extra).assign(seed=seed))
        print(f"\n=== Donnees synthetiques, 20 graines, effet de la variable explicative = {feat} ===")
        print(summarize(pd.concat(frames)).to_string())
    print("\n=== Puissance du test incremental (variable disponible sur 3 cycles seulement) ===")
    print("n=30 pays, T=9, variable observee aux cycles 6,7,8; 400 simulations par ligne")
    print(f"{'effet (pts/ET)':>15} {'|t|>2':>8} {'M3 bat M2':>11}")
    for eff in (0.0, 2.0, 4.0, 8.0):
        res = []
        for seed in range(400):
            S, F = synthetic_scores(seed=1000 + seed, feat_effect=eff)
            d = relative_positions(pd.DataFrame(S))
            res.append(incremental_feature_test(d, {6: F[:, 6], 7: F[:, 7]}, k=6))
        r = pd.DataFrame(res)
        print(f"{eff:>15.1f} {(r['t'].abs() > 2).mean():>8.2f} {r['wins'].mean():>11.2f}")
    print("\nLecture: skill_vs_naive > 0 = bat la persistance; cov80 proche de 0.8 = "
          "intervalles de rang bien calibres. Rien de tout cela ne dit quoi que ce soit "
          "des vraies donnees PISA.")