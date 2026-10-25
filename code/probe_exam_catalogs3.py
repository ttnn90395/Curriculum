"""Sonde 3 : codes filieres CBS (NL) et liens de fichiers des pages FI/PL/ES/DEPP.
Sortie : data/processed/probe_exam_catalogs3.txt"""
import gzip, re, urllib.request, urllib.parse
UA = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60)
    b = r.read()
    if b[:2] == b"\x1f\x8b":
        b = gzip.decompress(b)
    return b.decode("utf-8", "replace")
out = []
CB = "https://opendata.cbs.nl/"
for t in ("80119ned", "85382NED"):
    for f in (CB + "ODataApi/odata/%s/OnderwijssoortCodes?$format=json" % t,
              CB + "ODataFeed/odata/%s/Onderwijssoort?$format=json" % t,
              CB + "ODataApi/OData/%s/Onderwijssoort?$format=json" % t):
        out.append("== NL %s" % f[-70:])
        try:
            j = get(f)
            out.append("  OK %d car. : %s" % (len(j), j[:900].replace("\n", " ")))
            break
        except Exception as e:
            out.append("  ERREUR %s" % str(e)[:80])
P = [("FI", "https://www.ylioppilastutkinto.fi/fi/tietopalvelut/tilastot"),
     ("FI2", "https://www.ylioppilastutkinto.fi/fi/tietopalvelut/tilastot/painettu-tilastojulkaisu"),
     ("PL", "https://cke.gov.pl/egzamin-maturalny/egzamin-maturalny-w-formule-2023/wyniki-sprawozdania/"),
     ("PL2", "https://cke.gov.pl/egzamin-maturalny/egzamin-maturalny-w-formule-2015/wyniki/"),
     ("ES", "https://www.ciencia.gob.es/Ministerio/Estadisticas/SIIU/PAU.html"),
     ("DEPP2019", "https://www.education.gouv.fr/depp/resultats-definitifs-de-la-session-2019-du-baccalaureat-451650"),
     ("IT", "https://dati.istruzione.it/opendata/esploraidati")]
H = re.compile(r'href="([^"#]+)"', re.I)
K = re.compile(r"xls|csv|zip|pdf|download|media|file|fichier|tiedosto|attachment|dokument|statist|tilast|wynik", re.I)
for nom, u in P:
    out.append("== liens %s : %s" % (nom, u[-80:]))
    try:
        L = sorted({urllib.parse.urljoin(u, x) for x in H.findall(get(u)) if K.search(x)})
        out.append("  %d liens" % len(L))
        out += ["  " + x[:160] for x in L[:60]]
    except Exception as e:
        out.append("  ERREUR %s" % str(e)[:90])
open("data/processed/probe_exam_catalogs3.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
