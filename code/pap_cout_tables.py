import sys, re, os
try:
    import pymupdf as fitz
except ImportError:
    import fitz
num = re.compile(r"^\d{1,3}(?: \d{3})*$")
def tables(lines):
    """Rend [[categorie, [valeurs]]] pour le bloc COUTS ENTREE-SORTIE d'une page (lignes de texte)."""
    try:
        i = next(k for k, l in enumerate(lines) if re.search(r"CO[UÛ]TS ENTR[ÉE]E", l, re.I))
    except StopIteration:
        return None
    out, label = [], None
    for l in (re.sub(r"\s", " ", x) for x in lines[i + 1:]):
        if re.search(r"MESURES CAT[ÉE]GORIELLES", l, re.I):
            break
        if num.match(l):
            if label is not None:
                out[-1][1].append(int(l.replace(" ", "")))
        elif re.match(r"(Cat[ée]gorie d|Co[uû]t |dont r[ée]mun)", l, re.I):
            continue
        else:
            label = l; out.append([l, []])
    return out
for path in sys.argv[1:]:
    if not os.path.exists(path):
        print(f"== {path}: absent"); continue
    with open(path, "rb") as fh:
        if fh.read(5) != b"%PDF-":
            print(f"== {path}: PAS un PDF"); continue
    doc = fitz.open(path)
    print(f"== {path}: {len(doc)} pages; {' '.join(doc[0].get_text().split())[:110]}")
    for pno, page in enumerate(doc, 1):
        lines = [l.strip() for l in page.get_text().splitlines() if l.strip()]
        t = tables(lines)
        if t:
            head = " ".join(lines)
            prog = re.search(r"programme\s*(?:n°\s*)?(\d{3})", head, re.I)
            plf = re.search(r"PLF ?20\d\d", head)
            print(f"-- p.{pno} programme {prog.group(1) if prog else '?'} {plf.group(0) if plf else ''} | {head[:110]}")
            for lab, vals in t:
                print(f"   {lab}: {vals}")
