#!/usr/bin/env python3
"""oecd_fetch.py -- (1) liste TOUS les dataflows OECD.EDU.IMEP deja telecharges (xml local), (2) telecharge les jeux utiles
au calcul du cout d'une heure supplementaire par pays (salaires statutaires, temps d'enseignement, taille des classes),
(3) profil compact + extrait des lignes France. EXPLORATOIRE: aucune interpretation."""
import os, re, sys, csv, io, time, hashlib, urllib.request, urllib.error
import xml.etree.ElementTree as ET
OUT = "data/raw/oecd"; BASE = "https://sdmx.oecd.org/public/rest"
IDS = ["DSD_EAG_SAL_STA@DF_TCH", "DSD_EAG_SAL_STA@DF_TCH_REL", "DSD_EAG_WT@DF_ALL",
       "DSD_EAG_UOE_NON_FIN_PERS@DF_UOE_NF_PERS_CLS", "DSD_EAG_UOE_NON_FIN_PERS@DF_UOE_NF_PERS_STU"]
SKIP = ("STRUCTURE", "ACTION", "DECIMALS", "UNIT_MULT", "OBS_STATUS", "BASE_PER", "STATISTICAL_OPERATION")
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "curriculum-research/0.1"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()
def profile(path, area="FRA"):
    rows = list(csv.DictReader(io.StringIO(open(path, encoding="utf-8-sig").read())))
    print(f"   lignes: {len(rows)}")
    if not rows: return
    cols = [c for c in rows[0].keys() if c.isupper() and not c.startswith(SKIP) and c != "OBS_VALUE"]
    for c in cols:
        vals = sorted({r[c] for r in rows if r.get(c) not in (None, "")})
        if 1 < len(vals) <= 16: print(f"   {c}: {vals}")
        elif len(vals) > 16: print(f"   {c}: {len(vals)} valeurs, ex. {vals[:5]}")
    pays = sorted({r["REF_AREA"] for r in rows if "REF_AREA" in r}); print(f"   pays ({len(pays)}): {pays[:60]}")
    fra = [r for r in rows if r.get("REF_AREA") == area]
    print(f"   lignes {area}: {len(fra)}; extrait:")
    for r in fra[:10]:
        print("     " + " | ".join(f"{c}={r[c]}" for c in cols + ["OBS_VALUE"] if c in r and r[c] not in ("", "_Z") and c != "REF_AREA"))
if __name__ == "__main__":
    xml_path = f"{OUT}/dataflows_OECD_EDU_IMEP.xml"
    if os.path.exists(xml_path) and not sys.argv[1:]:
        root = ET.parse(xml_path).getroot()
        print("== tous les dataflows (id v version: nom)")
        for el in root.iter():
            if el.tag.endswith("}Dataflow") and el.get("id"):
                nm = next((n.text for n in el if n.tag.endswith("}Name")), "")
                print(f"  {el.get('id')} v{el.get('version')}: {nm}")
    for fid in (sys.argv[1:] or IDS):
        ag, fl = fid.split("|") if "|" in fid else ("OECD.EDU.IMEP", fid)
        url = f"{BASE}/data/{ag},{fl}/all?startPeriod=2013&dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
        path = f"{OUT}/{re.sub(r'[^A-Za-z0-9_]+', '_', fl)}.csv"
        try:
            b = get(url); open(path, "wb").write(b)
            print(f"\n-- {fid}: {len(b)/1e6:.1f} Mo; sha256 {hashlib.sha256(b).hexdigest()[:16]}"); profile(path)
        except urllib.error.HTTPError as e:
            print(f"\n-- {fid}: HTTP {e.code} (non telecharge)")
        except Exception as e:
            print(f"\n-- {fid}: erreur {e}")
        time.sleep(2)
