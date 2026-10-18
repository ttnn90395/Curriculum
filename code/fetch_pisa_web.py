"""Remplit data/manual/pisa_means_2022_2025.csv en lisant des tableaux HTML publics.

Sources essayees dans l'ordre: pages d'annexe OCDE (si les tableaux y sont en HTML),
puis Wikipedia (SOURCE SECONDAIRE, recopiee de l'OCDE: a recouper avec l'annexe).
Rigueur: un tableau n'est retenu que si
  - >= 36 des 38 pays OCDE y sont reconnus, valeurs dans [250, 650];
  - la France en maths vaut l'ancre du projet (474 en 2022, 458 en 2025, +-1);
sinon rien n'est ecrit. Colonnes lues dans l'ordre standard maths, lecture, sciences
(verifie par les en-tetes quand ils sont lisibles).

Usage: python code/fetch_pisa_web.py            (2022 et 2025)
       python code/fetch_pisa_web.py --year 2022 --extra-url https://...
"""
import io, re, sys, unicodedata, argparse
import requests
import pandas as pd

sys.path.insert(0, "code")
from forecast_rankings import OECD38_ISO3
from pisa_extended import DEFAULT, load_manual, SANITY

H = {"User-Agent": "Mozilla/5.0 (projet-education; recherche academique)"}
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


def tables_from(url):
    r = requests.get(url, headers=H, timeout=60)
    r.raise_for_status()
    return pd.read_html(io.StringIO(r.text))


def best_table(tables, anchor):
    """Retourne DataFrame iso3 x (mathematics, reading, science) ou None."""
    for t in tables:
        t = t.copy()
        t.columns = [" ".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in t.columns]
        for ccol in t.columns:
            iso = t[ccol].map(lambda v: LOOKUP.get(norm(v)))
            if iso.notna().sum() < 36:
                continue
            numeric = [c for c in t.columns if c != ccol and t[c].map(num).between(250, 650).sum() >= 30]
            if len(numeric) < 3:
                continue
            sub = pd.DataFrame({"iso3": iso})
            hdr = {c: c.lower() for c in numeric}
            pick = {}
            for s, kw in (("mathematics", "math"), ("reading", "read"), ("science", "scien")):
                m = [c for c in numeric if kw in hdr[c]]
                if len(m) == 1:
                    pick[s] = m[0]
            if len(pick) < 3:           # en-tetes illisibles: ordre standard
                pick = dict(zip(("mathematics", "reading", "science"), numeric[:3]))
                how = "ordre positionnel"
            else:
                how = "en-tetes"
            for s, c in pick.items():
                sub[s] = t[c].map(num)
            sub = sub.dropna(subset=["iso3"]).drop_duplicates("iso3").set_index("iso3")
            fr = sub["mathematics"].get("FRA")
            if fr is not None and abs(fr - anchor) <= 1.0:
                return sub, how
    return None, None


def candidate_urls(year, extra):
    urls = list(extra)
    urls += {2022: ["https://www.oecd.org/en/publications/pisa-2022-results-volume-i_53f23881-en/full-report/results-for-countries-and-economies_360c8f67.html"],
             2025: ["https://www.oecd.org/en/publications/pisa-2025-results-volume-i_73451bc5-en/full-report/results-for-countries-and-economies_33854635.html"]}[year]
    try:
        q = f"Programme for International Student Assessment {year}"
        r = requests.get("https://en.wikipedia.org/w/api.php", headers=H, timeout=30,
                         params=dict(action="query", list="search", srsearch=q, srlimit=6, format="json"))
        for h in r.json()["query"]["search"]:
            urls.append("https://en.wikipedia.org/wiki/" + h["title"].replace(" ", "_"))
    except Exception as e:
        print("  (recherche Wikipedia indisponible:", str(e)[:100], ")")
    urls.append("https://en.wikipedia.org/wiki/Programme_for_International_Student_Assessment")
    return list(dict.fromkeys(urls))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, choices=(2022, 2025))
    ap.add_argument("--extra-url", action="append", default=[])
    a = ap.parse_args()
    tmpl = pd.read_csv(DEFAULT, dtype={"source_table": str, "iso3": str, "subject": str})
    tmpl["source_table"] = tmpl["source_table"].astype(object)
    tmpl = tmpl.set_index(["iso3", "subject", "cycle"])
    done = []
    for year in ([a.year] if a.year else [2022, 2025]):
        anchor = SANITY[("FRA", "mathematics", year)]
        print(f"\n=== PISA {year} (ancre: France maths = {anchor}) ===")
        for url in candidate_urls(year, a.extra_url):
            try:
                tabs = tables_from(url)
            except Exception as e:
                print(f"  - {url[:90]} : {str(e)[:80]}")
                continue
            sub, how = best_table(tabs, anchor)
            print(f"  - {url[:90]} : {len(tabs)} tableaux, " + ("TABLEAU RETENU" if sub is not None else "aucun retenu"))
            if sub is None:
                continue
            for iso, row in sub.iterrows():
                for s in ("mathematics", "reading", "science"):
                    if pd.notna(row[s]):
                        tmpl.loc[(iso, s, year), "mean"] = row[s]
                        tmpl.loc[(iso, s, year), "source_table"] = f"{url} ({how})"
            print(f"    {len(sub)} pays; colonnes lues par {how}. Apercu:")
            print(sub.loc[[c for c in ["FRA", "DEU", "POL", "FIN", "KOR", "USA"] if c in sub.index]].to_string())
            done.append(year)
            break
        else:
            print(f"  -> AUCUNE source exploitable pour {year}")
    if done:
        tmpl.reset_index().to_csv(DEFAULT, index=False)
        print("\nEcrit:", DEFAULT)
        load_manual(DEFAULT)
        print("\nA FAIRE: recouper 4-5 pays avec l'annexe OCDE (surtout si la source est Wikipedia).")
    else:
        sys.exit("Rien ecrit.")


main()