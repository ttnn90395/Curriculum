"""Cout par point de PISA avec contrainte d'offre (Amendement 15 et sa precision). Reutilise cost_model.py et trajectory_cost.py.
Usage : ROOT=. python3 -I code/cost_per_point.py
Entrees : data/processed/meta_theta.csv, meta_theta.txt ; curriculum, classes, parametres de cout ; N0 = 8008 (central), 8857.
Sorties : data/processed/cost_per_point.csv et cost_per_point.txt. Exploratoire ; aucun parametre ajuste."""
import csv, importlib.util, math, os, re, sys
import numpy as np
root = os.environ.get("ROOT", ".")
def load(name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(root, "code/%s.py" % name))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
cm, tc = load("cost_model"), load("trajectory_cost")
P = cm.params(); Q = cm.national_params(None, P)
classes = cm.load_classes(tc.CLS)
base = cm.load_curr(tc.CUR, [])
GR = sorted({g for (lv, g) in classes if lv == "college"})
def bump(cur, d):
    for g in GR:
        for sub, dh in d(g, cur):
            k = ("college", g, sub)
            if sub == "LV2" and k not in cur: continue
            if k not in cur: raise SystemExit("matiere absente : %s" % (k,))
            cur[k] += dh
            if cur[k] < 0: raise SystemExit("heures negatives %s" % (k,))
def sci(g, cur):
    s = [k[2] for k in cur if k[0] == "college" and k[1] == g]
    if "SVT" in s and "physique-chimie" in s: return [("SVT", 0.5), ("physique-chimie", 0.5)]
    if "SVT+physique-chimie" in s: return [("SVT+physique-chimie", 1.0)]
    raise SystemExit("sciences : aucune regle pour le niveau %s" % g)
def mk(parts):
    cur = dict(base)
    for p in parts:
        if p == "math": bump(cur, lambda g, c: [("mathematiques", 1.0)])
        elif p == "fr": bump(cur, lambda g, c: [("francais", 1.0)])
        elif p == "sci": bump(cur, sci)
        elif p == "lv2": bump(cur, lambda g, c: [("LV2", -1.0)])
    return cur
def net_by_grade(cur):  # hausse nette par niveau (controle)
    return {g: sum(cur[k] - base.get(k, 0.0) for k in cur if k[0] == "college" and k[1] == g) for g in GR}
def setup(cur, scale):
    eA, _ = cm.etp_by_subject(base, classes, Q["service"]); eB, _ = cm.etp_by_subject(cur, classes, Q["service"])
    sub = set(eA) | set(eB)
    need = sum(max(eB.get(s, 0) - eA.get(s, 0), 0) for s in sub); sur = sum(max(eA.get(s, 0) - eB.get(s, 0), 0) for s in sub)
    ten = sum(eB.get(s, 0) for s in sub if eB.get(s, 0) > eA.get(s, 0))
    return dict(c=Q["cout"] / 1e6, cas=Q["cas_ratio"], need=need * scale, sur=sur * scale, EA=sum(eA.values()), tension=ten * scale)
# gains (meme tirage que optimise_hours.py)
rows = list(csv.DictReader(open(os.path.join(root, "data/processed/meta_theta.csv"))))
th = [r for r in rows if r["etude"] == "theta_RE"][0]; theta, se = float(th["effet"]), float(th["se"])
tau2 = float(re.search(r"tau2 = ([0-9.]+)", open(os.path.join(root, "data/processed/meta_theta.txt")).read()).group(1))
draw = np.random.default_rng(20261023).normal(theta, math.sqrt(se ** 2 + tau2), 20000)
def gain(sigma, h, f=None):
    dom = {d: sigma * draw * h[d] for d in h}
    if f is not None:
        loss = sigma * draw * f; dom = {d: dom[d] - loss for d in dom}
    m3 = (dom["math"] + dom["reading"] + dom["science"]) / 3
    return np.percentile(m3, [5, 50, 95])
H = lambda m=0, r=0, s=0: dict(math=m, reading=r, science=s)
SC = []  # (nom, parts, scale, hours, f)
for T, sc in (("T2_cycle_complet", 1.0), ("T1_niveau_teste_seul", 0.25)):
    SC += [("+1h maths [%s]" % T, ["math"], sc, H(m=1), None), ("+1h francais [%s]" % T, ["fr"], sc, H(r=1), None),
           ("+1h sciences [%s]" % T, ["sci"], sc, H(s=1), None), ("+1h des 3 matieres [%s]" % T, ["math", "fr", "sci"], sc, H(1, 1, 1), None)]
for f in (0.0, 0.25, 0.5):
    SC.append(("realloc LV2->maths f=%s [T2_cycle_complet]" % f, ["math", "lv2"], 1.0, H(m=1), f))
variants = [("sans_prime", None, None, None)]
for n0 in (8008, 8857):
    for corps in (False, True):
        for e in (0.3, 1.0, 2.0): variants.append(("prime_%s" % ("tout_corps" if corps else "entrants"), n0, e, corps))
L, RHO, D, T01, T02, R = 4, 0.5, 1, 0.10, 0.20, 0.02
out = []
S0 = setup(mk(["math"]), 1.0)
Cs, _ = tc.trajectory(S0, 1, 0.0, 0, 1e12, 0.0, 0.0)
okc = abs(Cs[-1] - 295.4) <= 0.1 and abs(Cs[-1] * S0["cas"] - 443.1) <= 0.1
print("controle : +1h maths regime %.1f / %.1f -> %s" % (Cs[-1], Cs[-1] * S0["cas"], "OK" if okc else "ECHEC"))
if not okc: sys.exit("controle echoue : code invalide")
for name, parts, sc, hrs, f in SC:
    cur = mk(parts); nb = net_by_grade(cur)
    want = {"math": 1, "fr": 1, "sci": 1}
    exp = sum(want.get(p, 0) for p in parts) + (-0.0 if "lv2" not in parts else 0.0)
    if "lv2" not in parts and any(abs(v - exp) > 1e-9 for v in nb.values()): sys.exit("hausse nette inattendue %s : %s" % (name, nb))
    S = setup(cur, sc)
    for sigma in (100.0, 90.0):
        g5, g50, g95 = gain(sigma, hrs, f)
        for vn, n0, e, corps in variants:
            Cs, one = tc.trajectory(S, L, RHO, D, e if e else 1.0, T01, T02, n0, bool(corps))
            reg = Cs[-1]; vc = tc.npv(Cs, R)
            vg = sum(g50 * min(1.0, t / L) / (1 + R) ** t for t in range(tc.T + 1))
            ok = g50 > 0
            out.append(dict(sigma=sigma, scenario=name, variante=vn, N0=n0 or "", eps=e or "", regime_hors_CAS=round(reg, 1), regime_avec_CAS=round(reg * S["cas"], 1),
                gain_p5=round(g5, 3), gain_med=round(g50, 3), gain_p95=round(g95, 3),
                R1_hors_CAS=round(reg / g50, 1) if ok else "", R1_avec_CAS=round(reg * S["cas"] / g50, 1) if ok else "",
                R1_lo=round(reg / g95, 1) if g95 > 0 and reg > 0 else "", R1_hi=round(reg / g5, 1) if g5 > 0 and reg > 0 else "",
                R2_hors_CAS=round(vc / vg, 1) if ok and vg > 0 else ""))
keys = list(out[0].keys())
with open(os.path.join(root, "data/processed/cost_per_point.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(out)
txt = ["controle de regression : OK (+1h maths 295,4 / 443,1)"]
firsts, nvar = {}, 0
for sigma in (100.0, 90.0):
    for vn, n0, e, corps in variants:
        sel = [r for r in out if r["sigma"] == sigma and r["variante"] == vn and r["N0"] == (n0 or "") and r["eps"] == (e or "") and r["R1_hors_CAS"] != ""]
        sel.sort(key=lambda r: r["R1_hors_CAS"]); nvar += 1
        if sel: firsts[sel[0]["scenario"]] = firsts.get(sel[0]["scenario"], 0) + 1
        if sigma == 100.0 and (vn == "sans_prime" or (n0 == 8008 and e == 1.0)):
            txt.append("sigma 100 | %s%s : " % (vn, "" if not n0 else " N0=8008 eps=1") + " ; ".join("%s: R1 %.0f M EUR/point (%s-%s)" % (r["scenario"], r["R1_hors_CAS"], r["R1_lo"], r["R1_hi"]) for r in sel[:6]))
dom = [s for s, c in firsts.items() if c == nvar]
txt.append("scenario premier dans les %d variantes x sigma : %s" % (nvar, dom[0] if dom else "aucun (classement dependant des variantes) ; premiers par frequence : %s" % sorted(firsts.items(), key=lambda x: -x[1])))
open(os.path.join(root, "data/processed/cost_per_point.txt"), "w").write("\n".join(txt) + "\n"); print("\n".join(txt))
