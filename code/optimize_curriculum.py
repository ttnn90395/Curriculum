#!/usr/bin/env python3
"""optimize_curriculum.py -- Module A de docs/SPEC_OPTIMISATION_HORAIRES.md  [EXPLORATOIRE, SCENARIOS]

Sac a dos a contraintes de precedence, resolu exactement (scipy.optimize.milp):
    max sum_n w_n x_n   s.t.  sum_n tau_n x_n <= f * sum_n tau_n ,  x_n <= x_p  (arete p -> n),  x_n in {0,1}

ATTENTION: les tau_n NE SONT PAS ESTIMES. Les tau ci-dessous sont des SCENARIOS construits a partir des
difficultes IRT (hypothese H_prop, section 3ter, non validee tant que P1/P2 n'ont pas ete executes).
Notions sans difficulte fiable: tau = mediane des notions fiables (marque 'imputed'). H est exprime en
FRACTION f du temps total, pas en heures. Aucun resultat n'est une recommandation."""
import re, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import milp, LinearConstraint, Bounds

sys.path.insert(0, str(Path(__file__).parent))
from kst_extension import EXT

DIFF = "data/processed/notion_difficulty_timss2023_g4.csv"
FRAME = "data/framework_timss2023_g4_math.csv"
OUT = Path("data/processed")
FRACS = [0.25, 0.50, 0.75]

ids = sorted(EXT)
idx = {n: i for i, n in enumerate(ids)}
edges = [(p, n) for n, nt in EXT.items() for p in nt.prerequisites]

# ---- difficultes -> tau (3 familles) ----
dd = pd.read_csv(DIFF)
rel = dd[dd.reliable.astype(bool)].drop_duplicates("notion").set_index("notion").mean_b
fam = {
    "exp": np.exp(rel - rel.mean()),
    "lin": rel - rel.min() + 1.0,
    "rang": rel.rank(),
}
tau = {}
for name, s in fam.items():
    med = float(np.median(s.to_numpy()))
    tau[name] = np.array([float(s[n]) if n in s.index else med for n in ids])
imputed = [n for n in ids if n not in rel.index]
print(f"{len(ids)} notions, {len(edges)} aretes; tau fonde sur difficulte pour {len(rel)}; imputees: {len(imputed)}")

# ---- poids ----
fr = pd.read_csv(FRAME).fillna("")
w_t = np.zeros(len(ids))
for area, g in fr.groupby("topic_area"):
    pct = float(re.search(r"\((\d+)%\)", area).group(1))
    per_obj = pct / len(g)
    for r in g.itertuples():
        ns = [x for x in r.notions.split(";") if x in idx]
        for x in ns:
            w_t[idx[x]] += per_obj / len(ns)
weights = {"egaux": np.ones(len(ids)), "timss": w_t}
print(f"poids TIMSS: somme {w_t.sum():.1f}; notions a poids nul: {[ids[i] for i in np.where(w_t == 0)[0]]}")

# ---- contraintes de precedence ----
A_prec = np.zeros((len(edges), len(ids)))
for k, (p, n) in enumerate(edges):
    A_prec[k, idx[n]] = 1.0
    A_prec[k, idx[p]] = -1.0


def solve(w, t, f):
    cons = [LinearConstraint(A_prec, -np.inf, 0.0),
            LinearConstraint(t.reshape(1, -1), -np.inf, f * t.sum())]
    res = milp(c=-w, constraints=cons, integrality=np.ones(len(ids)), bounds=Bounds(0, 1))
    if not res.success:
        raise RuntimeError(res.message)
    x = np.round(res.x).astype(int)
    for p, n in edges:                       # validite KST: etat ferme par les prerequis
        assert not (x[idx[n]] and not x[idx[p]]), (p, n)
    return x, float(w @ x), float(t @ x)


rows = []
for fam_name, t in tau.items():
    for wn, w in weights.items():
        for f in FRACS:
            x, val, used = solve(w, t, f)
            rows.append(dict(tau_famille=fam_name, poids=wn, fraction_temps=f, valeur=round(val, 2),
                             temps_utilise=round(used / t.sum(), 3), n_notions=int(x.sum()),
                             notions=";".join(ids[i] for i in np.where(x)[0])))
res = pd.DataFrame(rows)
res.to_csv(OUT / "optimum_scenarios.csv", index=False)

print("\n== Optimum par scenario (fraction du temps total; tau = SCENARIO) ==")
print(res[["tau_famille", "poids", "fraction_temps", "n_notions", "valeur", "temps_utilise"]].to_string(index=False))

print("\n== Noyau robuste (present dans TOUS les scenarios) et union, par fraction de temps ==")
for f in FRACS:
    sets = [set(r.notions.split(";")) for r in res[res.fraction_temps == f].itertuples()]
    core = set.intersection(*sets)
    union = set.union(*sets)
    print(f"f={f:.2f}: noyau {len(core)} {sorted(core)}\n        union {len(union)}; instables {sorted(union - core)}")
print("\nStatut: exploratoire; tau non estime (scenarios). Ecritures: data/processed/optimum_scenarios.csv")
