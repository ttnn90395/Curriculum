"""Meta-analyse de l'effet commun theta (SD par heure hebdomadaire), Amendement 6.2.
Etudes retenues : E01 (Lavy), E06 (Cattaneo, heures officielles), E07-E09 (Huebener, comptees comme UNE etude :
estimation = moyenne des trois, SE = moyenne des trois SE, hypothese conservatrice de correlation parfaite),
E10 (Rivkin-Schiman) seulement si extraite (value non NA). E05 exclue (double comptage de Cattaneo).
Effets aleatoires, DerSimonian-Laird. Sortie : data/processed/meta_theta.txt et .csv"""
import csv, math, os, sys
root = os.environ.get("ROOT", ".")
rows = {r["id"]: r for r in csv.DictReader(open(os.path.join(root, "data/evidence_instruction_time.csv")))}
def val(i):
    r = rows[i]
    if r["effect_sd_per_weekly_hour"] in ("NA", "") or r["se"] in ("NA", ""):
        return None
    return float(r["effect_sd_per_weekly_hour"]), float(r["se"])
studies = []
for sid, ids in [("Lavy", ["E01"]), ("Cattaneo", ["E06"]), ("Huebener", ["E07", "E08", "E09"]), ("Rivkin", ["E10"])]:
    v = [val(i) for i in ids]
    if any(x is None for x in v):
        print(f"{sid}: exclu (valeur manquante)")
        continue
    studies.append((sid, sum(x[0] for x in v) / len(v), sum(x[1] for x in v) / len(v)))
k = len(studies)
w = [1 / s[2] ** 2 for s in studies]
fe = sum(wi * s[1] for wi, s in zip(w, studies)) / sum(w)
Q = sum(wi * (s[1] - fe) ** 2 for wi, s in zip(w, studies))
C = sum(w) - sum(wi ** 2 for wi in w) / sum(w)
tau2 = max(0.0, (Q - (k - 1)) / C)
wr = [1 / (s[2] ** 2 + tau2) for s in studies]
re = sum(wi * s[1] for wi, s in zip(wr, studies)) / sum(wr)
se_re = math.sqrt(1 / sum(wr))
out = [f"k = {k} etudes", f"effet fixe = {fe:.4f}", f"Q = {Q:.3f} (ddl {k-1})", f"tau2 = {tau2:.6f}",
       f"theta (effets aleatoires) = {re:.4f}, SE = {se_re:.4f}, IC95 = [{re-1.96*se_re:.4f}, {re+1.96*se_re:.4f}]",
       "Etudes : " + "; ".join(f"{s[0]} {s[1]:.4f} ({s[2]:.4f})" for s in studies)]
os.makedirs(os.path.join(root, "data/processed"), exist_ok=True)
open(os.path.join(root, "data/processed/meta_theta.txt"), "w").write("\n".join(out) + "\n")
with open(os.path.join(root, "data/processed/meta_theta.csv"), "w", newline="") as f:
    wr_ = csv.writer(f); wr_.writerow(["etude", "effet", "se"]); wr_.writerows(studies)
    wr_.writerow(["theta_RE", re, se_re])
print("\n".join(out))
