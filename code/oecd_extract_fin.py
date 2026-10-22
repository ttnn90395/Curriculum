#!/usr/bin/env python3
"""oecd_extract_fin.py -- extrait en flux la depense par eleve (EAG UOE FIN PERSTUD), 1er cycle du secondaire, sources _T, periode >= 2022.
Ecrit data/raw/oecd/fin_perstud_lowsec.csv et imprime la France et le nombre de pays par combinaison (pour verifier l'unicite)."""
import csv, io, urllib.request, collections
URL = "https://sdmx.oecd.org/public/rest/data/OECD.EDU.IMEP,DSD_EAG_UOE_FIN@DF_UOE_INDIC_FIN_PERSTUD/all?startPeriod=2022&format=csvfilewithlabels"
KEEP = ["REF_AREA", "EDUCATION_LEV", "EXP_SOURCE", "EXP_DESTINATION", "EXPENDITURE_TYPE", "PRICE_BASE", "UNIT_MEASURE", "Q_SHEET_ROW_ID", "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS"]
LEV = {"ISCED11_2", "ISCED11_24"}; DST = {"INST_EDU_PUB", "INST_EDU"}; TYP = {"DIR_EXP", "CORE"}; UNI = {"USD_PPP_ST", "PT_B1GQ_POP"}
req = urllib.request.Request(URL, headers={"User-Agent": "curriculum-research/0.1"})
rows = []
with urllib.request.urlopen(req, timeout=900) as r:
    for row in csv.DictReader(io.TextIOWrapper(r, encoding="utf-8-sig", newline="")):
        if (row["EDUCATION_LEV"] in LEV and row["EXP_SOURCE"] == "_T" and row["EXP_DESTINATION"] in DST and row["EXPENDITURE_TYPE"] in TYP
                and row["UNIT_MEASURE"] in UNI and row["OBS_VALUE"] != ""):
            rows.append({k: row[k] for k in KEEP})
with open("data/raw/oecd/fin_perstud_lowsec.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=KEEP); w.writeheader(); w.writerows(rows)
print(f"{len(rows)} lignes retenues")
c = collections.defaultdict(set)
for x in rows: c[(x["EDUCATION_LEV"], x["EXP_DESTINATION"], x["EXPENDITURE_TYPE"], x["PRICE_BASE"], x["UNIT_MEASURE"], x["Q_SHEET_ROW_ID"], x["TIME_PERIOD"])].add(x["REF_AREA"])
print("combinaison (niveau, destination, type, prix, unite, ligne, annee) -> nb de pays:")
for k in sorted(c): print(" ", k, len(c[k]))
print("== France:")
for x in rows:
    if x["REF_AREA"] == "FRA": print(" ", x)
