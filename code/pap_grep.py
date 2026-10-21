import sys, re, os
try:
    import pymupdf as fitz
except ImportError:
    import fitz
pat = re.compile(r"co[uû]ts? (moyens?|d.entr[ée]e|de sortie)|hors CAS|taux de contribution|taux de cotisation", re.I)
for path in sys.argv[1:]:
    if not os.path.exists(path):
        print(f"== {path}: fichier absent; ignore"); continue
    with open(path, "rb") as fh:
        if fh.read(5) != b"%PDF-":
            print(f"== {path}: PAS un PDF (page de refus ou de redirection probable); ignore"); continue
    doc = fitz.open(path)
    first = " ".join(doc[0].get_text().split())[:160]
    print(f"== {path}: {len(doc)} pages; debut: {first}")
    hits = []
    for i, page in enumerate(doc, 1):
        lines = [l.strip() for l in page.get_text().splitlines() if l.strip()]
        for j, l in enumerate(lines):
            if pat.search(l):
                hits.append(f"p.{i}: " + " | ".join(lines[j:j + 3]))
    out = "data/processed/pap_grep_" + os.path.splitext(os.path.basename(path))[0] + ".txt"
    open(out, "w").write("\n".join(hits))
    print(f"   {len(hits)} lignes -> {out}")
    print("\n".join(hits[:60]))
