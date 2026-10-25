"""Sonde 6 : archive italienne IIciclo_AAAA.pdf (edscuola) et tables PxWeb espagnoles.
Sortie : data/processed/probe_exam_catalogs6.txt ; fichiers dans data/raw/exams/it"""
import gzip, os, re, urllib.error, urllib.parse, urllib.request
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
UA = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
def getb(u):
    u = urllib.parse.quote(u, safe=":/%?&=@")
    b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90).read()
    return gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b
out = []
os.makedirs("data/raw/exams/it", exist_ok=True)
EDS = "https://www.edscuola.it/archivio/statistiche/IIciclo_%s.pdf"
for s in range(2005, 2022):
    c = "%02d%02d" % (s % 100, (s + 1) % 100)
    try:
        b = getb(EDS % c)
        p = "data/raw/exams/it/IIciclo_%s.pdf" % c
        open(p, "wb").write(b)
        L = [x.strip() for pg in fz.open(p) for x in pg.get_text().split("\n") if x.strip()]
        k = [i for i, x in enumerate(L) if x.startswith("Italia")][:2]
        ex = [" | ".join(L[i:i + 9])[:110] for i in k]
        out.append("IT %s OK %d octets ; lignes Italia : %s" % (c, len(b), ex))
    except urllib.error.HTTPError as e:
        out.append("IT %s HTTP %s" % (c, e.code))
    except Exception as e:
        out.append("IT %s ERREUR %s" % (c, str(e)[:60]))
PX = "https://estadisticas.ciencia.gob.es/jaxiPx/Tabla.htm?path=/Universitaria/PAU/PAU/l0/&file=%s.px&L=0"
for n in ("px_pau_matric_sexo_tot", "px_pau_gen_matric_sexo_tot", "px_pau_nota_acceso_sexo_tot"):
    out.append("== ES %s" % n)
    try:
        t = getb(PX % n).decode("utf-8", "replace")
        ti = re.search(r"<title>(.*?)</title>", t, re.S)
        out.append("  titre : %s" % (ti.group(1).strip()[:150] if ti else "?"))
        mots = sorted(set(re.findall(r"(?:Aprobad|Presentad|Matricul|Apt)\w*", t)))
        out.append("  mots : %s" % mots[:12])
        P = r"csv|\.px|xls|files|bdsc|json"
        L = sorted(set(x for x in re.findall(r'href="([^"#]+)"', t) if re.search(P, x, re.I)))
        out += ["  " + urllib.parse.urljoin(PX % n, x)[:170] for x in L[:10]]
    except Exception as e:
        out.append("  ERREUR %s" % str(e)[:90])
open("data/processed/probe_exam_catalogs6.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
