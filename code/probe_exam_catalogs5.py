"""Sonde 5 : tableau 1 des PDF polonais ; liens PL 2015/2021 ; tables PxWeb espagnoles ; catalogue italien.
Sortie : data/processed/probe_exam_catalogs5.txt"""
import gzip, os, re, urllib.parse, urllib.request
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
UA = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
def get(u):
    u = urllib.parse.quote(u, safe=":/%?&=@")
    b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90).read()
    return (gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b).decode("utf-8", "replace")
out = []
for y in (2016, 2019, 2022, 2025):
    out.append("== PL %d, apres 'Tabela 1'" % y)
    d = fz.open("data/raw/exams/pl/pl_%d.pdf" % y)
    L = [x.strip() for pg in d for x in pg.get_text().split("\n") if x.strip()]
    i = next((k for k, x in enumerate(L) if x.startswith("Tabela 1")), None)
    if i is None:
        out.append("  Tabela 1 introuvable")
        continue
    out += ["  " + x[:120] for x in L[i:i + 24]]
H = re.compile(r'href="([^"#]+)"', re.I)
PL2 = "https://cke.gov.pl/egzamin-maturalny/egzamin-maturalny-w-formule-2015/wyniki/"
PL3 = "https://cke.gov.pl/egzamin-maturalny/egzamin-maturalny-w-formule-2023/wyniki-sprawozdania/"
for nom, u, pat in (("PL liste", PL2, r"2015|2021|2014|2013"),
                    ("PL 2021", PL2 + "sprawozdanie-z-egzaminu-maturalnego-2021/", r"pdf"),
                    ("PL 2026", PL3, r"2026")):
    out.append("== %s" % nom)
    try:
        L = sorted({urllib.parse.urljoin(u, x) for x in H.findall(get(u)) if re.search(pat, x, re.I)})
        out += ["  " + x[-130:] for x in L[:25]]
    except Exception as e:
        out.append("  ERREUR %s" % str(e)[:90])
ES = "https://estadisticas.ciencia.gob.es/dynPx/inebase/index.htm"
ES += "?type=pcaxis&path=/Universitaria/PAU/PAU/&file=pcaxis"
out.append("== ES tables (hors _ca)")
try:
    N = sorted(set(re.findall(r"file=([A-Za-z0-9_]+)\.px", get(ES))))
    out += ["  " + n for n in N if not n.endswith("_ca")]
except Exception as e:
    out.append("  ERREUR %s" % str(e)[:90])
IT = "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/"
out.append("== IT catalogue")
try:
    P = r"area|csv|esit|esam"
    L = sorted({urllib.parse.urljoin(IT, x) for x in H.findall(get(IT)) if re.search(P, x, re.I)})
    out += ["  " + x[-130:] for x in L[:40]]
except Exception as e:
    out.append("  ERREUR %s" % str(e)[:90])
open("data/processed/probe_exam_catalogs5.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
