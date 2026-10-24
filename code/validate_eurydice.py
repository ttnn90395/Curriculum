"""Validation externe du modele de cout (mode oecd) par Eurydice 2024/25 et Eurostat : Amendement 13 et ses precisions.
Entrees : data/evidence_eurydice_annual.csv, data/evidence_eurostat_expenditure.csv, data/processed/cross_country_net_cost.csv,
          curriculum France (argument 1, defaut data/instruction_hours_fr_secondary.csv ; colonnes level,grade,subject,weekly_hours).
Sortie : data/processed/validate_eurydice.txt. Aucun parametre ajuste ; seuils de l'Amendement 13."""
import csv, sys, statistics as st
ISO3 = dict(AT="AUT", AL="ALB", BA="BIH", BE="BEL", BG="BGR", CH="CHE", CY="CYP", CZ="CZE", DE="DEU", DK="DNK", EE="EST", EL="GRC",
            ES="ESP", FI="FIN", FR="FRA", HR="HRV", HU="HUN", IE="IRL", IS="ISL", IT="ITA", LI="LIE", LT="LTU", LU="LUX", LV="LVA",
            ME="MNE", MT="MLT", NL="NLD", NO="NOR", PL="POL", PT="PRT", RO="ROU", RS="SRB", SE="SWE", SI="SVN", SK="SVK", TR="TUR")
out = []
def say(s=""):
    out.append(s); print(s)
def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return r
def pearson(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return num / (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
def num(x):
    try: return float(x)
    except: return None
eur = {r["system"]: r for r in csv.DictReader(open("data/evidence_eurydice_annual.csv"))}
exp = {}
for r in csv.DictReader(open("data/evidence_eurostat_expenditure.csv")):
    v = num(r["pps_per_pupil"])
    if v is None: continue
    cur = exp.setdefault((r["geo"], r["isced11"]), (r["time"], v))
    if r["time"] > cur[0]: exp[(r["geo"], r["isced11"])] = (r["time"], v)
net = {r["pays"]: r for r in csv.DictReader(open("data/processed/cross_country_net_cost.csv"))}
# test 1
say("== Test 1 : France, heures annuelles par niveau (x 36 semaines) contre Eurydice ==")
path = sys.argv[1] if len(sys.argv) > 1 else "data/instruction_hours_fr_secondary.csv"
w = {}
for r in csv.DictReader(open(path)):
    h = num(r["weekly_hours"])
    if h is None: continue
    w[(r["level"], r["grade"])] = w.get((r["level"], r["grade"]), 0) + h
say("niveaux lus dans %s : %s" % (path, sorted(w)))
ref = {"college": ("CITE 24", 973.0), "lycee": ("CITE 34 (2de)", 1008.0), "primaire": ("CITE 1", 864.0)}
for key, (lab, e) in ref.items():
    if key == "lycee":
        v = [h for (lv, g), h in w.items() if "lyc" in lv.lower() and g.lower().startswith("2")]
    elif key == "college":
        v = [h for (lv, g), h in w.items() if "coll" in lv.lower()]
    else:
        v = [h for (lv, g), h in w.items() if "lyc" not in lv.lower() and "coll" not in lv.lower()]
    if not v:
        say("%-9s %-14s non realise (niveau absent du fichier)" % (key, lab)); continue
    m = 36 * sum(v) / len(v); d = m / e - 1
    say("%-9s %-14s modele %.0f h ; Eurydice %.0f h ; ecart %+.1f %% -> %s" % (key, lab, m, e, 100 * d, "OK" if abs(d) <= 0.10 else "ECHEC"))
# tests 2 et 3
rows, excl = [], []
for s, r in eur.items():
    if r["multitrack"] == "1" or " " in s:
        excl.append((s, "multi-filieres ou communautes")); continue
    iso = ISO3.get(s)
    if iso not in net: excl.append((s, "absent de cross_country_net_cost")); continue
    if (s, "ED1") not in exp or (s, "ED24") not in exp: excl.append((s, "absent d'Eurostat")); continue
    a1, h1, a24, h24 = int(r["years_isced1"]), float(r["hours_per_year_isced1"]), int(r["years_isced24"]), float(r["hours_per_year_isced24"])
    H = (a1 * h1 + a24 * h24) / (a1 + a24)
    E = (a1 * exp[(s, "ED1")][1] + a24 * exp[(s, "ED24")][1]) / (a1 + a24)
    n = net[iso]
    P = H * float(n["salaire_ppp"]) * float(n["facteur_employeur"]) / (float(n["heures_an"]) * float(n["taille_classe"]))
    rows.append((s, H, P, E, exp[(s, "ED1")][0] + "/" + exp[(s, "ED24")][0]))
say(); say("== Tests 2 et 3 : n = %d systemes ==" % len(rows))
say("exclus : " + "; ".join("%s (%s)" % x for x in excl))
if len(rows) >= 3:
    P = [x[2] for x in rows]; E = [x[3] for x in rows]
    rho = pearson(rank(P), rank(E))
    say("Test 2 : Spearman(predit, observe) = %.3f (seuil 0.6) -> %s" % (rho, "OK" if rho >= 0.6 else "ECHEC"))
    sh = [p / e for p, e in zip(P, E)]
    med, cv = st.median(sh), st.pstdev(sh) / st.mean(sh)
    say("Test 3 : part predite mediane = %.3f (intervalle [0.35,0.85]) -> %s ; CV = %.3f (seuil 0.25) -> %s" % (med, "OK" if 0.35 <= med <= 0.85 else "ECHEC", cv, "OK" if cv < 0.25 else "ECHEC"))
    rp, re = rank(P), rank(E)
    say(); say("systeme ; H (h/an) ; predit ; observe (PPS) ; part ; rang predit ; rang observe ; annees ED1/ED24")
    for x, a, b in sorted(zip(rows, rp, re), key=lambda t: -abs(t[1] - t[2])):
        say("%s ; %.0f ; %.0f ; %.0f ; %.2f ; %.1f ; %.1f ; %s" % (x[0], x[1], x[2], x[3], x[2] / x[3], a, b, x[4]))
else:
    say("n < 3 : tests 2 et 3 non realises")
open("data/processed/validate_eurydice.txt", "w").write("\n".join(out) + "\n")
