"""Extraction E1/E3 Pays-Bas (CBS) selon la Precision 18.
Sorties : data/evidence_exams_international.csv (lignes NL), data/processed/exams_nl_report.txt"""
import csv, gzip, json, os, urllib.parse, urllib.request
UA = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
CB = "https://opendata.cbs.nl/ODataFeed/odata/"
def get(u):
    b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90).read()
    if b[:2] == b"\x1f\x8b":
        b = gzip.decompress(b)
    return json.loads(b.decode("utf-8"))
def lignes(t, flt):
    u = CB + t + "/TypedDataSet?$format=json&$filter=" + urllib.parse.quote(flt)
    R = []
    while u:
        j = get(u)
        R += j["value"]
        u = j.get("odata.nextLink") or j.get("@odata.nextLink")
    return R
def serie(t, flt):
    S = {}
    for r in lignes(t, flt):
        p = r["Perioden"]
        if not p.endswith("SJ00"):
            continue
        y = int(p[:4]) + 1
        assert y not in S, "doublon %s %d" % (t, y)
        S[y] = (r["Examenkandidaten_1"], r["Gediplomeerden_2"])
    return S
F1 = "Onderwijssoort eq 'A025284' and Geslacht eq 'T001038' and Regiokenmerken eq 'NL01   '"
F0 = F1 + " and Migratieachtergrond eq 'T001040' and WoonregioSchoolregio eq 'A043085'"
rep = []
nouv = serie("85382NED", F1)
vieux = serie("80119ned", F0)
rep.append("85382NED : %d annees (%s-%s) ; 80119ned : %d annees (%s-%s)" % (
    len(nouv), min(nouv), max(nouv), len(vieux), min(vieux), max(vieux)))
rep.append("Ecart E1 sur les annees communes (85382NED - 80119ned, en points) :")
for y in sorted(set(nouv) & set(vieux)):
    a, b = nouv[y], vieux[y]
    if None in a + b:
        rep.append("  %d valeur manquante" % y)
        continue
    rep.append("  %d E1 %.3f vs %.3f  candidats %d vs %d" % (y, 100 * a[1] / a[0], 100 * b[1] / b[0], a[0], b[0]))
rem = {2020: "examens centraux annules, diplome sur evaluation interne", 2021: "regime d'examen amenage"}
dfn = {"E1": "Gediplomeerden / Examenkandidaten, Vwo, total, Nederland (CBS)",
       "E3": "Examenkandidaten, Vwo, total, Nederland (CBS)"}
rows = []
for y in range(2010, 2026):
    if y in nouv:
        s, t = nouv[y], "85382NED"
    elif y in vieux:
        s, t = vieux[y], "80119ned"
    else:
        rep.append("%d absent des deux tables" % y)
        continue
    if None in s:
        rep.append("%d valeur manquante dans %s" % (y, t))
        continue
    for ind, v in (("E1", round(100 * s[1] / s[0], 4)), ("E3", s[0])):
        rows.append(["NL", y, ind, v, dfn[ind], "CBS StatLine " + t, rem.get(y, "")])
out = "data/evidence_exams_international.csv"
old = []
if os.path.exists(out):
    old = [r for r in csv.reader(open(out, encoding="utf-8"))][1:]
    old = [r for r in old if r[0] != "NL"]
w = csv.writer(open(out, "w", newline="", encoding="utf-8"))
w.writerow(["pays", "annee", "indicateur", "valeur", "definition", "source", "remarque"])
w.writerows(old + rows)
open("data/processed/exams_nl_report.txt", "w").write("\n".join(rep) + "\n")
print("\n".join(rep))
print("lignes ecrites : %d (NL), conservees : %d" % (len(rows), len(old)))
