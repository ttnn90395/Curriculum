"""Diagnostic (lecture seule) : toutes les lignes France du temps d'enseignement reglementaire dans data/raw/oecd.
Affiche, pour chaque fichier contenant WKT_STA_TCH, les lignes France avec leurs dimensions (niveau, categorie d'enseignant, type de valeur, mesure, unite)."""
import csv, glob, os, sys
csv.field_size_limit(10**9)
found = False
for p in sorted(glob.glob("data/raw/oecd/*.csv")):
    if os.path.getsize(p) > 400_000_000:
        continue
    with open(p, newline="", encoding="utf-8", errors="replace") as f:
        rd = csv.reader(f); head = next(rd, None)
        if not head: continue
        low = [h.upper() for h in head]
        keep = [i for i, h in enumerate(low) if any(k in h for k in ("MEASURE", "EDUCATION", "ISCED", "TEACH", "UNIT", "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS", "ORIENT", "TYPE", "REF_AREA", "NOTE", "COMMENT"))]
        ref = [i for i, h in enumerate(low) if "REF_AREA" in h]
        n = 0
        for row in rd:
            if len(row) != len(head): continue
            if not any(c in ("FRA", "France") for c in (row[i] for i in ref)): continue
            if not any("WKT" in c for c in row): continue
            if not found:
                found = True
            if n == 0: print("==", p); print(" | ".join(head[i] for i in keep))
            print(" | ".join(row[i][:60] for i in keep)); n += 1
            if n >= 120: break
if not found: print("Aucune ligne France WKT trouvee dans data/raw/oecd (hors fichiers > 400 Mo)")
