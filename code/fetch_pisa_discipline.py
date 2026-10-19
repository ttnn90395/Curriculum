"""Climat disciplinaire PISA ("bazar en classe"): moyennes par pays et par cycle,
calculees a partir des MICRODONNEES officielles (fichiers eleves, questionnaire).

Pourquoi les microdonnees: les moyennes nationales de l'indice sont dans des annexes
OCDE inaccessibles en HTML; recalculer a partir du fichier eleve est reproductible
(moyenne ponderee par W_FSTUWT, erreur-type BRR avec les 80 poids repliques).

STATUT: URL de telechargement NON VERIFIEES (devinees); le mode --probe dit lesquelles
repondent. Lecture testee sur un faux fichier .sav, jamais sur les vrais fichiers PISA.
Formats geres: .sav, .sas7bdat (dans un zip ou non). Les anciens cycles en texte a
largeur fixe (2000-2012) ne sont pas geres ici.

Usage:
  python code/fetch_pisa_discipline.py --probe
  python code/fetch_pisa_discipline.py --download 2018
  python code/fetch_pisa_discipline.py --extract 2018            # liste les variables DISCLI*
  python code/fetch_pisa_discipline.py --extract 2018 --var DISCLIM
  python code/fetch_pisa_discipline.py --extract 2018 --file chemin/local.zip --var DISCLIM
Verifier dans la sortie le LIBELLE: matiere des cours (maths, lecture, sciences, langue)
differente selon les cycles => les cycles ne sont PAS directement comparables.
"""
import argparse, io, sys, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import requests

sys.path.insert(0, "code")
from forecast_rankings import OECD38_ISO3

H = {"User-Agent": "Mozilla/5.0 (projet-education; recherche academique)"}
RAW = Path("data/raw/pisa_micro")
OUT = Path("data/processed/pisa_discipline_means.csv")
CANDIDATES = {   # UNVERIFIED: a confirmer avec --probe
    2022: ["https://webfs.oecd.org/pisa2022/STU_QQQ_SPSS.zip", "https://webfs.oecd.org/pisa2022/STU_QQQ_SAS.zip"],
    2018: ["https://webfs.oecd.org/pisa2018/SPSS_STU_QQQ.zip"],
    2015: ["https://webfs.oecd.org/pisa/PUF_SPSS_COMBINED_CMB_STU_QQQ.zip"],
}
EXTS = (".sav", ".sas7bdat")


def probe():
    for y, urls in CANDIDATES.items():
        for u in urls:
            try:
                r = requests.get(u, headers=H, stream=True, timeout=30)
                size = int(r.headers.get("Content-Length", 0)) / 1e6
                print(f"{y}  HTTP {r.status_code}  {size:8.0f} Mo  {u}")
                r.close()
            except Exception as e:
                print(f"{y}  ECHEC {str(e)[:70]}  {u}")


def _fetch_resumable(u, dest, tries=8):
    """Telechargement avec reprise (Range) et nouvelles tentatives; fichier .part renomme a la fin."""
    import shutil, time
    part = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, tries + 1):
        have = part.stat().st_size if part.exists() else 0
        hdr = dict(H)
        if have:
            hdr["Range"] = f"bytes={have}-"
        try:
            with requests.get(u, headers=hdr, stream=True, timeout=(30, 120)) as r:
                if r.status_code == 416:            # deja complet
                    break
                if r.status_code not in (200, 206):
                    print(f"  HTTP {r.status_code}"); return False
                total = int(r.headers.get("Content-Length", 0)) + (have if r.status_code == 206 else 0)
                if r.status_code == 200:
                    have = 0
                free = shutil.disk_usage(RAW).free
                if total and free < (total - have) * 1.2:
                    sys.exit(f"Espace disque insuffisant: libre {free/1e9:.1f} Go, besoin {(total-have)/1e9:.1f} Go.")
                with open(part, "ab" if (r.status_code == 206 and have) else "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                if total and part.stat().st_size < total:
                    raise IOError(f"incomplet {part.stat().st_size}/{total}")
                break
        except SystemExit:
            raise
        except Exception as e:
            print(f"  tentative {attempt}/{tries}: {type(e).__name__}: {str(e)[:160]}")
            time.sleep(min(5 * attempt, 30))
    else:
        return False
    part.rename(dest)
    return True


def download(year):
    RAW.mkdir(parents=True, exist_ok=True)
    for u in CANDIDATES[year]:
        dest = RAW / f"{year}_{Path(u).name}"
        if dest.exists():
            print("Deja present:", dest); return dest
        print("Telechargement:", u)
        if _fetch_resumable(u, dest):
            print("Telecharge:", dest, f"({dest.stat().st_size/1e6:.0f} Mo)")
            return dest
    sys.exit(f"Aucun lien exploitable pour {year}. Telecharger le fichier eleve a la main puis --file.")


def open_table(path):
    path = Path(path)
    if path.suffix.lower() == ".zip":
        z = zipfile.ZipFile(path)
        sav = [n for n in z.namelist() if n.lower().endswith(EXTS)]
        name = next((n for n in sav if 'QQQ' in n.upper()), sav[0] if sav else None)
        if name is None:
            sys.exit(f"Pas de .sav/.sas7bdat dans {path}: {z.namelist()[:10]}")
        out = RAW / Path(name).name
        if not out.exists():
            RAW.mkdir(parents=True, exist_ok=True)
            out.write_bytes(z.read(name))
        path = out
    return path


def reader(path):
    import pyreadstat
    return pyreadstat.read_sav if str(path).lower().endswith(".sav") else pyreadstat.read_sas7bdat


def extract(year, file=None, var=None):
    import pyreadstat
    path = open_table(file or download(year))
    rd = reader(path)
    _, meta = rd(str(path), metadataonly=True)
    labels = dict(zip(meta.column_names, meta.column_labels))
    cands = [c for c in meta.column_names if c.upper().startswith("DISCLI")]
    print(f"\n[{year}] variables DISCLI* : ")
    for c in cands:
        print(f"   {c:12s} {labels.get(c)}")
    if var is None:
        if len(cands) == 1:
            var = cands[0]
        else:
            sys.exit("Choisir --var parmi la liste ci-dessus (verifier le libelle: matiere des cours).")
    if var not in meta.column_names:
        sys.exit(f"{var} absente.")
    reps = [c for c in meta.column_names if c.upper().startswith("W_FSTURWT")]
    cols = ["CNT", "W_FSTUWT", var] + reps
    df, _ = rd(str(path), usecols=cols)
    df["CNT"] = df["CNT"].astype(str).str.strip()
    df = df[df["CNT"].isin(OECD38_ISO3) & df[var].notna() & df["W_FSTUWT"].notna()]
    rows = []
    for cnt, g in df.groupby("CNT"):
        x, w = g[var].to_numpy(float), g["W_FSTUWT"].to_numpy(float)
        m = float((x * w).sum() / w.sum())
        se = np.nan
        if len(reps) == 80:      # BRR avec correction de Fay 0,5: var = sum (m_r - m)^2 / (80 * (1-0.5)^2)
            mr = [(x * g[c].to_numpy(float)).sum() / g[c].to_numpy(float).sum() for c in reps]
            se = float(np.sqrt(((np.array(mr) - m) ** 2).sum() / 20.0))
        rows.append(dict(iso3=cnt, cycle=year, variable=var, label=labels.get(var), mean=m, se=se, n=len(g)))
    res = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    old = pd.read_csv(OUT) if OUT.exists() else pd.DataFrame()
    if len(old):
        old = old[old["cycle"] != year]
    pd.concat([old, res], ignore_index=True).to_csv(OUT, index=False)
    print(f"\nEcrit: {OUT}  ({len(res)} pays OCDE, cycle {year}, variable {var})")
    print("Signe: verifier dans le libelle/codebook si une valeur HAUTE = meilleur climat (convention PISA: oui).")
    fr = res[res.iso3 == "FRA"]
    if len(fr):
        print(f"France: {fr['mean'].iloc[0]:+.3f} (se {fr['se'].iloc[0]:.3f}) ; moyenne simple des pays OCDE: {res['mean'].mean():+.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--download", type=int, choices=sorted(CANDIDATES))
    ap.add_argument("--extract", type=int)
    ap.add_argument("--file")
    ap.add_argument("--var")
    a = ap.parse_args()
    if a.probe:
        probe()
    elif a.download:
        download(a.download)
    elif a.extract:
        extract(a.extract, a.file, a.var)
    else:
        ap.print_help()