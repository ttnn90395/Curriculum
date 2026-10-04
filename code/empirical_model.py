"""
Projet Education -- Modele empirique (Partie 3)
===================================================
Conforme a SCOPE.md: cible PISA en priorite (TIMSS = robustesse
secondaire, pas construit ici), modeles simples uniquement
(OLS/ridge/lasso/PLS), pas de HLM ni de priors bayesiens (deferes
par la decision de scope).

Discipline confirmatoire/exploratoire (Plan.txt, Partie 2, Section
"Discipline confirmatoire/exploratoire"): ce script ne doit
tourner QUE sur les cycles PISA <= 2018 tant que les features et
la methode ne sont pas gelees. Le garde-fou year_cutoff=2018 est
applique par defaut, pas optionnel sans justification explicite.

Statut: testé sur donnees synthetiques (voir generate_synthetic_data).
Pas encore connecte a de vraies donnees TIMSS/PISA.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression
from sklearn.cross_decomposition import PLSRegression
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm


FEATURES = [
    "coverage_implemented",      # p_{i,n} agrege par pays
    "gap_intended_implemented",  # g_{i,n} agrege -- A RETIRER si
                                  # diagnostic_1 confirme la redondance
                                  # avec instructional_hours (cf.
                                  # diagnostic_regressions.py)
    "instructional_hours_total",
    "tracking_age",
    "prerequisite_violation_score",
]
TARGET = "pisa_score"  # priorite scope -- PAS timss_score ici
GROUP_COL = "country"
YEAR_COL = "cycle_year"


def generate_synthetic_data(n_countries: int = 22, seed: int = 0) -> pd.DataFrame:
    """Panel synthetique pour TESTER le pipeline uniquement --
    ne remplace aucune donnee reelle. Les coefficients vrais sont
    connus ici (utile pour verifier que le pipeline retrouve un
    signal quand il existe)."""
    rng = np.random.default_rng(seed)
    cycles = [2011, 2015, 2019]
    rows = []
    for c in range(n_countries):
        country = f"C{c:02d}"
        base_quality = rng.normal(0, 1)
        for year in cycles:
            coverage = np.clip(rng.normal(0.6 + 0.1 * base_quality, 0.15), 0, 1)
            gap = np.clip(rng.normal(0.15, 0.08) - 0.05 * base_quality, 0, 1)
            hours = rng.normal(140, 20)
            tracking_age = rng.choice([10, 12, 14, 15, 16])
            violation = np.clip(rng.normal(0.2 - 0.1 * base_quality, 0.1), 0, 1)
            # Signal vrai: coverage et violation comptent, gap et
            # hours n'ont volontairement PEU d'effet propre (pour
            # tester si le diagnostic de collinearite/redondance
            # le detecterait sur de vraies donnees)
            pisa = (
                480
                + 40 * coverage
                - 30 * violation
                + 0.3 * (tracking_age - 13)
                + rng.normal(0, 8)
            )
            rows.append(dict(
                country=country, cycle_year=year,
                coverage_implemented=coverage,
                gap_intended_implemented=gap,
                instructional_hours_total=hours,
                tracking_age=tracking_age,
                prerequisite_violation_score=violation,
                pisa_score=pisa,
            ))
    return pd.DataFrame(rows)


def check_vif(df: pd.DataFrame, features: list[str] = FEATURES) -> pd.Series:
    """Diagnostic de multicollinearite (Partie 3, Section
    'Diagnostic de multicollinearite') -- A EXECUTER avant
    d'interpreter les coefficients de n'importe quel modele
    lineaire ci-dessous. VIF > 5-10 signale une colinearite
    problematique."""
    X = sm.add_constant(df[features])
    vif = pd.Series(
        [variance_inflation_factor(X.values, i) for i in range(X.shape[1])],
        index=X.columns,
    )
    return vif.drop("const")


def nested_cv_compare_methods(
    df: pd.DataFrame,
    features: list[str] = FEATURES,
    target: str = TARGET,
    year_cutoff: int = 2018,
    n_splits: int = 5,
) -> pd.DataFrame:
    """Compare OLS/ridge/lasso/elastic net/PLS/processus gaussien
    par validation croisee groupee par pays (GroupKFold -- evite la
    fuite d'information intra-pays entre cycles, cf. Plan.txt
    'Approche empirique').

    GARDE-FOU: filtre sur year_cutoff par defaut (exploratoire
    seulement). Ne pas changer sans avoir explicitement gele la
    specification au prealable (cf. discipline confirmatoire/
    exploratoire).
    """
    if (df[YEAR_COL] > year_cutoff).any():
        n_dropped = (df[YEAR_COL] > year_cutoff).sum()
        print(
            f"ATTENTION: {n_dropped} observations post-{year_cutoff} "
            f"retirees -- zone confirmatoire non touchee par design "
            f"(cf. discipline confirmatoire/exploratoire, Plan.txt)"
        )
        df = df[df[YEAR_COL] <= year_cutoff].copy()

    X = df[features].values
    y = df[target].values
    groups = df[GROUP_COL].values

    n_groups = df[GROUP_COL].nunique()
    n_splits = min(n_splits, n_groups)
    gkf = GroupKFold(n_splits=n_splits)

    methods = {
        "OLS": LinearRegression(),
        "Ridge": Ridge(alpha=1.0),
        "Lasso": Lasso(alpha=0.1),
        "ElasticNet": ElasticNet(alpha=0.1, l1_ratio=0.5),
        "PLS": PLSRegression(n_components=min(3, len(features))),
        "GaussianProcess": GaussianProcessRegressor(
            kernel=RBF() + WhiteKernel(), normalize_y=True, random_state=0
        ),
    }

    results = []
    for name, model in methods.items():
        preds, truths = [], []
        for train_idx, test_idx in gkf.split(X, y, groups):
            scaler = StandardScaler().fit(X[train_idx])
            X_train = scaler.transform(X[train_idx])
            X_test = scaler.transform(X[test_idx])

            model.fit(X_train, y[train_idx])
            pred = model.predict(X_test)
            pred = np.ravel(pred)  # PLS renvoie (n,1)

            preds.extend(pred)
            truths.extend(y[test_idx])

        rmse = np.sqrt(mean_squared_error(truths, preds))
        r2 = r2_score(truths, preds)
        results.append(dict(method=name, cv_rmse=rmse, cv_r2=r2))

    return pd.DataFrame(results).sort_values("cv_rmse")


if __name__ == "__main__":
    print(__doc__)

    df = generate_synthetic_data()
    print(f"Panel synthetique: {len(df)} observations, "
          f"{df[GROUP_COL].nunique()} pays, cycles {sorted(df[YEAR_COL].unique())}")

    print("\n=== Diagnostic VIF (donnees synthetiques) ===")
    vif = check_vif(df)
    print(vif.round(2).to_string())
    high_vif = vif[vif > 5]
    if not high_vif.empty:
        print(f"\nATTENTION -- VIF > 5 pour: {list(high_vif.index)}")

    print("\n=== Comparaison des methodes (CV groupee par pays, <=2018 uniquement) ===")
    results = nested_cv_compare_methods(df)
    print(results.to_string(index=False))

    print(
        "\nRappel: ces resultats sont sur donnees SYNTHETIQUES -- "
        "ne rien conclure sur le vrai signal avant connexion aux "
        "donnees reelles (cf. data/README.md)."
    )
