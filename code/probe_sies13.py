"""Sonde 13 : mise en page des Notes Flash SIES anciennes (cohortes 2012, 2013, 2014, 2015). Sans reseau.
Sortie : data/processed/probe_sies13.txt"""
import re
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
W = {"2017-18": (100, 160), "2019-26": (70, 125), "2020-22": (80, 140)}
out = []
for k in ("2017-18", "2018-21", "2019-26", "2020-22"):
    p = "data/raw/exams/sies/nf_%s.pdf" % k
    d = fz.open(p)
    L = [x.replace("\xa0", " ").strip() for pg in d for x in pg.get_text().split("\n") if x.strip()]
    out.append("== %s : %d pages, %d lignes, %d octets" % (k, len(d), len(L), len(open(p, "rb").read())))
    out.append("  debut : %s" % " | ".join(L[:4])[:150])
    out.append("  lignes avec 'Mention' : %s" % [(i, x[:40]) for i, x in enumerate(L) if "Mention" in x][:4])
    out.append("  cohorte : %s" % re.findall(r"bacheliers (20\d\d) inscrits", " ".join(L))[:3])
    if k in W:
        s = " | ".join(L[W[k][0]:W[k][1]])
        out += ["  " + s[i:i + 150] for i in range(0, len(s), 150)]
open("data/processed/probe_sies13.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
