#!/usr/bin/env python3
"""oecd_profile_fin.py -- profile en flux (sans stocker) des flux de depenses EAG: valeurs distinctes par dimension, lignes France, dimensions du fichier.
Usage: python3 code/oecd_profile_fin.py [DATAFLOW ...]  (defaut: les deux flux de depenses; periode >= 2022 pour limiter le volume)."""
import csv, sys, io, urllib.request, collections
BASE = "https://sdmx.oecd.org/public/rest/data/OECD.EDU.IMEP,"
FLOWS = sys.argv[1:] or ["DSD_EAG_UOE_FIN@DF_UOE_INDIC_FIN_PERSTUD", "DSD_EAG_UOE_FIN@DF_UOE_INDIC_FIN_GDP"]
CAP = 60
for fl in FLOWS:
    url = f"{BASE}{fl}/all?startPeriod=2022&format=csvfilewithlabels"
    print(f"\n===== {fl}\n{url}", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "curriculum-research/0.1"})
    with urllib.request.urlopen(req, timeout=600) as r:
        rd = csv.DictReader(io.TextIOWrapper(r, encoding="utf-8-sig", newline=""))
        cols = rd.fieldnames; print("colonnes:", cols)
        cnt = {c: collections.Counter() for c in cols}; n = 0; fr = []; nonempty = 0
        for row in rd:
            n += 1
            if row.get("OBS_VALUE", "") != "": nonempty += 1
            for c in cols:
                if c in ("OBS_VALUE", "Observation value", "STRUCTURE", "STRUCTURE_ID", "STRUCTURE_NAME", "ACTION"): continue
                if len(cnt[c]) <= CAP: cnt[c][row[c]] += 1
            if row.get("REF_AREA") == "FRA" and len(fr) < 6 and row.get("OBS_VALUE", "") != "": fr.append(row)
    print(f"lignes: {n}, valeurs non vides: {nonempty}")
    for c in cols:
        if c in cnt and cnt[c]:
            v = cnt[c]; print(f"  {c}: {'>' + str(CAP) + ' valeurs' if len(v) > CAP else str(len(v)) + ' valeurs'}: {list(v)[:CAP]}")
    for row in fr: print("  FRA:", {k: row[k] for k in cols if k in ("MEASURE", "UNIT_MEASURE", "EDUCATION_LEV", "INST_TYPE_EDU", "EXP_SOURCE", "EXPENDITURE_TYPE", "REF_PERIOD", "TIME_PERIOD", "OBS_VALUE", "PRICE_BASE", "FINANCE_TYPE")})
