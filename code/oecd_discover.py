#!/usr/bin/env python3
"""oecd_discover.py -- decouverte (sans interpretation) des jeux OECD sur les enseignants (EXPLORATOIRE).
1) liste les dataflows de l'agence OECD.EDU.IMEP (Regards sur l'education) dont le nom evoque salaires, temps d'enseignement,
   taille des classes ou ratio eleves/enseignant; 2) telecharge chacun en CSV; 3) imprime dimensions et valeurs pour concevoir
   les requetes ensuite. Aucune donnee n'est interpretee ici. Limite de l'API OECD: ~60 requetes/heure -> peu de requetes."""
import os, re, sys, json, time, urllib.request, urllib.error
import xml.etree.ElementTree as ET
import csv, io
OUT = "data/raw/oecd"; os.makedirs(OUT, exist_ok=True)
BASE = "https://sdmx.oecd.org/public/rest"
KEYS = re.compile(r"salar|teaching time|class size|student.?teacher|pupil|teachers? ", re.I)
def get(url, accept=None):
    req = urllib.request.Request(url, headers={"User-Agent": "curriculum-research/0.1"} | ({"Accept": accept} if accept else {}))
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()
def flows(xml_bytes):
    root = ET.fromstring(xml_bytes)
    out = []
    for el in root.iter():
        if el.tag.endswith("}Dataflow") and el.get("id"):
            name = next((n.text for n in el if n.tag.endswith("}Name") and n.get("{http://www.w3.org/XML/1998/namespace}lang", "en") == "en"), "")
            out.append((el.get("id"), el.get("version", ""), (name or "").strip()))
    return out
def profile(path):
    rows = list(csv.DictReader(io.StringIO(open(path, encoding="utf-8-sig").read())))
    print(f"   lignes: {len(rows)}; colonnes: {list(rows[0].keys()) if rows else []}")
    if not rows: return
    for c in rows[0].keys():
        vals = sorted({r[c] for r in rows if r.get(c) not in (None, "")})
        if 1 < len(vals) <= 14 and not c.startswith(("OBS_VALUE", "TIME_PERIOD")):
            print(f"   {c}: {vals[:14]}")
    years = sorted({r.get("TIME_PERIOD", "") for r in rows}); print(f"   TIME_PERIOD: {years[:3]} .. {years[-3:]}")
if __name__ == "__main__":
    try:
        xml = get(f"{BASE}/dataflow/OECD.EDU.IMEP")
    except Exception as e:
        print("echec liste des dataflows:", e); sys.exit(1)
    open(f"{OUT}/dataflows_OECD_EDU_IMEP.xml", "wb").write(xml)
    fl = flows(xml)
    print(f"{len(fl)} dataflows OECD.EDU.IMEP; retenus par mot-cle:")
    sel = [f for f in fl if KEYS.search(f[2])]
    for i, (fid, ver, name) in enumerate(sel):
        print(f"  [{i}] {fid} v{ver}: {name}")
    json.dump(sel, open(f"{OUT}/dataflows_selection.json", "w"), indent=1)
    if "--download" in sys.argv:
        for fid, ver, name in sel[:int(sys.argv[sys.argv.index("--download") + 1]) if len(sys.argv) > sys.argv.index("--download") + 1 else 6]:
            url = f"{BASE}/data/OECD.EDU.IMEP,{fid}/all?startPeriod=2013&dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
            path = f"{OUT}/{re.sub(r'[^A-Za-z0-9_]+', '_', fid)}.csv"
            try:
                open(path, "wb").write(get(url)); print(f"-- {fid}: {name}"); profile(path)
            except urllib.error.HTTPError as e:
                print(f"-- {fid}: HTTP {e.code} (non telecharge)")
            except Exception as e:
                print(f"-- {fid}: erreur {e}")
            time.sleep(2)
