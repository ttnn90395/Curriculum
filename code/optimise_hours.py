"""Scenarios d'heures hebdomadaires -> points PISA et cout, Amendement 8 (pre-enregistre).
Entrees : data/processed/meta_theta.csv (theta_RE, SE), data/processed/meta_theta.txt (tau2),
constantes de cout du dossier (cost_transfers_*, verifiees dans la note : college 295/443 M EUR par heure hebdomadaire
supplementaire pour toutes les classes, hors CAS / avec CAS ; elementaire 322.4/508.4 ; lycee GT non utilise car les
15 ans sont au college ou en seconde, la seconde seule n'est pas isolee dans les couts).
Monte-Carlo : theta ~ N(theta_RE, SE^2 + tau2) (distribution predictive), sigma PISA = 100 (sensibilite 90), graine fixe.
Sorties : data/processed/optimise_hours.csv et .txt. Exploratoire."""
import csv, math, os, re
import numpy as np
root = os.environ.get("ROOT", ".")
rows = list(csv.DictReader(open(os.path.join(root, "data/processed/meta_theta.csv"))))
th = [r for r in rows if r["etude"] == "theta_RE"][0]
theta, se = float(th["effet"]), float(th["se"])
tau2 = float(re.search(r"tau2 = ([0-9.]+)", open(os.path.join(root, "data/processed/meta_theta.txt")).read()).group(1))
sd_pred = math.sqrt(se ** 2 + tau2)
COST_COL = {"hors_CAS": 295.0, "avec_CAS": 443.0}   # M EUR / (heure hebdo par classe, toutes classes du college)
N_GRADES = 4
rng = np.random.default_rng(20261023)
N = 20000
draw = rng.normal(theta, sd_pred, N)
out = []
def q(a): return np.percentile(a, [5, 50, 95])
scen = []  # (nom, heures par domaine {math,reading,science}, cout_fraction_college, hypothese_temps, spillover_f, heures_retirees_non_testees)
for T, frac in [("T2_cycle_complet", 1.0), ("T1_niveau_teste_seul", 1.0 / N_GRADES)]:
    scen += [(f"+1h maths college [{T}]", dict(math=1, reading=0, science=0), frac, 0.0, 0),
             (f"+1h francais college [{T}]", dict(math=0, reading=1, science=0), frac, 0.0, 0),
             (f"+1h sciences college [{T}]", dict(math=0, reading=0, science=1), frac, 0.0, 0),
             (f"+1h chacune des 3 matieres testees college [{T}]", dict(math=1, reading=1, science=1), 3 * frac, 0.0, 0)]
for f in (0.0, 0.25, 0.5):
    scen.append((f"realloc 1h LV2 -> maths college, cout nul, spillover f={f} [T2_cycle_complet]", dict(math=1, reading=0, science=0), 0.0, f, 1))
res = []
for sigma in (100.0, 90.0):
    for name, h, frac, f, realloc in scen:
        dom = {d: sigma * draw * h[d] for d in h}
        if realloc:
            loss = sigma * draw * f   # perte attribuee aux trois domaines (spillover des heures retirees)
            dom = {d: dom[d] - loss for d in dom}
        mean3 = (dom["math"] + dom["reading"] + dom["science"]) / 3
        c0, c1 = COST_COL["hors_CAS"] * frac, COST_COL["avec_CAS"] * frac
        line = dict(sigma=sigma, scenario=name, cout_hors_CAS=c0, cout_avec_CAS=c1)
        for d in ("math", "reading", "science"):
            a = q(dom[d]); line[f"d_{d}_p5"], line[f"d_{d}_med"], line[f"d_{d}_p95"] = a
        a = q(mean3); line["d_mean3_p5"], line["d_mean3_med"], line["d_mean3_p95"] = a
        line["M_eur_par_point_mean3_hors_CAS"] = (c0 / np.median(mean3)) if c0 > 0 and np.median(mean3) > 0 else float("nan")
        line["M_eur_par_point_mean3_avec_CAS"] = (c1 / np.median(mean3)) if c1 > 0 and np.median(mean3) > 0 else float("nan")
        res.append(line)
keys = list(res[0].keys())
os.makedirs(os.path.join(root, "data/processed"), exist_ok=True)
with open(os.path.join(root, "data/processed/optimise_hours.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(res)
txt = [f"theta = {theta:.4f}, SE = {se:.4f}, tau2 = {tau2:.6f}, ecart-type predictif = {sd_pred:.4f}; N = {N}; graine 20261023"]
for r in res:
    txt.append(f"sigma {r['sigma']:.0f} | {r['scenario']}: cout {r['cout_hors_CAS']:.0f}/{r['cout_avec_CAS']:.0f} M EUR (hors/avec CAS); "
               f"gain 3 domaines (p5/med/p95) {r['d_mean3_p5']:.2f}/{r['d_mean3_med']:.2f}/{r['d_mean3_p95']:.2f}; "
               f"maths {r['d_math_med']:.2f}, lecture {r['d_reading_med']:.2f}, sciences {r['d_science_med']:.2f}; "
               f"M EUR/point (moy 3 dom.) {r['M_eur_par_point_mean3_hors_CAS']:.0f}/{r['M_eur_par_point_mean3_avec_CAS']:.0f}")
open(os.path.join(root, "data/processed/optimise_hours.txt"), "w").write("\n".join(txt) + "\n")
print("\n".join(txt))
