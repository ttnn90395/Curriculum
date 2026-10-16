"""Remplit data/manual/pisa_means_2022_2025.csv depuis l'API SDMX officielle de l'OCDE.
Strict: aucune ecriture si l'extraction est ambigue.
Usage: python code/fetch_pisa_oecd.py            (auto)
       python code/fetch_pisa_oecd.py --grep XXX (liste les jeux dont le nom contient XXX)
"""
import io, sys, requests
import pandas as pd
import xml.etree.ElementTree as ET

sys.path.insert(0, "code")
from forecast_rankings import OECD38_ISO3
from pisa_extended import DEFAULT, load_manual

BASE = "https://sdmx.oecd.org/public/rest"
SUBJ = {"mathematics": "mathematic", "reading": "reading", "science": "science"}
H = {"User-Agent": "Mozilla/5.0 (projet-education)"}
KEYS = ("pisa", "international student assessment")


def all_flows():
    r = requests.get(f"{BASE}/dataflow/all", headers=H, timeout=180)
    print("HTTP", r.status_code, "-", len(r.content), "octets")
    r.raise_for_status()
    out = []
    for el in ET.fromstring(r.content).iter():
        if el.tag.endswith("}Dataflow"):
            name = next((c.text for c in el if c.tag.endswith("}Name") and c.text), "")
            out.append((el.get("agencyID"), el.get("id"), el.get("version"), name))
    return out


def extract(df):
    df.columns = [c.upper() for c in df.columns]
    for need in ("REF_AREA", "TIME_PERIOD", "OBS_VALUE"):
        if need not in df.columns:
            return None, f"colonne {need} absente (colonnes: {list(df.columns)[:20]})"
    df = df[df["REF_AREA"].isin(OECD38_ISO3) & df["TIME_PERIOD"].astype(str).isin(["2022", "2025"])].copy()
    for col in ("SEX", "GENDER"):
        if col in df.columns:
            df = df[df[col].astype(str).str.upper().isin(["_T", "T", "TOTAL", "ALL"])]
    txt = df.drop(columns=["OBS_VALUE"]).astype(str).agg(" ".join, axis=1).str.lower()
    keep = txt.str.contains(r"\bmean\b|\baverage\b") & ~txt.str.contains("standard|percentile|share|proportion|variance|gap|change")
    df, txt = df[keep], txt[keep]
    parts = []
    for s, kw in SUBJ.items():
        sub = df[txt.str.contains(kw)].copy()
        sub["subject"] = s
        parts.append(sub)
    d = pd.concat(parts)
    if d.empty:
        return None, "aucune ligne 'moyenne' pour 2022/2025"
    d["cycle"] = d["TIME_PERIOD"].astype(int)
    dup = d.duplicated(["REF_AREA", "subject", "cycle"], keep=False)
    if dup.any():
        g = d[dup].groupby(["REF_AREA", "subject", "cycle"])
        cols = [c for c in d.columns if g[c].nunique().max() > 1]
        return None, f"{int(dup.sum())} lignes ambigues; colonnes qui different: {cols}"
    return d[["REF_AREA", "subject", "cycle", "OBS_VALUE"]].rename(columns={"REF_AREA": "iso3", "OBS_VALUE": "mean"}), None


def main():
    flows = all_flows()
    print(len(flows), "jeux de donnees OCDE au total")
    if "--grep" in sys.argv:
        kw = sys.argv[sys.argv.index("--grep") + 1].lower()
        for f in flows:
            if kw in f[3].lower() or kw in (f[1] or "").lower():
                print("  ", f)
        return
    cand = [f for f in flows if any(k in f[3].lower() or k in (f[1] or "").lower() for k in KEYS)]
    print("Jeux PISA trouves:", len(cand))
    for f in cand:
        print("  ", f)
    if not cand:
        sys.exit("Aucun jeu PISA dans le catalogue. Essayer: python code/fetch_pisa_oecd.py --grep student")
    tmpl = pd.read_csv(DEFAULT, dtype={"source_table": str, "iso3": str, "subject": str})
    tmpl["source_table"] = tmpl["source_table"].astype(object)
    tmpl = tmpl.set_index(["iso3", "subject", "cycle"])
    for ag, fid, ver, name in cand:
        url = f"{BASE}/data/{ag},{fid},{ver}/all?startPeriod=2022&format=csvfilewithlabels"
        print(f"\nEssai: {name} ({fid})")
        try:
            r = requests.get(url, headers=H, timeout=600)
            r.raise_for_status()
            res, err = extract(pd.read_csv(io.StringIO(r.text), low_memory=False))
        except Exception as e:
            print("  echec:", str(e)[:300])
            continue
        if res is None:
            print("  ecarte:", err)
            continue
        print(f"  OK: {len(res)} valeurs extraites")
        for _, x in res.iterrows():
            tmpl.loc[(x.iso3, x.subject, int(x.cycle)), "mean"] = round(float(x["mean"]), 1)
            tmpl.loc[(x.iso3, x.subject, int(x.cycle)), "source_table"] = f"OECD SDMX {ag},{fid},{ver}"
        tmpl.reset_index().to_csv(DEFAULT, index=False)
        print("Ecrit:", DEFAULT)
        load_manual(DEFAULT)
        return
    sys.exit("Aucun jeu exploitable. Colle-moi la sortie ci-dessus.")


main()