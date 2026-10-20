#!/usr/bin/env python3
"""parse_timss_hours.py -- extrait l'exhibit 12.2 (G4 maths) du fichier TIMSS 2019 en CSV propre, puis
telecharge et inspecte le rapport Eurydice 2024/25 (copie hebergee) pour reperer les tableaux d'heures.
Structure du xlsx observee (2026-10-20): feuille '12.2 G4 MAT', en-tete ligne 4, colonnes
2=pays, 4=drapeau (heures totales), 5=heures totales/an, 6=ES, 8=drapeau (maths), 9=heures de maths/an, 10=ES."""
import re, sys, hashlib, subprocess, urllib.request
from pathlib import Path
import openpyxl
import pandas as pd

RAW, OUT = Path("data/raw"), Path("data/processed")
XLSX = RAW / "timss2019_instruction_time_m48.xlsx"
SHEET = "12.2 G4 MAT"
C = dict(country=2, flag_total=4, total=5, total_se=6, flag_math=8, math=9, math_se=10)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
rows = [list(r) for r in wb[SHEET].iter_rows(values_only=True)]
wb.close()
recs, tail = [], []
for i, r in enumerate(rows):
    r = r + [None] * (12 - len(r))
    m = num(r[C["math"]])
    if r[C["country"]] and m is not None and i >= 5:
        recs.append(dict(country_raw=str(r[C["country"]]).strip(),
                         flag_total=(str(r[C["flag_total"]]).strip() if r[C["flag_total"]] else ""),
                         total_hours=num(r[C["total"]]), total_se=num(r[C["total_se"]]),
                         flag_math=(str(r[C["flag_math"]]).strip() if r[C["flag_math"]] else ""),
                         math_hours=m, math_se=num(r[C["math_se"]])))
    elif any(v is not None for v in r) and i >= 5:
        tail.append((i, [str(v)[:110] for v in r if v is not None]))
df = pd.DataFrame(recs)
df.to_csv(OUT / "timss2019_math_hours_g4.csv", index=False)
print(f"{len(df)} pays; heures de maths/an: min {df.math_hours.min():.0f}, mediane {df.math_hours.median():.0f}, max {df.math_hours.max():.0f}")
print("drapeaux maths:", df.flag_math.value_counts(dropna=False).to_dict())
for key in ["France", "Germany", "Poland", "Finland", "England", "Japan", "Korea"]:
    print(" ", df[df.country_raw.str.startswith(key)].to_dict("records"))
print("\nLignes hors donnees (legende des drapeaux, notes) :")
for i, cells in tail[-12:]:
    print(f"  L{i:02d}: {' | '.join(cells)}")

# ---- rapport Eurydice (copie hebergee) ----
URL = "https://www.frse.org.pl/brepo/panel_repo_files/2025/07/08/r7nxi1/recommended-annual-instruction-time-in-full-time-c.pdf"
PDF = RAW / "eurydice_instruction_time_2025_report.pdf"
print("\n== Rapport Eurydice 2024/25")
try:
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=120).read()
    PDF.write_bytes(data)
    print(f"  {len(data)} octets; sha256 {hashlib.sha256(data).hexdigest()[:16]}; debut {data[:5]!r}")
except Exception as e:
    print(f"  ECHEC telechargement: {type(e).__name__}: {e}")
    sys.exit(0)

pages = None
try:
    import pdfplumber
    with pdfplumber.open(PDF) as pdf:
        pages = [(p.extract_text() or "") for p in pdf.pages]
except Exception as e1:
    try:
        from pypdf import PdfReader
        pages = [(p.extract_text() or "") for p in PdfReader(PDF).pages]
    except Exception as e2:
        try:
            txt = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True, check=True).stdout
            pages = txt.split("\f")
        except Exception as e3:
            print(f"  aucun extracteur PDF disponible ({type(e1).__name__}, {type(e2).__name__}, {type(e3).__name__}); installer: pip install pdfplumber")
if pages:
    (OUT / "eurydice_report_text.txt").write_text("\n\f\n".join(pages), encoding="utf-8")
    print(f"  {len(pages)} pages extraites -> data/processed/eurydice_report_text.txt")
    hit = [i + 1 for i, t in enumerate(pages) if "France" in t and re.search(r"[Mm]athematics", t)]
    print(f"  pages contenant 'France' et 'Mathematics': {hit[:30]}")
    for pno in hit[:6]:
        lines = [l for l in pages[pno - 1].splitlines() if "France" in l or "Mathematics" in l or "Table" in l or "Figure" in l]
        print(f"  -- p.{pno}:")
        for l in lines[:8]:
            print("     ", l[:200])
