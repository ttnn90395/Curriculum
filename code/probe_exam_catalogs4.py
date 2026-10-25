"""Sonde 4 : telecharge FI et PL, imprime leur contenu utile ; codes CBS (NL) ; tables PxWeb (ES) ; catalogue IT.
Sortie : data/processed/probe_exam_catalogs4.txt ; fichiers dans data/raw/exams/fi et /pl"""
import gzip, json, os, re, urllib.request, urllib.parse
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
UA = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
def getb(u):
    u = urllib.parse.quote(u, safe=":/%?&=@")
    b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90).read()
    return gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b
def get(u):
    return getb(u).decode("utf-8", "replace")
out = []
D = "data/raw/exams/"
FS = "https://tiedostot.ylioppilastutkinto.fi/ext/stat/"
FI = ["FB2026ST2001.pdf", "FS2026A2008T4003.pdf", "FS2026A2012T2011.pdf", "FS2026A2015T3010.pdf",
      "FS2026A2017T2010.pdf", "FS2026A2017T4020.csv", "FS2026A2017T4020.pdf", "FS2026A2017T4021.pdf",
      "FS2026A2022T2041.pdf", "FS2026A2024T4002.pdf", "FT2026KT3002.pdf", "FT2026KT3003.pdf",
      "FT2026KT3020.pdf", "FT2026KT3021.pdf"]
CK = "http://cke.gov.pl/images/_EGZAMIN_MATURALNY_OD_2015/Informacje_o_wynikach/"
C3 = "http://cke.gov.pl/images/_EGZAMIN_MATURALNY_OD_2023/Informacje_o_wynikach/"
PL = {2016: CK + "2016/20160912 Informacja o wynikach matury M Cz S.pdf",
      2017: CK + "2017/20170911 Informacja o wynikach matury M Cz S.pdf",
      2018: CK + "2018/20180907 Informacja o wynikach matury M Cz S.pdf",
      2019: CK + "2019/Informacja o wynikach matury_maj_czerwiec_sierpień.pdf",
      2020: CK + "2020/20200930 Informacja o wynikach egzaminu maturalnego 2020 COMPL.pdf",
      2022: CK + "2022/20220909 Informacja o wynikach egzaminu maturalnego 2022 COMPL.pdf",
      2023: "https://www.cke.gov.pl/images/_EGZAMIN_MATURALNY_OD_2015/Informacje_o_wynikach/2023/"
            "Informacja o wynikach egzaminu maturalnego 2023.pdf",
      2024: C3 + "2024/20240910 Informacja o wynikach egzaminu maturalnego 2024.pdf",
      2025: C3 + "2025/20250910 Informacja o wynikach egzaminu maturalnego 2025.pdf",
      2026: C3 + "komunikaty/2026/20260911 Informacja o wynikach egzaminu maturalnego 2026 M Cz S.pdf"}
def sauve(rep, nom, u):
    os.makedirs(D + rep, exist_ok=True)
    p = D + rep + "/" + nom
    if not os.path.exists(p):
        open(p, "wb").write(getb(u))
    return p
def texte(p, n):
    d = fz.open(p)
    return [x.strip() for i in range(min(n, len(d))) for x in d[i].get_text().split("\n") if x.strip()]
for nom in FI:
    out.append("== FI %s" % nom)
    try:
        p = sauve("fi", nom, FS + nom)
        if nom.endswith(".csv"):
            out += ["  " + l[:150] for l in open(p, encoding="utf-8", errors="replace").read().split("\n")[:12]]
        else:
            out += ["  " + l[:110] for l in texte(p, 1)[:9]]
    except Exception as e:
        out.append("  ERREUR %s" % str(e)[:80])
K = re.compile(r"zdawal|zdal|przyst|zdaj|odsetek", re.I)
for y, u in PL.items():
    out.append("== PL %d" % y)
    try:
        p = sauve("pl", "pl_%d.pdf" % y, u)
        L = [l for l in texte(p, 4) if K.search(l)]
        out += ["  " + l[:150] for l in L[:7]]
    except Exception as e:
        out.append("  ERREUR %s" % str(e)[:80])
CB = "https://opendata.cbs.nl/ODataFeed/odata/"
for t, dims in (("80119ned", ("Geslacht", "Migratieachtergrond", "WoonregioSchoolregio", "Regiokenmerken")),
                ("85382NED", ("Geslacht", "Regiokenmerken"))):
    out.append("== NL %s" % t)
    try:
        for d in ("Onderwijssoort",) + dims:
            v = json.loads(get(CB + "%s/%s?$format=json" % (t, d)))["value"]
            if d == "Onderwijssoort":
                tt = lambda x: x["Title"].lower()
                v = [x for x in v if "vwo" in tt(x) or "totaal" in tt(x)]
            out.append("  %s : %s" % (d, [(x["Key"], x["Title"][:30]) for x in v[:12]]))
        v = json.loads(get(CB + "%s/Perioden?$format=json" % t))["value"]
        out.append("  Perioden %d : %s ... %s" % (len(v), v[0]["Key"], v[-1]["Key"]))
    except Exception as e:
        out.append("  ERREUR %s" % str(e)[:90])
H = re.compile(r'href="([^"#]+)"', re.I)
ESU = "https://estadisticas.ciencia.gob.es/dynPx/inebase/index.htm"
ESU += "?type=pcaxis&path=/Universitaria/PAU/PAU/&file=pcaxis"
ITU = "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/"
for nom, u, pat in (("ES px", ESU, r"px|file|path"), ("IT cat", ITU, r"area|csv|esit|esam")):
    out.append("== %s : %s" % (nom, u[-70:]))
    try:
        L = sorted({urllib.parse.urljoin(u, x) for x in H.findall(get(u)) if re.search(pat, x, re.I)})
        out.append("  %d liens" % len(L))
        out += ["  " + x[:170] for x in L[:40]]
    except Exception as e:
        out.append("  ERREUR %s" % str(e)[:90])
open("data/processed/probe_exam_catalogs4.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
