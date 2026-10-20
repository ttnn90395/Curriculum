#!/usr/bin/env python3
"""fetch_timss2015_hours.py -- telecharge l'exhibit TIMSS 2015 (9.1, G4: heures de maths par an) et INSPECTE sa grille brute.
Format .xls (ancien): lecture via pandas + xlrd (pip install xlrd). Aucune interpretation avant lecture de la structure."""
import hashlib, sys, urllib.request
from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)
DEST = RAW / "timss2015_instruction_time_g4.xls"
BASE = "timss2015.org/wp-content/uploads/filebase/mathematics/9.-classroom-instruction/9_1_math-instructional-time-spent-on-mathematics-grade-4.xls"


def inspect_grid(path, engine=None, nrows=24, w=14):
    book = pd.read_excel(path, sheet_name=None, header=None, engine=engine)
    print(f"  feuilles: {list(book)}")
    for sn, df in list(book.items())[:3]:
        print(f"  --- feuille '{sn}' : {df.shape} ---")
        for i, r in df.head(nrows).iterrows():
            cells = [f"{j}={str(v)[:w]}" for j, v in enumerate(r.tolist()) if pd.notna(v)]
            if cells:
                print(f"   L{i:02d}: " + "  ".join(cells)[:230])


if __name__ == "__main__":
    data = None
    for scheme in ("https://", "http://"):
        try:
            req = urllib.request.Request(scheme + BASE, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=90).read()
            print(f"telecharge via {scheme}: {len(data)} octets; sha256 {hashlib.sha256(data).hexdigest()[:16]}; debut {data[:8]!r}")
            break
        except Exception as e:
            print(f"{scheme}: {type(e).__name__}: {e}")
    if data is None:
        sys.exit("echec de telechargement")
    DEST.write_bytes(data)
    try:
        inspect_grid(DEST, engine="xlrd")
    except ImportError:
        sys.exit("xlrd manquant: pip install xlrd puis relancer")
