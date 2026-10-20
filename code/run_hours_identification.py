#!/usr/bin/env python3
"""run_hours_identification.py -- applique docs/SPEC_OPTIMISATION_HORAIRES.md (3bis, 3ter, 3quater, 3quinquies). EXPLORATOIRE.

Modele: H_c = alpha + sum_k tau_k x_{c,k} + eps, alpha >= 0, tau >= 0 (moindres carres non negatifs).
Specification primaire: 3 domaines (Nombre N1-N7, Mesure et geometrie G3-G6, Donnees D1-D2), x_dom = somme des x_topic.
H_prop (3ter): H_c = alpha + kappa * sum_t g(b_t) x_{c,t}, 3 familles g (exp, lin, rang), topics a difficulte fiable seulement.
Mesure H: V_T = heures de maths enseignees par an en 4e annee (TIMSS). V_E (Eurydice) abandonnee.
Regles fixees avant donnees:
  D1  : R2 predictif (un pays laisse de cote) > 95e percentile du nul par permutation (1000, lignes de x entre pays).
  D2' : ajuster sur 2015, predire 2019, UNE fois; erreur absolue moyenne < celle de la moyenne des heures 2015.
  P3  : rejet si kappa estime = 0 (borne).
  tau n'est utilisable dans le module A que si D1 ET D2' passent.
Amendement 3sexies: fichier crosswalk robustesse (high+medium), G1 (low) exclu, G2 exclu (absent en 2015), soit 13 sujets;
  domaines Nombre 7, MesureGeo 4 (G3-G6), Donnees 2; sensibilite S4 = 6 sujets a confiance elevee (2 domaines).
Choix d'implementation NON precises dans l'amendement (signales): x_2015 = (valeur == 1) comme x_2019 (meme regle);
  appariement des pays par noms normalises + table d'alias explicite (aucun appariement flou); topics incomplets ecartes.
Exclusions: participants benchmarking, moyenne internationale, entites de 5e annee (note (5)), pays sans heures de maths."""
import re, sys, unicodedata
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import nnls

P = Path("data/processed")
SEED, NPERM, NBOOT = 20261020, 1000, 2000
TOPICS = [f"N{i}" for i in range(1, 8)] + ["G3", "G4", "G5", "G6", "D1", "D2"]   # 13 sujets (amendement 3sexies)
HI = ["N1", "N2", "N4", "N7", "G3", "G6"]   # sujets a confiance elevee communs aux 3 cycles (sensibilite S4)
DOM = {"Nombre": [t for t in TOPICS if t[0] == "N"], "MesureGeo": [t for t in TOPICS if t[0] == "G"],
       "Donnees": [t for t in TOPICS if t[0] == "D"]}
BENCH = {"International Average", "Ontario, Canada", "Quebec, Canada", "Madrid, Spain", "Abu Dhabi, UAE",
         "Dubai, UAE", "Moscow City, Russian Fed."}
ALIAS = {"korea rep of": "korea", "korea republic of": "korea", "republic of korea": "korea",
         "hong kong sar": "hong kong", "iran islamic rep of": "iran", "iran islamic republic of": "iran",
         "turkey": "turkiye", "russian federation": "russia", "czech republic": "czechia",
         "slovak republic": "slovakia", "macao sar": "macao", "chinese taipei": "taiwan",
         "north macedonia": "macedonia"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(\d\)", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return ALIAS.get(s, s)


# ---------- donnees ----------
def load_hours(cycle):
    h = pd.read_csv(P / f"timss{cycle}_math_hours_g4.csv")
    if "benchmarking" in h:
        h = h[~h.benchmarking.astype(bool)]
    h = h[~h.country_raw.isin(BENCH)]
    h = h[~h.country_raw.str.contains(r"\(5\)\s*$")]
    h = h[~h.country_raw.str.lower().str.contains("international average")]
    h = h.assign(key=h.country_raw.map(norm))
    if "flag_math" not in h:
        h["flag_math"] = ""
    return h.dropna(subset=["math_hours"]).drop_duplicates("key")


cv = pd.read_csv(P / "crosswalk_topic_values_robustesse.csv")   # high + medium; low (G1) exclu par le gel du crosswalk
assert set(TOPICS) <= set(cv.topic_id), f"sujets manquants: {sorted(set(TOPICS) - set(cv.topic_id))}"
cv = cv[cv.topic_id.isin(TOPICS)]
cv["key"] = cv.country.map(norm)


def assemble(cycle):
    h = load_hours(cycle)
    w = cv[cv.cycle == cycle].pivot_table(index="key", columns="topic_id", values="value", aggfunc="first")
    full = w.dropna()
    both = h.merge(full, left_on="key", right_index=True)
    print(f"cycle {cycle}: heures {len(h)}, couverture {len(w)} ({len(w) - len(full)} incomplets), apparies {len(both)}")
    print("   heures sans couverture:", sorted(set(h.key) - set(full.index)))
    print("   couverture sans heures:", sorted(set(full.index) - set(h.key)))
    return both.reset_index(drop=True)


d19, d15 = assemble(2019), assemble(2015)
if len(d19) < 25:
    sys.exit(f"REGLE 3quater: {len(d19)} pays < 25 -> regression NON executee (rapport descriptif seulement).")

# ---------- difficultes b_t (H_prop) ----------
fw = pd.read_csv("data/framework_timss2023_g4_math.csv").fillna("")
do = pd.read_csv(P / "difficulty_by_objective_g4.csv").set_index("obj")
o2t = {r.obj_id: r.crosswalk_topic for r in fw.itertuples() if r.crosswalk_topic}
o2t["D34"] = "D2"
bt, reliable = {}, {}
for t in TOPICS:
    objs = [o for o, tt in o2t.items() if tt == t and o in do.index]
    if objs:
        n = do.loc[objs, "n_items"]
        bt[t] = float((do.loc[objs, "mean_b"] * n).sum() / n.sum())
        reliable[t] = bool((n >= 5).all())
RT = [t for t in TOPICS if reliable.get(t)]
b = pd.Series({t: bt[t] for t in RT})
G = {"exp": np.exp(b - b.mean()), "lin": b - b.min() + 1.0, "rang": b.rank()}
print(f"\ntopics a difficulte fiable pour H_prop: {len(RT)} {RT}; exclus: {sorted(set(TOPICS) - set(RT))}")


# ---------- estimation ----------
def fit(A, y, w=None):
    A1 = np.column_stack([np.ones(len(A)), A])
    if w is not None:
        s = np.sqrt(w)
        return nnls(A1 * s[:, None], y * s)[0]
    return nnls(A1, y)[0]


def pred(coef, A):
    return coef[0] + A @ coef[1:]


def loco_r2(A, y, w=None):
    n, sse, ssm = len(y), 0.0, 0.0
    for i in range(n):
        m = np.arange(n) != i
        c = fit(A[m], y[m], None if w is None else w[m])
        sse += (y[i] - pred(c, A[i])) ** 2
        ssm += (y[i] - y[m].mean()) ** 2
    return 1 - sse / ssm


def perm_null(A, y, w, rng):
    return np.array([loco_r2(A[rng.permutation(len(A))], y, w) for _ in range(NPERM)])


def designs(d, binar=True):
    X = d[TOPICS].to_numpy(float)
    X = (X == 1.0).astype(float) if binar else X
    Xd = np.column_stack([X[:, [TOPICS.index(t) for t in DOM[k]]].sum(1) for k in DOM])
    out = {"domaines(3)": Xd}
    for g, s in G.items():
        out[f"H_prop_{g}"] = (X[:, [TOPICS.index(t) for t in RT]] * s.to_numpy()).sum(1, keepdims=True)
    return X, out


X19, D19 = designs(d19)
X15, D15 = designs(d15)
y19, y15 = d19.math_hours.to_numpy(float), d15.math_hours.to_numpy(float)
rng = np.random.default_rng(SEED)

rows = []
print("\n== D1 (2019, n=%d), D2' (2015 -> 2019), P3 ==" % len(d19))
for name in D19:
    A = D19[name]
    r2 = loco_r2(A, y19)
    null = perm_null(A, y19, None, rng)
    p95, pval = float(np.percentile(null, 95)), float((1 + (null >= r2).sum()) / (NPERM + 1))
    c15 = fit(D15[name], y15)
    e_mod = float(np.mean(np.abs(y19 - pred(c15, A))))
    e_base = float(np.mean(np.abs(y19 - y15.mean())))
    c19 = fit(A, y19)
    d1, d2 = r2 > p95, e_mod < e_base
    p3 = (name == "domaines(3)") or c19[1] > 1e-9
    rows.append(dict(modele=name, r2_loco=round(r2, 3), nul_p95=round(p95, 3), p_perm=round(pval, 4), D1=d1,
                     mae_2015_vers_2019=round(e_mod, 1), mae_moyenne_2015=round(e_base, 1), D2p=d2, P3_ok=p3,
                     tau_utilisable=bool(d1 and d2 and p3), coef_2019=np.round(c19, 2).tolist()))
res = pd.DataFrame(rows)
print(res.drop(columns="coef_2019").to_string(index=False))
res.to_csv(P / "hours_identification_results.csv", index=False)

# ---------- IC bootstrap des tau (domaines, 2019) ----------
bs = []
for _ in range(NBOOT):
    i = rng.integers(0, len(y19), len(y19))
    bs.append(fit(D19["domaines(3)"][i], y19[i]))
bs = np.array(bs)
c = fit(D19["domaines(3)"], y19)
print("\n== tau par domaine (heures de maths/an par sujet couvert), 2019, IC95% bootstrap sur pays ==")
for j, nm in enumerate(["alpha"] + list(DOM)):
    print(f"  {nm:10s} {c[j]:7.2f}  [{np.percentile(bs[:, j], 2.5):6.2f}, {np.percentile(bs[:, j], 97.5):6.2f}]")

# ---------- D4 descriptif ----------
k = d19.index[d19.key == "france"]
if len(k):
    m = np.arange(len(y19)) != k[0]
    cf = fit(D19["domaines(3)"][m], y19[m])
    print(f"\nD4 (France hors ajustement): prevu {pred(cf, D19['domaines(3)'][k[0]]):.0f} h, observe {y19[k[0]]:.0f} h")

# ---------- D3 + specification topics (exploratoire) ----------
A1 = np.column_stack([np.ones(len(X19)), X19])
cond = np.linalg.cond(A1 / np.maximum(np.linalg.norm(A1, axis=0), 1e-12))
print(f"\nD3: conditionnement de la matrice (13 sujets) = {cond:.1f} ({'> 30: specification a 13 sujets NON retenue' if cond > 30 else '<= 30: exploratoire'})")
if cond <= 30:
    r2t = loco_r2(X19, y19)
    nt = perm_null(X19, y19, None, rng)
    print(f"  topics: R2_loco {r2t:.3f}, nul p95 {np.percentile(nt, 95):.3f}")

# ---------- sensibilites (domaines, 2019) ----------
print("\n== Sensibilites (modele a 3 domaines, 2019) ==")
sens = []
m_s = (d19.flag_math != "s").to_numpy()
_, Ds = designs(d19)
sens.append(("S1 sans pays marques 's'", Ds["domaines(3)"][m_s], y19[m_s], None))
sens.append(("S2 pondere 1/ES^2", Ds["domaines(3)"], y19, 1.0 / np.maximum(d19.math_se.to_numpy(float), 0.5) ** 2))
_, Dh = designs(d19, binar=False)
sens.append(("S3 code 2 = 0.5", Dh["domaines(3)"], y19, None))
for nm, A, y, w in sens:
    r2 = loco_r2(A, y, w)
    nul = perm_null(A, y, w, rng)
    print(f"  {nm}: n={len(y)}, R2_loco {r2:.3f}, nul p95 {np.percentile(nul, 95):.3f}, p {(1 + (nul >= r2).sum()) / (NPERM + 1):.4f}")

# S4: sujets a confiance elevee seulement (N1,N2,N4,N7 | G3,G6), 2 domaines
Xb = (d19[HI].to_numpy(float) == 1.0).astype(float)
A4 = np.column_stack([Xb[:, [0, 1, 2, 3]].sum(1), Xb[:, [4, 5]].sum(1)])
r4 = loco_r2(A4, y19)
n4 = perm_null(A4, y19, None, rng)
print(f"  S4 sujets a confiance elevee (6 sujets, 2 domaines): n={len(y19)}, R2_loco {r4:.3f}, nul p95 {np.percentile(n4, 95):.3f}, p {(1 + (n4 >= r4).sum()) / (NPERM + 1):.4f}")

ok = res[res.tau_utilisable]
print("\nVERDICT (regle 3bis/3quinquies): " + (f"tau utilisable pour {list(ok.modele)}" if len(ok)
      else "tau NON utilisable (D1 et D2' non satisfaits simultanement) -> retour aux scenarios"))
print("Statut: exploratoire. Ecritures: data/processed/hours_identification_results.csv")
