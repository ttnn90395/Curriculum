"""Sonde 17 (Amendement 25) : catalogue des jeux OCDE (SDMX) et Eurostat sur achevement / abandon dans le superieur.
Imprime seulement identifiants et titres ; aucune valeur n'est lue.
Sorties : data/raw/oecd/*, data/processed/probe_oecd17.txt"""
import os, re, urllib.request
os.makedirs("data/raw/oecd", exist_ok=True)
KW = re.compile(r"complet|graduat|drop|attrit|retention|persist|entrant|tertiary|bachelor|enrol", re.I)
SRC = [
 ("OECD", "https://sdmx.oecd.org/public/rest/dataflow/all?references=none&detail=allstubs", "data/raw/oecd/oecd_dataflows.xml"),
 ("EUROSTAT", "https://ec.europa.eu/eurostat/api/dissemination/catalogue/toc/txt?lang=en", "data/raw/oecd/eurostat_toc.txt"),
]
out = []
def pr(s):
    print(s); out.append(s)
for nom, u, p in SRC:
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"}), timeout=120)
        b = r.read(); open(p, "wb").write(b)
    except Exception as e:
        pr("== %s ECHEC : %s" % (nom, str(e)[:160])); continue
    t = b.decode("utf-8", "ignore")
    pr("== %s %d octets" % (nom, len(b)))
    if nom == "OECD":
        L = re.findall(r'<structure:Dataflow[^>]*\bid="([^"]+)"[^>]*agencyID="([^"]+)".*?<common:Name xml:lang="en">([^<]+)', t, re.S)
        pr("   %d jeux au total" % len(L))
        for i, a, n in L:
            if re.search(r"complet|graduat|drop|attrit|retention|persist|entrant|new entr|enrolment", n, re.I) and re.search(r"educ|tertiary|UOE|student|graduat|enrol", n + a, re.I):
                pr("   %s | %s | %s" % (a, i, n[:110]))
    else:
        n = 0
        for ln in t.splitlines():
            if re.search(r"complet|drop|attrit|retention|persist|entrant|new entrant", ln, re.I) and re.search(r"tertiary|educ|student|bachelor", ln, re.I):
                pr("   " + ln[:230]); n += 1
                if n >= 40: break
open("data/processed/probe_oecd17.txt", "w").write("\n".join(out) + "\n")
