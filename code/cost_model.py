"""Modele de cout d'un curriculum : entretien (regime permanent) et transition d'un curriculum a un autre. Amendement 12.
Usage :
  python3 code/cost_model.py maintain --curriculum data/instruction_hours_fr_secondary.csv --mode national [--delta college,mathematiques,+1]
  python3 code/cost_model.py transition --curriculum data/instruction_hours_fr_secondary.csv --delta college,mathematiques,+1 --delta college,LV2,-1 --mode national
Curriculum : csv level,grade,subject,weekly_hours (heures hebdomadaires par classe). Classes : data/classes_fr.csv (level,grade,classes).
Mode national (France) : cout moyen charge hors CAS par ETP (parametres du depot) et service hebdomadaire 18 h (ou moyenne ponderee par corps).
Mode oecd : cout par eleve = h x semaines / H x salaire brut PPA x (facteur employeur) / taille de classe, parametres de data/processed/cross_country_net_cost.csv.
Aucune valeur manquante n'est imputee : un niveau sans classes dans le fichier est ignore et signale."""
import argparse, csv, os, sys
root = os.environ.get("ROOT", ".")
def rd(p): return list(csv.DictReader(open(os.path.join(root, p))))
def params():
    P = {}
    for row in csv.reader(open(os.path.join(root, "data/parameters_teachers_cost.csv"))):
        if len(row) >= 2 and row[0] != "id" and row[1].strip() != "":
            try: P[row[0]] = float(row[1])
            except ValueError: pass
    return P
def load_curr(path, deltas):
    cur = {}
    for r in rd(path):
        cur[(r["level"], r["grade"], r["subject"])] = cur.get((r["level"], r["grade"], r["subject"]), 0.0) + float(r["weekly_hours"])
    for d in deltas:
        lv, sb, dh = d.split(",")
        dh = float(dh)
        hit = [k for k in cur if k[0] == lv and k[2] == sb]
        if not hit: raise SystemExit(f"delta sans cible : {d}")
        for k in hit:
            cur[k] = cur[k] + dh
            if cur[k] < 0: raise SystemExit(f"heures negatives pour {k}")
    return cur
def load_classes(path):
    return {(r["level"], r["grade"]): float(r["classes"]) for r in rd(path)}
def etp_by_subject(cur, classes, service):
    etp, ignored = {}, set()
    for (lv, g, s), h in cur.items():
        if (lv, g) not in classes:
            ignored.add((lv, g)); continue
        etp[s] = etp.get(s, 0.0) + h * classes[(lv, g)] / service
    return etp, ignored
def national_params(args, P):
    return dict(cout=P["cout_ens2d_hors_CAS"], service=18.0, cas_ratio=P.get("ratio_avecCAS_sur_horsCAS_P141", 1.5001))
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["maintain", "transition"])
    ap.add_argument("--curriculum", default="data/instruction_hours_fr_secondary.csv")
    ap.add_argument("--classes", default="data/classes_fr.csv")
    ap.add_argument("--mode", choices=["national", "oecd"], default="national")
    ap.add_argument("--country", default="FRA")
    ap.add_argument("--delta", action="append", default=[], help="level,subject,+h applique a tous les niveaux de classe du level")
    ap.add_argument("--rho", type=float, default=0.5, help="part du surplus reconvertible vers les besoins (parametre de scenario)")
    a = ap.parse_args()
    P = params()
    base = load_curr(a.curriculum, [])
    alt = load_curr(a.curriculum, a.delta)
    classes = load_classes(a.classes)
    out = []
    if a.mode == "national":
        q = national_params(a, P)
        eA, ign = etp_by_subject(base, classes, q["service"]); eB, _ = etp_by_subject(alt, classes, q["service"])
        cA, cB = sum(eA.values()) * q["cout"] / 1e6, sum(eB.values()) * q["cout"] / 1e6
        out.append(f"niveaux sans classes (ignores) : {sorted(ign)}")
        out.append(f"ETP : {sum(eA.values()):.0f} -> {sum(eB.values()):.0f} ; cout hors CAS : {cA:.1f} -> {cB:.1f} M EUR (difference {cB-cA:+.1f}) ; avec CAS (ratio {q['cas_ratio']}): {cA*q['cas_ratio']:.1f} -> {cB*q['cas_ratio']:.1f} (difference {(cB-cA)*q['cas_ratio']:+.1f})")
        if a.cmd == "transition":
            surplus = sum(max(eA.get(s, 0) - eB.get(s, 0), 0) for s in set(eA) | set(eB))
            need = sum(max(eB.get(s, 0) - eA.get(s, 0), 0) for s in set(eA) | set(eB))
            retrained = min(a.rho * surplus, need); recruited = need - retrained; idle = surplus - retrained
            out.append(f"flux d'ETP (comptes, sans parametre de cout) : surplus {surplus:.0f}, besoins {need:.0f}, reconvertis {retrained:.0f} (rho={a.rho}), recrutes {recruited:.0f}, excedentaires {idle:.0f}")
            out.append("couts ponctuels : voir data/transition_parameters.csv (placeholders non sources) ; exprimes en fraction du cout annuel d'un ETP :")
            for r in rd("data/transition_parameters.csv"):
                coef = float(r["value"]); n = {"retrain": retrained, "recruit": recruited, "idle": idle}[r["applies_to"]]
                out.append(f"  {r['id']} [{r['status']}] {r['label']}: {n:.0f} ETP x {coef} x {q['cout']:.0f} EUR = {n*coef*q['cout']/1e6:.1f} M EUR")
    else:
        row = [r for r in rd("data/processed/cross_country_net_cost.csv") if r["pays"] == a.country][0]
        S, F, H, W, N = (float(row[k]) for k in ("salaire_ppp", "facteur_employeur", "heures_an", "semaines", "taille_classe"))
        def per_pupil(cur, employer):
            tot = 0.0
            for (lv, g, s), h in cur.items():
                tot += h * W / H * S * (F if employer else 1.0) / N
            return tot
        n_levels = len({(k[0], k[1]) for k in base})
        out.append(f"{a.country} : salaire PPA {S:.0f}, facteur employeur {F}, H {H:.0f} h, {W:.0f} semaines, classe {N:.1f} ; {n_levels} niveaux de classe")
        out.append(f"cout par eleve (somme sur les niveaux, PPA) : brut {per_pupil(base, False):.0f} -> {per_pupil(alt, False):.0f} ; employeur {per_pupil(base, True):.0f} -> {per_pupil(alt, True):.0f}")
    print("\n".join(out))
if __name__ == "__main__":
    main()
