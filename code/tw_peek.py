import csv, sys, re
path = "data/raw/oecd/DSD_TAX_WAGES_DECOMP_DF_TW_DECOMP.csv"
codes = {}; levels = set(); hh = {}; units = {}; seen = []
with open(path, encoding="utf-8-sig") as fh:
    for r in csv.DictReader(fh):
        codes[r["MEASURE"]] = r.get("Measure", ""); levels.add(r["INCOME_PRINCIPAL"]); hh[r["HOUSEHOLD_TYPE"]] = r.get("Household type", "")
        units.setdefault(r["MEASURE"], set()).add(r["UNIT_MEASURE"])
        if r["REF_AREA"] == "FRA" and r["TIME_PERIOD"] == "2025" and r["HOUSEHOLD_TYPE"] == "S_C0" and r["INCOME_PRINCIPAL"] in ("AW70", "AW100", "AW130") and r["OBS_VALUE"] != "":
            seen.append((r["INCOME_PRINCIPAL"], r["MEASURE"], r["UNIT_MEASURE"], r.get("CIVIL_STATUS", ""), r["OBS_VALUE"]))
print("MEASURE (code: libelle; unites):")
for c in sorted(codes): print(f"  {c}: {codes[c]}; {sorted(units[c])}")
print("HOUSEHOLD_TYPE:", hh)
nums = sorted(int(re.sub(r"\D", "", l)) for l in levels if re.sub(r"\D", "", l)); print("INCOME_PRINCIPAL: de AW%d a AW%d, %d niveaux" % (nums[0], nums[-1], len(nums)))
print("France 2025, personne seule sans enfant (S_C0):")
for t in sorted(seen): print("  ", *t)
