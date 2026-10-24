"""Trajectoire de cout court et long terme d'un curriculum (Amendement 14). Reutilise code/cost_model.py (Amendement 12).
Usage : ROOT=. python3 -I code/trajectory_cost.py regression
        ROOT=. python3 -I code/trajectory_cost.py grid --delta college,mathematiques,+1 [--delta ...] [--n0 N]
--n0 : recrutement annuel actuel (ETP) ; sans lui la prime salariale d'equilibre n'est pas calculee (declaree non realisee).
Base de la prime : cout moyen charge par ETP (surestime le salaire d'un entrant ; limite declaree).
Sorties : data/processed/trajectory_regression.txt, trajectory_grid.csv, trajectory_summary.txt. Aucun parametre ajuste."""
import argparse, csv, importlib.util, itertools, os, sys
root = os.environ.get("ROOT", ".")
spec = importlib.util.spec_from_file_location("cost_model", os.path.join(root, "code/cost_model.py"))
cm = importlib.util.module_from_spec(spec); spec.loader.exec_module(cm)
T, DEPART, CARRIERE = 30, 0.03, 30
CUR = "data/instruction_hours_fr_secondary.csv"; CLS = "data/classes_fr.csv"
def setup(deltas):
    P = cm.params(); q = cm.national_params(None, P)
    classes = cm.load_classes(CLS)
    eA, _ = cm.etp_by_subject(cm.load_curr(CUR, []), classes, q["service"])
    eB, _ = cm.etp_by_subject(cm.load_curr(CUR, deltas), classes, q["service"])
    subj = set(eA) | set(eB)
    need = sum(max(eB.get(s, 0) - eA.get(s, 0), 0) for s in subj)
    sur = sum(max(eA.get(s, 0) - eB.get(s, 0), 0) for s in subj)
    tension = sum(eB.get(s, 0) for s in subj if eB.get(s, 0) > eA.get(s, 0))
    return dict(c=q["cout"] / 1e6, cas=q["cas_ratio"], need=need, sur=sur, EA=sum(eA.values()), tension=tension)
def trajectory(S, L, rho, d, eps, t01, t02, n0=None, corps=False):
    """Renvoie la liste C(t) (M EUR hors CAS), t = 0..T, et la part ponctuelle."""
    c = S["c"]; absorb = DEPART * S["EA"]
    p = lambda t: min(1.0, t / L)
    Rc = Qc = Ic = 0.0; Qin = [0.0] * (T + 1); Qadd = [0.0] * (T + 1)
    Acum = 0.0; Cs, one = [], 0.0
    prevR = prevQ = 0.0; dwmax = 0.0; cohorts = []
    for t in range(T + 1):
        N, Sg = p(t) * S["need"], p(t) * S["sur"]
        R = min(rho * Sg, N); Q = N - R
        dR, dQ = R - prevR, Q - prevQ; prevR, prevQ = R, Q
        Qadd[t] = dQ
        if t + d <= T: Qin[t + d] += dQ
        newidle = Sg - R - (Ic + Acum)          # surplus non reconverti cree a t
        newidle = max(newidle, 0.0)
        Ic += newidle                            # stock oisif avant absorption
        ab = min(Ic, absorb) if t > 0 else 0.0   # absorption a partir de l'annee suivante
        Ic -= ab; Acum += ab
        stock_in = sum(Qin[:t + 1])
        dP = stock_in - Acum
        cost = c * dP
        o = c * (t01 * dR + t02 * dQ)
        prem = 0.0
        if n0 and S["need"] > 0:
            dw = (dQ / n0) / eps
            cohorts.append((t, dw, n0 + dQ)); dwmax = max(dwmax, dw)
            if corps:
                prem = c * dwmax * S["tension"] * (1.0 if t > 0 else 0.0)
            else:
                prem = sum(c * w * n for (u, w, n) in cohorts if t - u < CARRIERE)
        Cs.append(cost + o + prem); one += o
    return Cs, one
def npv(Cs, r): return sum(x / (1 + r) ** t for t, x in enumerate(Cs))
def regression():
    out = []; ok = True
    cases = [(["college,mathematiques,+1"], 295.4, 443.1), (["college,mathematiques,+1", "college,LV2,-1"], 73.8, 110.8)]
    for dl, ref_h, ref_a in cases:
        S = setup(dl)
        Cs, _ = trajectory(S, 1, 0.0, 0, 1e12, 0.0, 0.0)
        reg_h, reg_a = Cs[-1], Cs[-1] * S["cas"]
        good = abs(reg_h - ref_h) <= 0.1 and abs(reg_a - ref_a) <= 0.1; ok &= good
        out.append("%s : regime hors CAS %.1f (ref %.1f) ; avec CAS %.1f (ref %.1f) -> %s" % (dl, reg_h, ref_h, reg_a, ref_a, "OK" if good else "ECHEC"))
    out.append("controle de regression : " + ("REUSSI" if ok else "ECHEC, code invalide"))
    open(os.path.join(root, "data/processed/trajectory_regression.txt"), "w").write("\n".join(out) + "\n"); print("\n".join(out))
    return ok
def grid(a):
    S = setup(a.delta); n0 = a.n0
    rows = []; maxshare = 0.0
    for L, rho, d, eps, t01, t02, r in itertools.product((2, 4, 8), (0.25, 0.5, 0.75), (0, 1, 2), (0.3, 1.0, 2.0), (0.05, 0.10, 0.20), (0.10, 0.20, 0.40), (0.0, 0.02, 0.04)):
        for corps in ((False, True) if n0 else (False,)):
            Cs, one = trajectory(S, L, rho, d, eps, t01, t02, n0, corps)
            Cs0, _ = trajectory(S, L, rho, d, eps, 0.0, 0.0, n0, corps)
            v, v0 = npv(Cs, r), npv(Cs0, r)
            share = (v - v0) / v if v else 0.0; maxshare = max(maxshare, share)
            rows.append([L, rho, d, eps, t01, t02, r, int(corps), "%.1f" % max(Cs), "%.1f" % Cs[-1], "%.1f" % v, "%.1f" % (v * S["cas"]), "%.3f" % share])
    with open(os.path.join(root, "data/processed/trajectory_grid.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["L", "rho", "d", "eps", "T01", "T02", "taux", "prime_tout_corps", "pic_hors_CAS", "regime_hors_CAS", "VAN30_hors_CAS", "VAN30_avec_CAS", "part_ponctuels_VAN"]); w.writerows(rows)
    cen = [x for x in rows if x[:7] == [4, 0.5, 1, 1.0, 0.10, 0.20, 0.02] and x[7] == 0][0]
    out = ["curriculum modifie par %s ; ETP besoins %.0f, surplus %.0f ; cout ETP %.5f M EUR" % (a.delta, S["need"], S["sur"], S["c"]),
           "prime salariale : " + ("calculee avec N0 = %.0f ETP/an (base : cout moyen charge ; surestime le salaire d'un entrant)" % n0 if n0 else "non realisee (N0 non fournie)"),
           "cellule centrale (L=4, rho=0,5, d=1, eps=1, T01=0,10, T02=0,20, taux 2 %%, prime entrants) : pic %s M EUR, regime %s, VAN30 hors CAS %s, avec CAS %s" % (cen[8], cen[9], cen[10], cen[11]),
           "part maximale des couts ponctuels dans la VAN sur la grille : %.1f %% -> %s" % (100 * maxshare, "conclusion robuste aux couts ponctuels non sources" if maxshare < 0.10 else "conclusion DEPENDANTE de couts non sources"),
           "grille : %d lignes dans data/processed/trajectory_grid.csv" % len(rows)]
    open(os.path.join(root, "data/processed/trajectory_summary.txt"), "w").write("\n".join(out) + "\n"); print("\n".join(out))
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["regression", "grid"]); ap.add_argument("--delta", action="append", default=[]); ap.add_argument("--n0", type=float, default=None)
    a = ap.parse_args()
    if a.cmd == "regression": sys.exit(0 if regression() else 1)
    if not regression(): sys.exit("regression echouee : aucune autre sortie")
    grid(a)
