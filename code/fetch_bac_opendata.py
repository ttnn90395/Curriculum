"""Telecharge les series ouvertes du baccalaureat (DEPP, data.education.gouv.fr) selon l'Amendement 16, sans autre transformation que des taux.
Sorties : data/evidence_bac_reussite_ensemble.csv, data/evidence_bac_mentions_academie.csv, data/processed/bac_series_report.txt"""
import csv, gzip, json, urllib.error, urllib.parse, urllib.request
B = "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/"
def get(u):
    try:
        raw = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}), timeout=120).read()
    except urllib.error.HTTPError as e:
        raise SystemExit("HTTP %s : %s" % (e.code, e.read()[:300]))
    if raw[:2] == b"\x1f\x8b": raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))
def q(ds, **p): return get(B + ds + "/records?" + urllib.parse.urlencode(p))["results"]
out = []
# (a) reussite par voie, ligne Ensemble
a = q("fr-en-reussite-au-baccalaureat-age", where='age="Ensemble"', order_by="annee", limit=100,
      select="annee,pourcentage_d_admis_au_baccalaureat_general,pourcentage_d_admis_au_baccalaureat_technologique,pourcentage_d_admis_au_baccalaureat_professionnel,pourcentage_d_admis_au_baccalaureat,nombre_d_admis_au_baccalaureat")
with open("data/evidence_bac_reussite_ensemble.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["annee", "taux_general", "taux_techno", "taux_pro", "taux_ensemble", "admis_ensemble"])
    for r in a:
        w.writerow([str(r["annee"])[:4], r["pourcentage_d_admis_au_baccalaureat_general"], r["pourcentage_d_admis_au_baccalaureat_technologique"],
                    r["pourcentage_d_admis_au_baccalaureat_professionnel"], r["pourcentage_d_admis_au_baccalaureat"], r["nombre_d_admis_au_baccalaureat"]])
out.append("N1 : taux de reussite (%) par annee : annee ; general ; techno ; pro ; ensemble")
for r in a: out.append("%s ; %s ; %s ; %s ; %s" % (str(r["annee"])[:4], r["pourcentage_d_admis_au_baccalaureat_general"], r["pourcentage_d_admis_au_baccalaureat_technologique"], r["pourcentage_d_admis_au_baccalaureat_professionnel"], r["pourcentage_d_admis_au_baccalaureat"]))
# (b) mentions par session et voie
sel = ("session,voie,sum(nombre_d_inscrits) as inscrits,sum(nombre_de_presents) as presents,sum(nombre_d_admis_totaux) as admis,"
       "sum(nombre_d_admis_avec_mention_tb_avec_les_felicitations_du_jury) as tbf,sum(nombre_d_admis_avec_mention_tb_sans_les_felicitations_du_jury) as tb,"
       "sum(nombre_d_admis_avec_mention_b) as b,sum(nombre_d_admis_avec_mention_ab) as ab")
b = q("fr-en-baccalaureat-par-academie", select=sel, group_by="session,voie", order_by="session,voie", limit=100)
with open("data/evidence_bac_mentions_academie.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["session", "voie", "inscrits", "presents", "admis", "tb_felicitations", "tb", "b", "ab"])
    for r in b: w.writerow([str(r["session"])[:4], r["voie"], r["inscrits"], r["presents"], r["admis"], r["tbf"], r["tb"], r["b"], r["ab"]])
out.append(""); out.append("N2 : session ; voie ; admis/presents (%) ; mentions/admis (%) ; TB(avec+sans felicitations)/admis (%)")
for r in b:
    adm, pre = r["admis"] or 0, r["presents"] or 0
    men = (r["tbf"] or 0) + (r["tb"] or 0) + (r["b"] or 0) + (r["ab"] or 0)
    out.append("%s ; %s ; %.1f ; %.1f ; %.1f" % (str(r["session"])[:4], r["voie"], 100 * adm / pre if pre else float("nan"), 100 * men / adm if adm else float("nan"), 100 * ((r["tbf"] or 0) + (r["tb"] or 0)) / adm if adm else float("nan")))
open("data/processed/bac_series_report.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
