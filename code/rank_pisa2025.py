"""Rang de la France, PISA 2025, a partir de data/evidence_pisa2025_country_tables.csv (reproduction secondaire
des tableaux OCDE). Rang = 1 + nombre de systemes strictement meilleurs ; ex aequo non departages.
Aucune inference sur la significativite : l'OCDE publie des intervalles de rang que ce script ne reconstruit pas.
Sorties : data/processed/rank_pisa2025.txt"""
import csv, os
root = os.environ.get("ROOT", ".")
rows = list(csv.DictReader(open(os.path.join(root, "data/evidence_pisa2025_country_tables.csv"))))
dom = ["mathematics", "reading", "science"]
def val(r, d): return float(r[d]) if r[d] != "" else None
out = []
def ranks(sub, label):
    for d in dom:
        v = {r["system"]: val(r, d) for r in sub if val(r, d) is not None}
        f = v["France"]
        out.append(f"{label} {d}: France {f:.0f}, rang {1+sum(1 for x in v.values() if x > f)}/{len(v)} (ex aequo avec {[k for k,x in v.items() if x==f and k!='France']})")
    v = {r["system"]: sum(val(r, d) for d in dom) / 3 for r in sub if all(val(r, d) is not None for d in dom)}
    f = v["France"]
    out.append(f"{label} moyenne des 3 domaines: France {f:.1f}, rang {1+sum(1 for x in v.values() if x > f)}/{len(v)}")
ranks(rows, "Tous systemes")
ranks([r for r in rows if r["oecd_member"] == "1"], "Membres OCDE")
sub = [r for r in rows if r["oecd_member"] == "1"]
for d in dom:
    vs = [val(r, d) for r in sub]
    out.append(f"Moyenne simple des {len(vs)} membres OCDE, {d}: {sum(vs)/len(vs):.1f}")
os.makedirs(os.path.join(root, "data/processed"), exist_ok=True)
open(os.path.join(root, "data/processed/rank_pisa2025.txt"), "w").write("\n".join(out) + "\n")
print("\n".join(out))
