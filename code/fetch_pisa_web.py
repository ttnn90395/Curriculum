"""Remplit data/manual/pisa_means_2022_2025.csv depuis des tableaux HTML publics.

v2 (corrige): v1 lisait les colonnes "par position" et a pris des annees
anterieures pour la lecture et les sciences. Ici:
  * la colonne d'une ANNEE est reperee par son en-tete (ex. "2022");
  * la MATIERE d'un tableau multi-annees est identifiee en comparant sa colonne
    2018 aux scores 2018 de la Banque mondiale deja telecharges (source
    independante, >= 90 % des pays a +-1 point). Sans cela, la matiere n'est
    pas acceptee (pas de lecture positionnelle);
  * ancre maths: France 474 (2022) / 458 (2025), +-1.
Rien n'est ecrit si ces controles echouent. Source Wikipedia = secondaire.

Usage: python code/fetch_pisa_web.py                 (2022 puis 2025)
       python code/fetch_pisa_web.py --year 2025 --extra-url https://...
"""
import io, re, sys, argparse, unicodedata, warnings
import requests
import pandas as pd

sys.path.insert(0, "code")
from forecast_rankings import OECD38_ISO3, load_worldbank_json
from pisa_extended import DEFAULT, load_manual, SANITY
from pathlib import Path

warnings.simplefilter("ignore")
H = {"User-Agent": "Mozilla/5.0 (projet-education; recherche academique)"}
SUBJECTS = ("mathematics", "reading", "science")
KW = {"mathematics": "math", "reading": "read", "science": "scien"}
NAMES = {
 "AUS": ["australia"], "AUT": ["austria"], "BEL": ["belgium"], "CAN": ["canada"], "CHL": ["chile"],
 "COL": ["colombia"], "CRI": ["costarica"], "CZE": ["czechrepublic", "czechia"], "DNK": ["denmark"],
 "EST": ["estonia"], "FIN": ["finland"], "FRA": ["france"], "DEU": ["germany"], "GRC": ["greece"],
 "HUN": ["hungary"], "ISL": ["iceland"], "IRL": ["ireland"], "ISR": ["israel"], "ITA": ["italy"],
 "JPN": ["japan"], "KOR": ["korea", "southkorea", "republicofkorea"], "LVA": ["latvia"],
 "LTU": ["lithuania"], "LUX": ["luxembourg"], "MEX": ["mexico"], "NLD": ["netherlands"],
 "NZL": ["newzealand"], "NOR": ["norway"], "POL": ["poland"], "PRT": ["portugal"],
 "SVK": ["slovakia", "slovakrepublic"], "SVN": ["slovenia"], "ESP": ["spain"], "SWE": ["sweden"],
 "CHE": ["switzerland"], "TUR": ["turkey", "turkiye"], "GBR": ["unitedkingdom", "uk"],
 "USA": ["unitedstates", "unitedstatesofamerica", "us"],
}
LOOKUP = {v: k for k, vs in NAMES.items() for v in vs}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\[.*?\]|\(.*?\)", "", s)
    return re.sub(r"[^a-z]", "", s)


def num(x):
    m = re.match(r"\s*(\d{3}(?:\.\d+)?)", str(x))
    return float(m.group(1)) if m else float("nan")


def wb2018():
    out = {}
    for s in SUBJECTS:
        p = Path("data/raw") / f"worldbank_pisa_{s}.json"
        if p.exists():
            df = load_worldbank_json(p)
            out[s] = df[df["cycle"] == 2018].set_index("country")["score"].to_dict()
    return out


def parse_tables(tables, years, wb):
    """-> {(subject, year): Series iso3->score, plus info}"""
    found = {}
    for t in tables:
        t = t.copy()
        t.columns = [" ".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in t.columns]
        ccol = next((c for c in t.columns if t[c].map(lambda v: LOOKUP.get(norm(v))).notna().sum() >= 36), None)
        if ccol is None:
            continue
        iso = t[ccol].map(lambda v: LOOKUP.get(norm(v)))
        scorecols = {}      # (annee) -> colonne ; ou (annee, matiere)
        for c in t.columns:
            if c == ccol or t[c].map(num).between(250, 650).sum() < 30:
                continue
            ym = re.findall(r"\b(20\d\d|19\d\d)\b", c)
            low = c.lower()
            subj = next((s for s, k in KW.items() if k in low), None)
            if ym:
                scorecols.setdefault((int(ym[0]), subj), c)
        def series(c):
            return pd.Series(t[c].map(num).values, index=iso.values).dropna()
        subjects_in = {k[1] for k in scorecols}
        if None in subjects_in and len(subjects_in) == 1 and (2018, None) in scorecols:
            # tableau multi-annees sans matiere dans l'en-tete: identifier via Banque mondiale
            s18 = series(scorecols[(2018, None)])
            best = None
            for s, ref in wb.items():
                common = [k for k in s18.index if k in ref]
                if len(common) >= 25:
                    ag = sum(abs(s18[k] - ref[k]) <= 1.0 for k in common) / len(common)
                    if ag >= 0.9 and (best is None or ag > best[1]):
                        best = (s, ag)
            if best is None:
                continue
            for y in years:
                if (y, None) in scorecols:
                    found.setdefault((best[0], y), (series(scorecols[(y, None)]), f"colonne {y}; matiere via BM 2018 ({best[1]:.0%} concordance)"))
        else:
            for (y, s), c in scorecols.items():
                if y in years and s:
                    found.setdefault((s, y), (series(c), f"en-tete '{c[:40]}'"))
    return found


# Ancres France 2025 (secondaires, a recouper): maths = ancre du projet; lecture/sciences
# lues sur la page DEPP/digischool qui cite l'OCDE (France 456 / 483).
ANCHOR_FR = {("mathematics", 2025): 458, ("reading", 2025): 456, ("science", 2025): 483}
SRC2025 = {  # pages d'une seule matiere, tableau de moyennes par pays (eduscores.org cite les tableaux OCDE)
    "mathematics": "https://eduscores.org/pisa-math-scores/",
    "reading": "https://eduscores.org/pisa-reading-scores/",
    "science": "https://eduscores.org/pisa-science-scores/",
}


def parse_single_subject_page(tables, subject, year):
    """Choisit, parmi les colonnes numeriques, celle dont la valeur France egale l'ancre (+-0.5)."""
    anchor = ANCHOR_FR[(subject, year)]
    for t in tables:
        t = t.copy()
        t.columns = [" ".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in t.columns]
        ccol = next((c for c in t.columns if t[c].map(lambda v: LOOKUP.get(norm(v))).notna().sum() >= 30), None)
        if ccol is None:
            continue
        iso = t[ccol].map(lambda v: LOOKUP.get(norm(v)))
        for c in t.columns:
            if c == ccol:
                continue
            vals = pd.Series(t[c].map(num).values, index=iso.values).dropna()
            vals = vals[vals.index.notna()]
            if len(vals) >= 30 and "FRA" in vals.index and abs(vals["FRA"] - anchor) <= 0.5:
                return vals[~vals.index.duplicated()], f"colonne '{c[:30]}' choisie par ancre France={anchor}"
    return None, None


def candidate_urls(extra):
    urls = list(extra) + ["https://en.wikipedia.org/wiki/Programme_for_International_Student_Assessment"]
    return list(dict.fromkeys(urls))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, choices=(2022, 2025))
    ap.add_argument("--extra-url", action="append", default=[])
    a = ap.parse_args()
    years = [a.year] if a.year else [2022, 2025]
    wb = wb2018()
    if not wb:
        print("[note] scores BM 2018 absents (download_data.py --pisa-wb): identification de matiere impossible pour les tableaux multi-annees.")
    df = pd.read_csv(DEFAULT, dtype={"source_table": str, "iso3": str, "subject": str})
    df["source_table"] = df["source_table"].astype(object)
    wrote = False
    if 2025 in years:
        mask = df["cycle"] == 2025
        got = 0
        for s, url in SRC2025.items():
            try:
                r = requests.get(url, headers=H, timeout=60); r.raise_for_status()
                ser, how = parse_single_subject_page(pd.read_html(io.StringIO(r.text)), s, 2025)
            except Exception as e:
                print(f"- 2025 {s}: {url} : {str(e)[:90]}"); continue
            if ser is None:
                print(f"- 2025 {s}: {url} : aucune colonne ne satisfait l'ancre France={ANCHOR_FR[(s, 2025)]} -> ignoree")
                continue
            sel0 = mask & (df["subject"] == s)
            df.loc[sel0, ["mean", "source_table"]] = [float("nan"), None]
            for iso, v in ser.items():
                sel = sel0 & (df["iso3"] == iso)
                df.loc[sel, "mean"] = v
                df.loc[sel, "source_table"] = f"{url} [{how}]"
            got += 1; wrote = True
            print(f"  2025 {s}: {len(ser)} pays ({how})")
            print("     " + "  ".join(f"{k}={ser[k]:.0f}" for k in ["FRA", "DEU", "POL", "FIN", "KOR", "USA"] if k in ser.index))
        years = [y for y in years if y != 2025]
    for url in (candidate_urls(a.extra_url) if years else []):
        try:
            r = requests.get(url, headers=H, timeout=60); r.raise_for_status()
            tabs = pd.read_html(io.StringIO(r.text))
        except Exception as e:
            print(f"- {url[:90]} : {str(e)[:90]}"); continue
        found = parse_tables(tabs, years, wb)
        print(f"- {url[:90]} : {len(tabs)} tableaux, {len(found)} series (matiere, annee) identifiees")
        for y in years:
            anchor = SANITY[("FRA", "mathematics", y)]
            m = found.get(("mathematics", y))
            if m is None or "FRA" not in m[0].index or abs(m[0]["FRA"] - anchor) > 1.0:
                print(f"  {y}: maths absentes ou ancre France={anchor} non satisfaite -> annee ignoree")
                continue
            mask_y = df["cycle"] == y
            df.loc[mask_y, ["mean", "source_table"]] = [float("nan"), None]
            for s in SUBJECTS:
                if (s, y) not in found:
                    print(f"  {y} {s}: NON IDENTIFIEE (laissee vide)"); continue
                ser, how = found[(s, y)]
                for iso, v in ser.items():
                    sel = mask_y & (df["subject"] == s) & (df["iso3"] == iso)
                    df.loc[sel, "mean"] = v
                    df.loc[sel, "source_table"] = f"{url} [{how}]"
                print(f"  {y} {s}: {len(ser)} pays ({how})")
                print("     " + "  ".join(f"{k}={ser[k]:.0f}" for k in ["FRA", "DEU", "POL", "FIN", "KOR", "USA"] if k in ser.index))
            wrote = True
    if not wrote:
        sys.exit("Rien ecrit (aucune annee validee).")
    df.to_csv(DEFAULT, index=False)
    print("\nEcrit:", DEFAULT)
    load_manual(DEFAULT)
    print("\nA FAIRE: recouper 4-5 pays avec l'annexe OCDE (source secondaire).")


main()