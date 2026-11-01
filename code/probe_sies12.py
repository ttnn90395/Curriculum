"""Sonde 12 : localisation, dans les Notes Flash SIES deja telechargees, des lignes par serie de bac
(general, techno, pro, ensemble) et de la phrase sur le taux de passage L1-L2. Sans reseau.
Sortie : data/processed/probe_sies12.txt"""
import glob, re
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
K = re.compile(r"^(Bac(calaur.at)? )?(g.n.ral|technologique|professionnel)\b|^Ensemble|taux de passage", re.I)
out = []
for p in sorted(glob.glob("data/raw/exams/sies/nf_*.pdf")):
    out.append("== " + p.split("/")[-1])
    L = [x.replace("\xa0", " ").strip() for pg in fz.open(p) for x in pg.get_text().split("\n") if x.strip()]
    n = 0
    for i, x in enumerate(L):
        if K.search(x) and n < 14:
            out.append("  [%d] %s" % (i, " | ".join(L[i:i + 5])[:160]))
            n += 1
open("data/processed/probe_sies12.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
