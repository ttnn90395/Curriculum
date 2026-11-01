"""Sonde 18 (Precision 29) : metadonnees des jeux OCDE DF_UOE_NF_STUD_TOTALS et Eurostat educ_uoe_ent01 / grad01.
Imprime dimensions, codes et dimensions du jeu de donnees ; aucune valeur d'effectif n'est lue ni imprimee.
Sorties : data/raw/oecd/stud_totals.csv, data/processed/probe_oecd18.txt"""
import csv, io, json, os, re, urllib.request
import xml.etree.ElementTree as ET
os.makedirs("data/raw/oecd", exist_ok=True)
out = []
def pr(s=""):
    print(s); out.append(s)
def get(u, t=300):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=t).read()
DF = "OECD.EDU.IMEP,DSD_EAG_UOE_NON_FIN_STUD@DF_UOE_NF_STUD_TOTALS"
try:
    b = get("https://sdmx.oecd.org/public/rest/data/%s/?startPeriod=2012&dimensionAtObservation=AllDimensions&format=csvfilewithlabels" % DF)
    open("data/raw/oecd/stud_totals.csv", "wb").write(b)
    R = list(csv.DictReader(io.StringIO(b.decode("utf-8", "ignore"))))
    pr("== OCDE %s : %d lignes ; colonnes : %s" % ("DF_UOE_NF_STUD_TOTALS", len(R), list(R[0].keys())))
    for c in R[0].keys():
        if c in ("OBS_VALUE", "Observation value", "TIME_PERIOD", "Time period"): continue
        V = sorted(set(r[c] for r in R))
        pr("   %s : %d valeurs ; %s" % (c, len(V), V[:30]))
    tp = [k for k in R[0].keys() if k in ("TIME_PERIOD",)]
    if tp:
        T = sorted(set(r["TIME_PERIOD"] for r in R)); pr("   annees : %s" % T)
    ra = [k for k in R[0].keys() if k == "REF_AREA"]
    if ra:
        pr("   pays (REF_AREA) : %s" % sorted(set(r["REF_AREA"] for r in R)))
except Exception as e:
    pr("== OCDE ECHEC : %s" % str(e)[:200])
for ds in ("educ_uoe_ent01", "educ_uoe_grad01"):
    try:
        u = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/%s?format=JSON&lang=en&geo=FR&time=2019" % ds
        j = json.loads(get(u, 120))
        pr("== Eurostat %s : dimensions %s" % (ds, j.get("id")))
        for d in j["id"]:
            cat = j["dimension"][d]["category"]
            lab = cat.get("label", {})
            pr("   %s : %s" % (d, "; ".join("%s=%s" % (k, lab.get(k, "")[:40]) for k in list(cat["index"])[:25])))
    except Exception as e:
        pr("== Eurostat %s ECHEC : %s" % (ds, str(e)[:200]))
open("data/processed/probe_oecd18.txt", "w").write("\n".join(out) + "\n")
