#!/usr/bin/env python3
"""estimate_notion_difficulty.py  [EXPLORATOIRE, non aveugle]

Difficulte IRT par objectif du cadre TIMSS 2023 G4 maths, puis par notion KST.
  - items: classification TIMSS 2023 (fichier Item Information), jointure par Item ID
    avec les parametres du fichier IRT TIMSS 2023 (colonne 'Location (bi)').
  - objectif = (aire, numero de topic); verifie manuellement sur les libelles
    (fichier data/processed/difficulty_audit_labels.csv).
  - notion = items poules des objectifs lies (data/framework_timss2023_g4_math.csv).
  - IC: bootstrap sur les items, stratifie par objectif, 4000 repliques, graine fixe.
  - aretes du graphe: difference b(notion) - b(prerequis), descriptive, sans p-valeur
    (les aretes partagent des notions: non independantes).
Le graphe n'est PAS modifie (irt_difficulty reste None)."""
import re, sys, csv, collections
from pathlib import Path
import numpy as np
import pandas as pd
import openpyxl

IRT = "data/raw/timss2023_irt_params_g4.xlsx"
INFO = "data/raw/timss2023_item_info_g4.xlsx"
FRAME = "data/framework_timss2023_g4_math.csv"
OUT = Path("data/processed")
SEED, B = 20261020, 4000
MIN_ITEMS = 5   # seuil POST HOC, fixe apres la 1ere lecture (FD1: 1 item). Resultats donnes avec et sans.
MIN_JOIN = 0.60           # part des items IRT 'M' apparies; sinon arret
ID_RE = re.compile(r"^M[A-Z]\d{5}[A-Z]?$")
C_ID, C_LOC, C_LOCSE, C_SLOPE = 2, 7, 8, 5

sys.path.insert(0, str(Path(__file__).parent))
from kst_extension import EXT


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def rows_of(path, sheet):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    r = [list(x) for x in wb[sheet].iter_rows(values_only=True)]
    wb.close()
    return r


def obj_id(area, topic):
    a = str(area).strip().lower()
    try:
        t = int(topic)
    except (TypeError, ValueError):
        return None
    for key, pre in [("whole numbers", "WN"), ("expressions", "EX"), ("fractions", "FD"),
                     ("measurement", "M"), ("geometry", "GE")]:
        if a.startswith(key):
            return f"{pre}{t}"
    if a.startswith("reading"):
        return f"D{t}"
    if a.startswith("interpreting") or a.startswith("using data"):
        return "D34"
    return None


# ---------- 1. IRT ----------
irt = {}
for r in rows_of(IRT, "Mathematics"):
    if len(r) > C_LOC and r[C_ID] and ID_RE.match(str(r[C_ID]).strip()):
        loc = num(r[C_LOC])
        if loc is not None:
            irt[str(r[C_ID]).strip()] = dict(b=loc, b_se=num(r[C_LOCSE]), a=num(r[C_SLOPE]))
print(f"Items IRT maths avec location numerique: {len(irt)}; prefixes {dict(collections.Counter(i[:4] for i in irt))}")
if len(irt) < 50:
    sys.exit("Trop peu d'items IRT lus: verifier les indices de colonnes.")

# ---------- 2. Info + jointure ----------
recs = []
for sheet in ["T23 G4", "T23 G4 Paper"]:        # LD Paper (echelle numeracy) exclue
    rr = rows_of(INFO, sheet)
    hdr = [str(h).strip() if h is not None else "" for h in rr[0]]
    ix = {h: j for j, h in enumerate(hdr) if h}
    for r in rr[1:]:
        if not r[ix["Item ID"]] or str(r[ix["Subject"]]).strip() != "M":
            continue
        iid = str(r[ix["Item ID"]]).strip()
        o = obj_id(r[ix["Topic Area"]], r[ix["Topic"]])
        recs.append(dict(item=iid, sheet=sheet, obj=o, domain=r[ix["Content Domain"]],
                         area=str(r[ix["Topic Area"]]).strip(), topic=r[ix["Topic"]],
                         cog=r[ix["Cognitive Domain"]], pts=num(r[ix["Maximum Points"]]) or 1.0,
                         scaling=r[ix.get("Scaling Status", 0)] if "Scaling Status" in ix else None,
                         label=str(r[ix["Label"]]) if "Label" in ix else ""))
info = pd.DataFrame(recs).drop_duplicates("item")
print(f"Items info maths (digital+papier): {len(info)}")
info["in_irt"] = info.item.isin(irt)
print("Jointure par prefixe (info -> IRT):")
print(info.assign(p=info.item.str[:4]).groupby("p").in_irt.agg(["sum", "count"]).to_string())
m_irt = [i for i in irt if i.startswith("M")]
join_rate = info.in_irt.sum() / max(1, len(m_irt))
print(f"Items IRT 'M' apparies a une classification 2023: {info.in_irt.sum()} / {len(m_irt)} = {join_rate:.0%}")
_all = set()
for _sh in ['T23 G4', 'T23 G4 Paper', 'T23 G4 LD Paper']:
    _rr = rows_of(INFO, _sh)
    _c = [str(h).strip() if h is not None else '' for h in _rr[0]].index('Item ID')
    _all |= {str(r[_c]).strip() for r in _rr[1:] if r[_c]}
_un = [i for i in m_irt if i not in set(info.item)]
print(f"IRT non apparies: {len(_un)} (par prefixe {dict(collections.Counter(i[:4] for i in _un))}); "
      f"presents ailleurs dans le fichier info (autre feuille/sujet): {sum(i in _all for i in _un)}")
print('  exemples:', _un[:12])
if join_rate < MIN_JOIN:
    print("Prefixes IRT non apparies:", dict(collections.Counter(i[:4] for i in m_irt if i not in set(info.item))))
    sys.exit(f"Jointure < {MIN_JOIN:.0%}: arret (les items IRT sans classification 2023 viennent d'autres cycles).")

d = info[info.in_irt & info.obj.notna()].copy()
d["b"] = d.item.map(lambda i: irt[i]["b"])
d["derived"] = d.label.str.contains("DERIVED", case=False)
d["excluded"] = d.label.str.contains("EXCLUDED", case=False)
d = d[~d.excluded].copy()
d["digital"] = d.item.str.startswith("ME")
print(f"\nItems retenus: {len(d)} (derived {int(d.derived.sum())}, digital {int(d.digital.sum())}, papier {int((~d.digital).sum())})")
d.to_csv(OUT / "difficulty_items_used.csv", index=False)
(d.sort_values(["obj", "item"]).groupby("obj").head(4)[["obj", "item", "area", "topic", "label"]]
   .to_csv(OUT / "difficulty_audit_labels.csv", index=False))

# ---------- 3. objectifs -> notions ----------
fr = pd.read_csv(FRAME).fillna("")
obj2not = {r.obj_id: [x for x in r.notions.split(";") if x] for r in fr.itertuples()}
obj2not["D1"] = obj2not.get("D1", ["d01"]); obj2not["D2"] = obj2not.get("D2", ["d01"])
obj2not["D34"] = sorted(set(obj2not.get("D3", []) + obj2not.get("D4", [])))
notions = sorted({n for v in obj2not.values() for n in v})
not2obj = {n: [o for o, v in obj2not.items() if n in v] for n in notions}

# ---------- 4. estimateurs ----------
rng = np.random.default_rng(SEED)
objs = sorted(d.obj.unique())
bv = {o: d[d.obj == o].b.to_numpy() for o in objs}


def notion_means(vals_by_obj):
    out = {}
    for n in notions:
        s = sum(vals_by_obj[o].sum() for o in not2obj[n] if o in vals_by_obj)
        c = sum(len(vals_by_obj[o]) for o in not2obj[n] if o in vals_by_obj)
        if c:
            out[n] = s / c
    return out


point = notion_means(bv)
boots = []
for _ in range(B):
    boots.append(notion_means({o: rng.choice(v, len(v), replace=True) for o, v in bv.items()}))
bdf = pd.DataFrame(boots)

# objectifs
orows = []
for o in objs:
    v = bv[o]
    bs = np.array([rng.choice(v, len(v)).mean() for _ in range(B)])
    orows.append(dict(obj=o, n_items=len(v), mean_b=v.mean(), median_b=np.median(v),
                      ci_lo=np.percentile(bs, 2.5) if len(v) >= MIN_ITEMS else np.nan,
                      ci_hi=np.percentile(bs, 97.5) if len(v) >= MIN_ITEMS else np.nan,
                      notions=";".join(obj2not.get(o, []))))
odf = pd.DataFrame(orows)
odf.to_csv(OUT / "difficulty_by_objective_g4.csv", index=False)
print("\n== Difficulte (location b, echelle IRT TIMSS) par objectif ==")
print(odf.round(3).to_string(index=False))

# ajuste: b ~ objectif + domaine cognitif + points max, moyenne marginale par objectif
X = pd.get_dummies(d[["obj", "cog"]].astype(str), drop_first=False).astype(float)
X["pts"] = d.pts.to_numpy()
beta, *_ = np.linalg.lstsq(X.to_numpy(), d.b.to_numpy(), rcond=None)
cov_cols = [c for c in X.columns if c.startswith("cog_")] + ["pts"]
base = X[cov_cols].mean().to_numpy()
adj_obj = {}
for o in objs:
    col = f"obj_{o}"
    adj_obj[o] = beta[list(X.columns).index(col)] + sum(beta[list(X.columns).index(c)] * base[k] for k, c in enumerate(cov_cols))
nobj_n = {o: len(bv[o]) for o in objs}
adj_not = {n: sum(adj_obj[o] * nobj_n[o] for o in not2obj[n] if o in adj_obj) / sum(nobj_n[o] for o in not2obj[n] if o in adj_obj)
           for n in notions if any(o in adj_obj for o in not2obj[n])}


def sens(mask):
    sub = d[mask]
    out = {}
    for n in notions:
        v = sub[sub.obj.isin(not2obj[n])].b
        if len(v):
            out[n] = v.mean()
    return out


s_nod, s_dig = sens(~d.derived), sens(d.digital)
rows = []
for n in notions:
    if n not in point:
        continue
    rows.append(dict(notion=n, label=EXT[n].label if n in EXT else "", objectives=";".join(not2obj[n]),
                     n_items=sum(len(bv[o]) for o in not2obj[n] if o in bv),
                     reliable=all(len(bv[o]) >= MIN_ITEMS for o in not2obj[n] if o in bv),
                     mean_b=point[n],
                     ci_lo=bdf[n].quantile(.025) if all(len(bv[o]) >= MIN_ITEMS for o in not2obj[n] if o in bv) else np.nan,
                     ci_hi=bdf[n].quantile(.975) if all(len(bv[o]) >= MIN_ITEMS for o in not2obj[n] if o in bv) else np.nan,
                     adj_b=adj_not.get(n), b_no_derived=s_nod.get(n), b_digital_only=s_dig.get(n),
                     typical_grade=EXT[n].typical_grade if n in EXT else None))
ndf = pd.DataFrame(rows).sort_values("mean_b")
ndf.to_csv(OUT / "notion_difficulty_timss2023_g4.csv", index=False)
print("\n== Difficulte par notion (ordre croissant) ==")
print(ndf.drop(columns="label").round(3).to_string(index=False))
print("\nLimites: notions partageant un objectif (n04/n05; n06/n07; d01 pooled) ont la meme valeur par construction.")

rel = dict(zip(ndf.notion, ndf.reliable))
# ---------- 5. aretes ----------
erows = []
for nid, nt in EXT.items():
    for p in nt.prerequisites:
        if nid in point and p in point and not (set(not2obj[nid]) & set(not2obj[p])):
            diff = point[nid] - point[p]
            pr = float((bdf[nid] - bdf[p] > 0).mean())
            erows.append(dict(prereq=p, notion=nid, b_prereq=point[p], b_notion=point[nid],
                              diff=diff, boot_p_notion_harder=pr, reliable=bool(rel[nid] and rel[p])))
edf = pd.DataFrame(erows).sort_values("diff")
edf.to_csv(OUT / "difficulty_edges_g4.csv", index=False)
n_edges = sum(len(nt.prerequisites) for nt in EXT.values())
print(f"\n== Aretes testables: {len(edf)} / {n_edges} (autres: notion sans item TIMSS ou objectif partage) ==")
print(edf.round(3).to_string(index=False))
for name, e in [('toutes', edf), (f'fiables (objectifs >= {MIN_ITEMS} items)', edf[edf.reliable])]:
    if len(e):
        print(f"\n[{name}] {len(e)} aretes: notion plus difficile que son prerequis (point): {(e['diff'] > 0).sum()}; "
              f"P_boot >= 0.95: {(e.boot_p_notion_harder >= .95).sum()}; inversions franches (P <= 0.05): {(e.boot_p_notion_harder <= .05).sum()}")
sub = ndf[ndf.reliable].dropna(subset=["typical_grade"])
if len(sub) > 3:
    print(f"Spearman(mean_b, typical_grade pilote) sur {len(sub)} notions: "
          f"{sub.mean_b.rank().corr(sub.typical_grade.rank()):.2f}")
print("\nStatut: exploratoire, non aveugle. Aucune p-valeur. Ecritures: data/processed/difficulty_*.csv, notion_difficulty_*.csv")
