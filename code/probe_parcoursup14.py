"""Sonde 14 : catalogue des jeux ouverts Parcoursup (sessions 2018-2025) et champs sur les mentions.
Sortie : data/processed/probe_parcoursup14.txt"""
import gzip, json, re, urllib.request
AG = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
U = "https://data.enseignementsup-recherche.gouv.fr/api/datasets/1.0/search/?q=parcoursup&rows=100"
r = urllib.request.urlopen(urllib.request.Request(U, headers={"User-Agent": AG, "Accept-Encoding": "identity"}), timeout=90)
b = r.read()
j = json.loads((gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b).decode("utf-8", "replace"))
K = re.compile(r"mention|_tb|acc_|fili|typ|bac|session|annee|rentree", re.I)
out = ["%d jeux" % j.get("nhits", 0)]
for d in sorted(j.get("datasets", []), key=lambda x: x["datasetid"]):
    m = d.get("metas", {})
    f = [x["name"] for x in d.get("fields", [])]
    out.append("== %s | %s | %s lignes | %d champs" % (d["datasetid"], str(m.get("title"))[:60], m.get("records_count"), len(f)))
    if "parcoursup" in d["datasetid"] and any(c in d["datasetid"] for c in ("2018", "2020", "2022", "2025")) or d["datasetid"] == "fr-esr-parcoursup":
        out.append("   champs : %s" % ", ".join(x for x in f if K.search(x))[:600])
open("data/processed/probe_parcoursup14.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
