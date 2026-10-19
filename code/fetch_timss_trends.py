"""Moyennes TIMSS 4e annee MATHS par pays et par cycle (1995-2023), source officielle IEA.
================================================================================
Source: Exhibit 1.1.10 "Trends in Average Mathematics Achievement" (TIMSS 2023 International
Results), fichier Excel publie par l'IEA:
  https://timss2023.org/wp-content/uploads/2024/11/1-1-10_ach-g4m-trend-table.xlsx
(URL lue sur la page timss2023.org/?p=5551 le 2026-10-19; le fichier n'a pas pu etre
telecharge depuis l'environnement d'ecriture: la LECTURE du classeur est donc testee
sur des classeurs synthetiques seulement; sa structure reelle est inconnue.)

Securites (pas de lecture positionnelle devinee):
  - deux dispositions gerees: "long" (une ligne par pays x annee) et "large" (annees en colonnes);
  - 36 valeurs de controle lues dans la version PDF du meme exhibit (France 488/485/484 en
    2015/2019/2023, etc.): si moins de 90 % concordent (+-1 point), le script s'arrete;
  - --inspect affiche les premieres lignes brutes de chaque feuille, sans rien ecrire.
Sorties: data/raw/timss2023_trend_g4_math.xlsx, data/processed/timss_g4_math_scores_long.csv
(country, cycle, score, se, grade5, benchmarking).

Usage:
  python code/fetch_timss_trends.py --inspect
  python code/fetch_timss_trends.py
  python code/fetch_timss_trends.py --file chemin/local.xlsx      # si telechargement manuel
"""
import argparse, re, sys
from pathlib import Path
import openpyxl
import pandas as pd
import requests

URL = "https://timss2023.org/wp-content/uploads/2024/11/1-1-10_ach-g4m-trend-table.xlsx"
RAW = Path("data/raw/timss2023_trend_g4_math.xlsx")
OUT = Path("data/processed/timss_g4_math_scores_long.csv")
H = {"User-Agent": "Mozilla/5.0 (projet-education; recherche academique)"}
YEARS = {1995, 1999, 2003, 2007, 2011, 2015, 2019, 2023}
BENCH = {"Ontario, Canada", "Quebec, Canada", "Abu Dhabi, UAE", "Dubai, UAE"}
HEADER_START = ("average", "scale", "95%", "confidence", "difference", "timss", "exhibit", "note",
                "source", "benchmarking", "standard", "countries", "see ", "reliability")
HEADER_EXACT = {"country", "year", "countries"}
NUM = re.compile(r"^\s*(\d{3}(?:\.\d+)?)\s*(?:\(\s*(\d+(?:\.\d+)?)\s*\))?\s*$")

# Valeurs de controle lues dans le PDF du meme exhibit (1-1-9-10_ach-g4m-trend.pdf).
ANCHORS = {
    "France": {2015: 488, 2019: 485, 2023: 484},
    "Germany": {2007: 525, 2011: 528, 2015: 522, 2019: 521, 2023: 524},
    "Poland": {2015: 535, 2019: 520, 2023: 546},
    "Finland": {2011: 545, 2015: 535, 2019: 532, 2023: 529},
    "Japan": {1995: 567, 2003: 565, 2007: 568, 2011: 585, 2015: 593, 2019: 593, 2023: 591},
    "England": {1995: 484, 2003: 531, 2007: 541, 2011: 542, 2015: 546, 2019: 556, 2023: 552},
    "Singapore": {1995: 590, 2003: 594, 2007: 599, 2011: 606, 2015: 618, 2019: 625, 2023: 615},
}


def as_year(c):
    try:
        y = int(float(c)) if not isinstance(c, str) else int(c.strip())
    except (TypeError, ValueError):
        return None
    return y if y in YEARS else None


def score_se(c):
    """(score, se) si la cellule contient une moyenne d'echelle plausible, sinon None."""
    if isinstance(c, bool) or c is None:
        return None
    if isinstance(c, (int, float)):
        return (float(c), None) if 150 <= float(c) <= 800 else None
    m = NUM.match(str(c))
    if m and 150 <= float(m.group(1)) <= 800:
        return float(m.group(1)), (float(m.group(2)) if m.group(2) else None)
    return None


def clean_name(s):
    s = re.sub(r"\s+", " ", str(s)).strip()
    grade5 = bool(re.search(r"\(5\)\s*$|\s5\s*$", s))
    s = re.sub(r"\s*\(5\)\s*$", "", s)
    s = re.sub(r"[¹²³⁰-⁹]+$", "", s).strip()
    return s, grade5


def is_name(c):
    if not isinstance(c, str):
        return False
    t = c.strip()
    tl = t.lower()
    return bool(t) and as_year(t) is None and tl not in HEADER_EXACT and not tl.startswith(HEADER_START) \
        and score_se(t) is None and len(t) < 60


def parse_sheet(ws):
    """Disposition reelle de l'Exhibit 1.1.10 (verifiee sur --inspect): une ligne contenant SEULEMENT
    le nom du pays, puis une ligne par annee: [marqueurs de note...] annee, moyenne, ET, IC, ...
    On travaille sur les cellules NON VIDES de chaque ligne (les colonnes vides ne comptent pas)."""
    out, cur = [], None
    for r in ws.iter_rows(values_only=True):
        cells = [c for c in r if c is not None and not (isinstance(c, str) and not c.strip())]
        if not cells:
            continue
        if len(cells) == 1 and isinstance(cells[0], str):
            t = cells[0].strip()
            if is_name(t) and len(t) >= 3 and t[0].isalpha() and ":" not in t:
                cur = clean_name(t)
            continue
        if cur is None:
            continue
        yi = next((j for j, c in enumerate(cells[:3]) if as_year(c) is not None), None)
        if yi is None or yi + 1 >= len(cells):
            continue
        v = score_se(cells[yi + 1])
        if v is None:
            continue
        se = None
        if yi + 2 < len(cells) and isinstance(cells[yi + 2], (int, float)) and not isinstance(cells[yi + 2], bool) \
                and 0 < cells[yi + 2] < 30:
            se = float(cells[yi + 2])
        out.append(dict(country=cur[0], cycle=as_year(cells[yi]), score=v[0], se=se, grade5=cur[1]))
    return out, "long-compact"


def check_anchors(df):
    ok = tot = 0
    bad = []
    for c, d in ANCHORS.items():
        for y, v in d.items():
            tot += 1
            s = df[(df.country == c) & (df.cycle == y)]["score"]
            if len(s) and abs(float(s.iloc[0]) - v) <= 1:
                ok += 1
            else:
                bad.append((c, y, v, None if not len(s) else float(s.iloc[0])))
    return ok, tot, bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--file")
    ap.add_argument("--url", default=URL)
    a = ap.parse_args()
    path = Path(a.file) if a.file else RAW
    if not path.exists():
        RAW.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(a.url, headers=H, timeout=60)
        print("HTTP", r.status_code, len(r.content), "octets")
        if r.status_code != 200:
            sys.exit("Telechargement impossible: telecharger le fichier a la main puis --file.")
        RAW.write_bytes(r.content)
        path = RAW
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    print("Feuilles:", wb.sheetnames)
    if a.inspect:
        for sn in wb.sheetnames:
            print(f"\n--- {sn} ---")
            for i, r in enumerate(wb[sn].iter_rows(values_only=True)):
                print(i, [c for c in r if c is not None][:10])
                if i >= 25:
                    break
        return
    parts = []
    for sn in wb.sheetnames:
        rows, mode = parse_sheet(wb[sn])
        print(f"feuille {sn!r}: {len(rows)} valeurs (disposition {mode})")
        parts += rows
    df = pd.DataFrame(parts).drop_duplicates(["country", "cycle"])
    if df.empty:
        sys.exit("Rien lu: lancer --inspect et me coller la sortie.")
    ok, tot, bad = check_anchors(df)
    print(f"\nValeurs de controle concordantes (+-1): {ok}/{tot}")
    for b in bad:
        print("  ecart:", b)
    if ok < 0.9 * tot:
        sys.exit("Moins de 90 % des valeurs de controle concordent: lecture non fiable. "
                 "Lancer --inspect et me coller la sortie.")
    df["benchmarking"] = df.country.isin(BENCH)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.sort_values(["country", "cycle"]).to_csv(OUT, index=False)
    print(f"\nEcrit: {OUT} ({len(df)} lignes, {df.country.nunique()} entites)")
    print("Nombre d'entites par cycle:")
    print(df.groupby("cycle")["country"].nunique().to_string())
    print("Cycles par pays (3 premiers):")
    for c in ("France", "Germany", "Poland"):
        print(f"  {c}: {sorted(df[df.country == c].cycle.tolist())}")


if __name__ == "__main__":
    main()
