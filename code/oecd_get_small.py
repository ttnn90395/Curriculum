#!/usr/bin/env python3
"""oecd_get_small.py -- telecharge en flux un petit dataflow OECD.EDU.IMEP (periode >= 2022) vers data/raw/oecd/<nom>.csv, puis imprime
les valeurs distinctes par dimension et les lignes France. Usage: python3 code/oecd_get_small.py FLOW NOM  (ex.: DSD_EAG_UOE_NON_FIN_PERS@DF_UOE_NF_PERS_STR str)"""
import csv, io, sys, urllib.request, collections
flow, name = sys.argv[1], sys.argv[2]
url = f"https://sdmx.oecd.org/public/rest/data/OECD.EDU.IMEP,{flow}/all?startPeriod=2022&format=csvfilewithlabels"
print(url, flush=True)
req = urllib.request.Request(url, headers={"User-Agent": "curriculum-research/0.1"})
raw = urllib.request.urlopen(req, timeout=600).read().decode("utf-8-sig")
open(f"data/raw/oecd/{name}.csv", "w", encoding="utf-8").write(raw)
rows = list(csv.DictReader(io.StringIO(raw))); cols = list(rows[0]); print(f"{len(rows)} lignes; colonnes: {cols}")
skip = {"STRUCTURE", "STRUCTURE_ID", "STRUCTURE_NAME", "ACTION", "OBS_VALUE", "Observation value"}
for c in cols:
    if c in skip or not c.isupper() and c != c.upper(): continue
    v = collections.Counter(r[c] for r in rows)
    if len(v) <= 40 and c == c.upper(): print(f"  {c}: {len(v)} valeurs: {list(v)}")
for r in rows:
    if r.get("REF_AREA") == "FRA" and r["OBS_VALUE"] != "": print("  FRA:", {k: r[k] for k in cols if k == k.upper() and k not in skip and r[k] != "" and k not in ("LAST_UPDATE", "LAST_MODIFIED")} | {"OBS_VALUE": r["OBS_VALUE"]})
