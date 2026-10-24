"""Telecharge la depense publique par eleve (Eurostat educ_uoe_fine09, PPS, ED1 et ED24, 2021-2023) vers data/evidence_eurostat_expenditure.csv.
Filtres fixes par la Precision 2 de l'Amendement 13. Aucune autre transformation."""
import json, urllib.request, csv
u = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/educ_uoe_fine09"
     "?format=JSON&lang=en&freq=A&unit=PPS&isced11=ED1&isced11=ED24&lastTimePeriod=3")
d = json.load(urllib.request.urlopen(u, timeout=120))
ids, size = d["id"], d["size"]
def pos(dim):
    idx = d["dimension"][dim]["category"]["index"]
    if isinstance(idx, dict):
        return sorted(idx, key=idx.get)
    return list(idx)
cats = [pos(k) for k in ids]
vals = d["value"]
if isinstance(vals, list):
    vals = {str(i): v for i, v in enumerate(vals) if v is not None}
stat = d.get("status", {}) or {}
if isinstance(stat, list):
    stat = {str(i): s for i, s in enumerate(stat) if s}
stride = [1] * len(size)
for i in range(len(size) - 2, -1, -1):
    stride[i] = stride[i + 1] * size[i + 1]
rows = []
for k, v in vals.items():
    k = int(k)
    c = {ids[i]: cats[i][(k // stride[i]) % size[i]] for i in range(len(ids))}
    rows.append((c["geo"], c["isced11"], c["time"], v, stat.get(str(k), "")))
rows.sort()
with open("data/evidence_eurostat_expenditure.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["geo", "isced11", "time", "pps_per_pupil", "status"])
    w.writerows(rows)
print(len(rows), "lignes ;", len({r[0] for r in rows}), "geo ; periodes :", sorted({r[2] for r in rows}))
