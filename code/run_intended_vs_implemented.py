"""Curriculum PREVU (coordinateur national) vs MIS EN OEUVRE (enseignants) -- TIMSS G4 maths, 2019 et 2023.
Entrees: data/processed/crosswalk_topic_values_robustesse.csv (prevu 0/0.5/1, high+medium)
         data/processed/teacher_topics_g4_math.csv (enseignants: % avant / cette annee / pas encore)
Table d'appariement ecrite dans data/crosswalk_teacher_g4_math.csv (a relire et commiter).
Mesure de tendance principale: pct_before (libelle identique 2019/2023).
pct_not_yet: 2019 inclut "or just introduced" -> NON comparable entre cycles.
France 2023: ~20 % d'eleves sans reponse enseignant. Descriptif, non causal.
"""
import re
from pathlib import Path
import numpy as np
import pandas as pd

TEACH = Path("data/processed/teacher_topics_g4_math.csv")
PANEL = Path("data/processed/crosswalk_topic_values_robustesse.csv")
MAPCSV = Path("data/crosswalk_teacher_g4_math.csv")
OUTD = Path("data/processed")
FOCUS = ["France", "Germany", "Poland"]
COLS = ["pct_before", "pct_this_year", "pct_not_yet"]

MAPPING = [
    (2019, "ATBM05AA", "N1", ""), (2019, "ATBM05AB", "N2", ""), (2019, "ATBM05AC", "N3", ""),
    (2019, "ATBM05AD", "N6", ""), (2019, "ATBM05AE", "N7", ""), (2019, "ATBM05AF", "N4", ""),
    (2019, "ATBM05AG", "N5", ""), (2019, "ATBM05BA", "G1", "G1 = low, exclu du panel prevu"),
    (2019, "ATBM05BB", "G2", ""), (2019, "ATBM05BC", "G3", ""),
    (2019, "ATBM05BD", "", "paralleles/perpendiculaires: non apparie (comme MA407BD)"),
    (2019, "ATBM05BE", "G4", ""), (2019, "ATBM05BF", "G5", ""), (2019, "ATBM05BG", "G6", ""),
    (2019, "ATBM05CA", "D1", ""), (2019, "ATBM05CB", "D1", ""), (2019, "ATBM05CC", "D2", ""),
    (2023, "ATBM06AA", "N1", ""), (2023, "ATBM06AB", "N2", "additions/soustractions"),
    (2023, "ATBM06AC", "N2", "multiplications"), (2023, "ATBM06AD", "N2", "divisions"),
    (2023, "ATBM06AE", "N3", "pair/impair, multiples, facteurs"), (2023, "ATBM06AF", "N3", "arrondis/estimations"),
    (2023, "ATBM06AG", "N6", "nombre manquant"), (2023, "ATBM06AH", "N7", ""),
    (2023, "ATBM06AI", "N4", "representer/comparer"), (2023, "ATBM06AJ", "N4", "additionner/soustraire"),
    (2023, "ATBM06AK", "N5", "representer/comparer"), (2023, "ATBM06AL", "N5", "additionner/soustraire"),
    (2023, "ATBM06BA", "G1", "G1 = low, exclu du panel prevu"), (2023, "ATBM06BB", "G2", ""),
    (2023, "ATBM06BC", "G3", "perimetres"), (2023, "ATBM06BD", "G3", "aires/volumes"),
    (2023, "ATBM06BE", "G4", "paralleles/perpendiculaires (fusionne avec angles cote prevu)"),
    (2023, "ATBM06BF", "G4", "angles"), (2023, "ATBM06BG", "G5", "figures 2D"),
    (2023, "ATBM06BH", "G6", "solides 3D"),
    (2023, "ATBM06CA", "D1", "lire"), (2023, "ATBM06CB", "D1", "creer"), (2023, "ATBM06CC", "D2", ""),
]


def norm(s):
    s = str(s).lower().replace("&", "and").replace("t\u00fcrkiye", "turkey")
    return re.sub(r"[^a-z0-9 ]", "", s).strip()


def main():
    for p in (TEACH, PANEL):
        if not p.exists():
            raise SystemExit(f"MANQUANT: {p}")
    mp = pd.DataFrame(MAPPING, columns=["cycle", "sheet", "topic_id", "note"])
    mp.to_csv(MAPCSV, index=False)
    print(f"Table d'appariement ecrite: {MAPCSV} ({len(mp)} lignes) -- a relire puis commiter.")

    t = pd.read_csv(TEACH).merge(mp[mp.topic_id.notna() & (mp.topic_id != "")], on=["cycle", "sheet"], how="inner")
    t["ckey"] = t["country"].map(norm)
    g = t.groupby(["cycle", "ckey", "topic_id"])
    agg = g[COLS].mean()
    agg[g[COLS[0]].count() < g.size()] = np.nan
    agg["country_t"] = g["country"].first()
    agg = agg.reset_index()

    pn = pd.read_csv(PANEL)
    pn = pn[pn.cycle.isin([2019, 2023])].copy()
    pn["ckey"] = pn["country"].map(norm)
    pn = pn.rename(columns={"value": "intended", "country": "country_p"})
    m = agg.merge(pn[["cycle", "ckey", "topic_id", "intended", "country_p"]],
                  on=["cycle", "ckey", "topic_id"], how="inner").dropna(subset=["intended"] + COLS)
    m["country"] = m["country_p"]
    for cy in (2019, 2023):
        tc, pc = set(agg[agg.cycle == cy].ckey), set(pn[pn.cycle == cy].ckey)
        print(f"[{cy}] pays almanac {len(tc)}, pays curriculum {len(pc)}, communs {len(tc & pc)}; "
              f"hors appariement (curriculum): {sorted(pn[(pn.cycle == cy) & ~pn.ckey.isin(tc)].country_p.unique())[:12]}")
    OUTD.mkdir(parents=True, exist_ok=True)
    m.drop(columns=["country_p", "country_t"], errors="ignore").to_csv(OUTD / "intended_vs_implemented_g4.csv", index=False)
    print(f"Ecrit: {OUTD / 'intended_vs_implemented_g4.csv'} ({len(m)} lignes)")

    pd.set_option("display.width", 220)
    for cy in (2019, 2023):
        print(f"\n===== {cy}: prevu (I) vs enseigne (B=avant, T=cette annee, N=pas encore, en %) =====")
        sub = m[(m.cycle == cy) & m.country.isin(FOCUS)]
        for tid, gg in sub.groupby("topic_id"):
            cells = []
            for c in FOCUS:
                r = gg[gg.country == c]
                cells.append(f"{c[:3]}: I={r.intended.iloc[0]:.1f} B={r.pct_before.iloc[0]:3.0f} T={r.pct_this_year.iloc[0]:3.0f} N={r.pct_not_yet.iloc[0]:3.0f}"
                             if len(r) else f"{c[:3]}: --")
            print(f"  {tid:3s} " + " | ".join(cells))

    print("\n===== B. Prevu vs mis en oeuvre, tous pays (par cycle) =====")
    for cy in (2019, 2023):
        s = m[m.cycle == cy]
        rho_b = s["intended"].corr(s["pct_before"], method="spearman")
        rho_n = s["intended"].corr(s["pct_not_yet"], method="spearman")
        print(f"[{cy}] n={len(s)} pays-sujets; Spearman(prevu, %avant)={rho_b:+.2f}; Spearman(prevu, %pas encore)={rho_n:+.2f}")
        print(s.groupby("intended")[COLS].agg(["median", "count"]).round(0).to_string())

    print("\n===== C. Evolution 2019 -> 2023 (sujets communs; %avant = mesure stable) =====")
    a = m[m.cycle == 2019].set_index(["country", "topic_id"])[["intended", "pct_before"]]
    b = m[m.cycle == 2023].set_index(["country", "topic_id"])[["intended", "pct_before"]]
    d = (b - a).dropna()
    tr = d.groupby("country").agg(n_topics=("intended", "size"), d_prevu=("intended", "mean"), d_before=("pct_before", "mean"))
    tr = tr[tr.n_topics >= 3].round(2)
    tr["rang_d_prevu"] = tr.d_prevu.rank(ascending=False, method="min").astype(int)
    tr["rang_d_before"] = tr.d_before.rank(ascending=False, method="min").astype(int)
    tr.to_csv(OUTD / "intended_vs_implemented_trends.csv")
    print(f"{len(tr)} pays; mediane d_prevu={tr.d_prevu.median():+.2f}, mediane d_before={tr.d_before.median():+.1f} pts")
    print(tr.loc[tr.index.isin(FOCUS)].to_string())
    print(f"Spearman entre pays (d_prevu, d_before) = {tr.d_prevu.corr(tr.d_before, method='spearman'):+.2f}")
    print("\nRappel: prevu = declaration du coordinateur; enseigne = declaration des enseignants "
          "(France 2023: ~20 % d'eleves sans reponse enseignant); descriptif, non causal.")


if __name__ == "__main__":
    main()
