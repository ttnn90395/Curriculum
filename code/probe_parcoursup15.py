"""Sonde 15 : telechargement des jeux Parcoursup 2018-2025 et controle des champs de mention et de filiere.
Sorties : data/raw/parcoursup/*.csv, data/processed/probe_parcoursup15.txt"""
import csv, gzip, os, sys, urllib.request
csv.field_size_limit(10**8)
H = "https://data.enseignementsup-recherche.gouv.fr/"
ID = {2018: "fr-esr-parcoursup-2018", 2019: "fr-esr-parcoursup-2019", 2020: "fr-esr-parcoursup_2020",
      2021: "fr-esr-parcoursup_2021", 2022: "fr-esr-parcoursup_2022", 2023: "fr-esr-parcoursup_2023",
      2024: "fr-esr-parcoursup_2024", 2025: "fr-esr-parcoursup"}
AG = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
D = "data/raw/parcoursup/"
os.makedirs(D, exist_ok=True)
def telecharge(i, p):
    U = [H + "api/explore/v2.1/catalog/datasets/%s/exports/csv?use_labels=false&delimiter=%%3B" % i,
         H + "explore/dataset/%s/download/?format=csv&use_labels_for_header=false&csv_separator=%%3B" % i]
    for u in U:
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": AG, "Accept-Encoding": "identity"}), timeout=180)
            b = r.read()
            if b[:2] == b"\x1f\x8b":
                b = gzip.decompress(b)
            if len(b) > 10000:
                open(p, "wb").write(b)
                return u[:60]
        except Exception as e:
            sys.stderr.write("  %s : %s\n" % (u[:70], str(e)[:60]))
    return None
def f(x):
    try:
        return float(x)
    except Exception:
        return 0.0
MEN = ["acc_tb", "acc_tbf", "acc_b", "acc_ab", "acc_sansmention", "acc_mention_nonrenseignee"]
out = []
for y, i in sorted(ID.items()):
    p = D + "%d_%s.csv" % (y, i)
    src = "deja present" if os.path.exists(p) else telecharge(i, p)
    out.append("== %d %s : %s" % (y, i, src))
    if not os.path.exists(p):
        continue
    t = open(p, "rb").read().decode("utf-8-sig", "replace")
    R = list(csv.DictReader(t.splitlines(), delimiter=";"))
    cols = {c.lower(): c for c in R[0]}
    pres = [m for m in MEN + ["acc_neobac", "acc_bg", "acc_bt", "acc_bp", "fili", "session"] if m in cols]
    manq = [m for m in MEN + ["acc_neobac", "fili", "session"] if m not in cols]
    out.append("   %d lignes ; session(s) %s ; champs presents %d ; absents %s" % (
        len(R), sorted({r[cols["session"]] for r in R})[:3], len(pres), manq))
    tot = {m: sum(f(r[cols[m]]) for r in R) for m in MEN + ["acc_neobac"] if m in cols}
    out.append("   somme : " + " ; ".join("%s %d" % (m, v) for m, v in tot.items()))
    S = {}
    for r in R:
        k = r[cols["fili"]]
        d = S.setdefault(k, [0, 0.0])
        d[0] += 1
        d[1] += f(r[cols["acc_neobac"]])
    out.append("   fili : " + " | ".join("%s (%d, %d)" % (k[:34], v[0], v[1]) for k, v in sorted(S.items(), key=lambda z: -z[1][1])[:16]))
open("data/processed/probe_parcoursup15.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
