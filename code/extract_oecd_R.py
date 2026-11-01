"""R(t,d) = diplomes de licence / nouveaux entrants de licence d'il y a d ans (Amendement 25, Precisions 29 et 30).
Lit data/raw/oecd/stud_totals.csv. Sorties : data/evidence_oecd_R.csv, data/processed/oecd_R.txt"""
import csv, json, re, statistics as S, urllib.request
OECD = "AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA".split()
EU = {"AUT":"AT","BEL":"BE","CZE":"CZ","DNK":"DK","EST":"EE","FIN":"FI","FRA":"FR","DEU":"DE","GRC":"EL","HUN":"HU","IRL":"IE","ITA":"IT","LVA":"LV","LTU":"LT","LUX":"LU","NLD":"NL","POL":"PL","PRT":"PT","SVK":"SK","SVN":"SI","ESP":"ES","SWE":"SE"}
rows = list(csv.DictReader(open("data/raw/oecd/stud_totals.csv", encoding="utf-8")))
codes = sorted(set(r["EDUCATION_LEV"] for r in rows if re.fullmatch(r"Bachelor.s or equivalent level", r["Education level"])))
if len(codes) != 1:
    raise SystemExit("code CITE 6 non unique : %s" % codes)
LV = codes[0]
V, W = {}, set()
for r in rows:
    if r["EDUCATION_LEV"] != LV or r["SEX"] != "_T" or r["MOBILITY"] != "_T" or r["MEASURE"] not in ("NENT", "GRAD"):
        continue
    if r["REF_AREA"] not in OECD or r["OBS_STATUS"] not in ("A", "W") or not r["OBS_VALUE"]:
        continue
    k = (r["REF_AREA"], r["MEASURE"], int(r["TIME_PERIOD"]))
    V[k] = float(r["OBS_VALUE"])
    if r["OBS_STATUS"] == "W": W.add(k)
def R(c, t, d, src=V):
    g, e = src.get((c, "GRAD", t)), src.get((c, "NENT", t - d))
    return 100.0 * g / e if g is not None and e else None
out = ["code CITE 6 retenu : %s ; %d pays presents" % (LV, len(set(k[0] for k in V)))]
rec = []
for c in OECD:
    for t in range(2015, 2025):
        r3, r4 = R(c, t, 3), (R(c, t, 4) if t >= 2016 else None)
        if r3 is None and r4 is None: continue
        fl = "W" if ((c, "GRAD", t) in W or (c, "NENT", t - 3) in W) else ""
        rec.append([c, t, "" if r3 is None else round(r3, 1), "" if r4 is None else round(r4, 1), fl])
w = csv.writer(open("data/evidence_oecd_R.csv", "w", newline="", encoding="utf-8"))
w.writerow(["pays", "annee", "R3_pct", "R4_pct", "drapeau_W"]); w.writerows(rec)
out.append("\nPar annee (R3) : n pays, mediane, France (valeur, rang 1 = plus haut)")
for t in range(2015, 2025):
    L = {c: R(c, t, 3) for c in OECD if R(c, t, 3) is not None}
    if not L: continue
    f = L.get("FRA"); rg = (1 + sum(1 for v in L.values() if f is not None and v > f)) if f is not None else None
    out.append("  %d : n=%d ; mediane %.1f ; FRA %s ; rang %s" % (t, len(L), S.median(L.values()), "%.1f" % f if f else "-", rg))
def fmt(x):
    return "%5.1f" % x if x is not None else "    -"
def gap(x, y):
    return None if x is None or y is None else y - x
for d, a in ((3, 2015), (4, 2016)):
    out.append("\nR%d : valeurs %d, 2019, 2024 ; ecarts 2019-%d, 2024-2019, 2024-%d (points) ; chaque ecart omis si une de ses deux valeurs manque" % (d, a, a, a))
    G = [[], [], []]
    for c in OECD:
        x = [R(c, t, d) for t in (a, 2019, 2024)]
        e = [gap(x[0], x[1]), gap(x[1], x[2]), gap(x[0], x[2])]
        if all(v is None for v in e): continue
        for i in range(3):
            if e[i] is not None: G[i].append(e[i])
        out.append("  %s %s %s %s | %s %s %s" % (c, fmt(x[0]), fmt(x[1]), fmt(x[2]), fmt(e[0]), fmt(e[1]), fmt(e[2])))
    out.append("  n pays par ecart : %d %d %d ; mediane des ecarts : %s" % (len(G[0]), len(G[1]), len(G[2]),
               " ".join("%+.1f" % S.median(g) if g else "-" for g in G)))
# controle Eurostat
try:
    def es(ds):
        u = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/%s?format=JSON&lang=en&sex=T&age=TOTAL&isced11=ED6&unit=NR" % ds
        j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read())
        ids, size = j["id"], j["size"]
        geo = list(j["dimension"]["geo"]["category"]["index"]); tm = list(j["dimension"]["time"]["category"]["index"])
        out_ = {}
        for key, val in j["value"].items():
            k = int(key); pos = []
            for s in reversed(size): pos.append(k % s); k //= s
            pos = pos[::-1]
            out_[(geo[pos[ids.index("geo")]], int(tm[pos[ids.index("time")]]))] = val
        return out_
    EN, EG = es("educ_uoe_ent01"), es("educ_uoe_grad01")
    gaps = []
    for c3, c2 in EU.items():
        for t in range(2015, 2025):
            a = R(c3, t, 3)
            g, e = EG.get((c2, t)), EN.get((c2, t - 3))
            if a is None or g is None or not e: continue
            gaps.append((c3, t, abs(a - 100.0 * g / e)))
    out.append("\nControle Eurostat : %d couples pays-annee ; ecart absolu max %.1f ; > 2 points : %d" % (
        len(gaps), max(g[2] for g in gaps) if gaps else 0, sum(1 for g in gaps if g[2] > 2)))
    for c, t, g in sorted(gaps, key=lambda z: -z[2])[:8]:
        out.append("  %s %d : %.1f" % (c, t, g))
except Exception as e:
    out.append("\nControle Eurostat non fait : %s" % str(e)[:150])
open("data/processed/oecd_R.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
