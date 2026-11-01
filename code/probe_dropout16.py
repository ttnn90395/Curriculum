"""Sonde 16 (Amendement 24) : sources d'abandon / non-continuation en premiere annee, DE UK NL ES PL.
Telecharge des pages et fichiers candidats, imprime taille, type, liens de donnees et contextes de mots-cles.
Aucune valeur n'est retenue ici. Sorties : data/raw/exams/dropout/*, data/processed/probe_dropout16.txt"""
import os, re, sys, urllib.request, urllib.parse
try:
    import pymupdf as fz
except ImportError:
    import fitz as fz
D = "data/raw/exams/dropout"
os.makedirs(D, exist_ok=True)
U = [
 ("UK", "https://www.hesa.ac.uk/pis/noncon"),
 ("UK", "https://www.hesa.ac.uk/node/139571"),
 ("UK", "https://www.hesa.ac.uk/node/140010"),
 ("DE", "https://www.dzhw.eu/services/material/pressemitteilungen/2022_08_17_pm_dzhw_abbruch.pdf"),
 ("DE", "https://guse.dzhw.eu/portal/de/Tabelle-2.5.90.pdf"),
 ("NL", "https://www.cbs.nl/-/media/_excel/2021/39/studieuitval-na-eerste-jaar-mbo-hbo-wo.xlsx"),
 ("NL", "https://www.vereniginghogescholen.nl/system/knowledge_base/attachments/files/000/001/200/original/factsheet_studievoortgang_2020-2021_v2.pdf"),
 ("NL", "https://vereniginghogescholen.nl/system/knowledge_base/attachments/files/000/001/402/original/factsheet_studievoortgang_2023-2024_v20240604_final.pdf"),
 ("NL", "https://duo.nl/open_onderwijsdata/images/trendrapport-ho.pdf"),
 ("ES", "https://www.ciencia.gob.es/Noticias/2022/Marzo/ministerio-universidades-presenta-informe-sobre-el-abandono-de-los-estudios-universitarios-y-medidas-para-reducirlo.html"),
 ("ES", "https://www.ciencia.gob.es/gl/Noticias/2024/Noviembre/estadisticas-universidades-rendimiento.html"),
 ("PL", "https://ela.nauka.gov.pl/"),
]
KW = re.compile(r"non-?continuation|not continuing|Studienabbruch|abandon|uitval|drop-?out|rendement|porzucen|rezygnac|resygnac|tasa de abandono", re.I)
out = []
def pr(s=""):
    print(s); out.append(s)
for pays, u in U:
    nom = re.sub(r"[^A-Za-z0-9._-]", "_", u.split("//")[1])[-90:]
    p = os.path.join(D, pays + "_" + nom)
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=60)
        b = r.read(); ct = r.headers.get("Content-Type", "")
        open(p, "wb").write(b)
    except Exception as e:
        pr("== %s %s\n   ECHEC : %s" % (pays, u, str(e)[:150])); continue
    pr("== %s %s\n   %d octets ; %s" % (pays, u, len(b), ct))
    txt, links = "", []
    if b[:4] == b"%PDF":
        txt = " ".join(x for pg in fz.open(p) for x in pg.get_text().split())
    elif b[:2] == b"PK":
        pr("   fichier xlsx/zip : a lire a part (feuilles non listees ici)")
    else:
        h = b.decode("utf-8", "ignore")
        links = sorted(set(re.findall(r'href="([^"]+\.(?:csv|xlsx?|pdf|zip)[^"]*)"', h, re.I)))
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))
    for l in links[:12]:
        pr("   lien : " + urllib.parse.urljoin(u, l))
    n = 0
    for m in KW.finditer(txt):
        if n >= 5: break
        pr("   ..." + txt[max(0, m.start() - 90):m.end() + 130])
        n += 1
    pr("   mots-cles : %d contextes imprimes" % n)
os.makedirs("data/processed", exist_ok=True)
open("data/processed/probe_dropout16.txt", "w").write("\n".join(out) + "\n")
