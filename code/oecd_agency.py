#!/usr/bin/env python3
"""oecd_agency.py -- liste les dataflows d'agences OECD (impots sur les salaires, pensions, remunerations), sans rien interpreter.
Usage: python3 code/oecd_agency.py [AGENCE ...]; par defaut OECD.CTP.TPS (Taxing Wages), OECD.ELS.SPD (pensions), OECD.ELS.SAE (emploi, salaires)."""
import sys, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oecd_discover import get, flows, BASE
KEY = re.compile(r"wage|wedge|labou?r cost|net |earn|pension|contribution|tax", re.I)
os.makedirs("data/raw/oecd", exist_ok=True)
for ag in (sys.argv[1:] or ["OECD.CTP.TPS", "OECD.ELS.SPD", "OECD.ELS.SAE"]):
    try:
        xml = get(f"{BASE}/dataflow/{ag}")
    except Exception as e:
        print(f"== {ag}: echec ({e})"); continue
    open(f"data/raw/oecd/dataflows_{ag.replace('.', '_')}.xml", "wb").write(xml)
    fl = flows(xml); sel = [f for f in fl if KEY.search(f[2])]
    print(f"== {ag}: {len(fl)} dataflows, {len(sel)} retenus")
    for fid, ver, name in sel[:60]:
        print(f"   {fid} v{ver}: {name}")
