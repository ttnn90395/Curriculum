"""
Projet Education -- Telechargement des donnees
==================================================
STATUT: NON TESTE dans le sandbox de developpement -- aucun acces
reseau vers worldbank.org, eurostat, oecd.org ou timss2023.org
n'est disponible depuis cet environnement (liste blanche limitee
a pypi/npm/github). A executer et deboguer sur une machine avec
acces internet normal.

Deux categories, traitees differemment:
  1. APIs publiques avec endpoint stable -> telechargement automatise
     (World Bank, Eurostat). Code fourni, a tester.
  2. Portails necessitant navigation/acceptation de conditions
     d'usage (TIMSS, PISA, PIAAC, TALIS, DEPP) -> pas d'API simple
     connue ; le script VERIFIE la presence des fichiers attendus
     et affiche les instructions de telechargement manuel sinon,
     plutot que de pretendre automatiser ce qui ne l'est pas.

Usage:
    python download_data.py --all
    python download_data.py --worldbank --eurostat
    python download_data.py --check   # verifie ce qui manque
"""

import argparse
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import json

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (research script, projet-education)"


def _fetch(url: str, dest: Path, timeout: int = 30) -> bool:
    """Telecharge un fichier avec gestion d'erreur explicite --
    ne masque jamais un echec sous un succes silencieux."""
    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=timeout) as response:
            dest.write_bytes(response.read())
        print(f"  OK  {dest.name} ({dest.stat().st_size:,} octets)")
        return True
    except (URLError, HTTPError) as e:
        print(f"  ECHEC  {url} -- {e}")
        return False


# =================================================================
# 1. World Bank API -- automatisable
# =================================================================
# Documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
# Format: api.worldbank.org/v2/country/{pays}/indicator/{code}?format=json

WORLDBANK_INDICATORS = {
    "unemployment_total": "SL.UEM.TOTL.ZS",
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "education_spend_pct_gdp": "SE.XPD.TOTL.GD.ZS",
}

def download_worldbank(countries: str = "all", start_year: int = 2000, end_year: int = 2025):
    """countries: code ISO3 separes par ';', ou 'all'."""
    print("\n=== World Bank API ===")
    for name, code in WORLDBANK_INDICATORS.items():
        url = (
            f"https://api.worldbank.org/v2/country/{countries}/indicator/{code}"
            f"?date={start_year}:{end_year}&format=json&per_page=20000"
        )
        dest = DATA_DIR / f"worldbank_{name}.json"
        _fetch(url, dest)


# =================================================================
# 2. Eurostat API -- automatisable
# =================================================================
# Documentation: https://ec.europa.eu/eurostat/web/main/data/web-services
# Dataset cible: isoc_sks_itspt (specialistes TIC en emploi)

EUROSTAT_DATASETS = {
    "ict_specialists": "isoc_sks_itspt",
}

def download_eurostat():
    print("\n=== Eurostat API ===")
    for name, dataset_code in EUROSTAT_DATASETS.items():
        url = (
            f"https://ec.europa.eu/eurostat/api/dissemination/"
            f"statistics/1.0/data/{dataset_code}?format=JSON&lang=FR"
        )
        dest = DATA_DIR / f"eurostat_{name}.json"
        _fetch(url, dest)


# =================================================================
# 3. TIMSS 2023 -- automatisable, URLs directes confirmees
#    (pas de connexion requise, verifie le 2026-10-04)
# =================================================================
# Source: https://timss2023.org/data/
# ATTENTION: licence IEA -- usage non commercial, educatif et de
# recherche uniquement ; citer la source (voir docstring du
# fichier timss2023.org/data pour le texte exact de citation).

TIMSS2023_BASE = "https://timss2023.org/wp-content/uploads/data/"

TIMSS2023_FILES = {
    # Fichiers LEGERS, prioritaires -- directement exploitables
    # pour le graphe de notions (Section 5, Partie 2) sans avoir
    # besoin des grosses microdonnees
    "curriculum_g4": "T23_CurriculumData_G4.xlsx",       # g_{i,n}, grade 4
    "curriculum_g8": "T23_CurriculumData_G8.xlsx",       # g_{i,n}, grade 8
    "irt_params_g4": "T23_IRTParameters_G4.xlsx",        # w_n (poids du graphe), grade 4
    "irt_params_g8": "T23_IRTParameters_G8.xlsx",        # w_n (poids du graphe), grade 8
    "codebook_g4": "T23_Codebook_G4.xlsx",
    "codebook_g8": "T23_Codebook_G8.xlsx",
    "item_info_g4": "T23_ItemInformation_G4.xlsx",
    "item_info_g8": "T23_ItemInformation_G8.xlsx",
    # Fichiers LOURDS (SPSS, ~950 Mo-1 Go chacun) -- microdonnees
    # completes, necessaires pour le modele empirique (Partie 3)
    # mais pas pour une premiere exploration du graphe
    "spss_g4": "T23_Data_SPSS_G4.zip",   # ~991 Mo
    "spss_g8": "T23_Data_SPSS_G8.zip",   # ~949 Mo
    # Variables contextuelles derivees -- peut deja contenir des
    # indices agreges utiles (p_{i,n} pre-calcule, etc.)
    "derived_context_g4": "T23_DerivedContextVariables_G4.zip",
    "derived_context_g8": "T23_DerivedContextVariables_G8.zip",
}

# CONFIRME (2026-10-06): URLs verifiees par recuperation complete des
# pages (pas juste un extrait de recherche) -- fichiers statiques
# reels pour 2015 ET 2019, comme 2023.
TIMSS_HISTORICAL = {
    2019: {
        "base": "https://timss2019.org/international-database/downloads/",
        "curriculum_g4": "T19_G4_Curriculum Data.zip",   # espace litteral confirme dans le HTML
        "curriculum_g8": "T19_G8_Curriculum Data.zip",
    },
    2015: {
        "base": "https://timssandpirls.bc.edu/timss2015/international-database/downloads/",
        "curriculum_g4": "T15_G4_CQ_Data.zip",            # pas d'espace pour 2015
        "curriculum_g8": "T15_G8_CQ_Data.zip",
    },
}

def download_timss_historical(cycles: list[int] = (2015, 2019)):
    """Curriculum Questionnaire des cycles anterieurs a 2023 --
    necessaire pour voir si le RANG de la France en couverture
    curriculaire baisse dans le temps.

    FORMAT: .zip contenant des fichiers SPSS (.sav), pas des .xlsx
    -- necessite pyreadstat (pip install pyreadstat) pour les ouvrir."""
    from urllib.parse import quote
    print("\n=== TIMSS, cycles historiques (curriculum uniquement) ===")
    for year in cycles:
        if year not in TIMSS_HISTORICAL:
            print(f"  {year}: URLs non verifiees, ignore")
            continue
        info = TIMSS_HISTORICAL[year]
        for key in ("curriculum_g4", "curriculum_g8"):
            url = info["base"] + quote(info[key])
            dest = DATA_DIR / f"timss{year}_{key}.zip"
            _fetch(url, dest, timeout=60)


def download_timss2023(include_heavy: bool = False):
    """Par defaut, telecharge seulement les fichiers legers
    (xlsx) -- curriculum, IRT, codebooks, item info. Passer
    include_heavy=True pour ajouter les microdonnees SPSS
    completes (~2 Go au total, deconseille sur connexion lente)."""
    print("\n=== TIMSS 2023 (IEA, acces direct) ===")
    for name, filename in TIMSS2023_FILES.items():
        is_heavy = filename.endswith(".zip") and "Data_SPSS" in filename
        if is_heavy and not include_heavy:
            print(f"  SKIP  {name} (lourd, utiliser --timss-heavy pour l'inclure)")
            continue
        url = TIMSS2023_BASE + filename
        dest = DATA_DIR / f"timss2023_{name}{Path(filename).suffix}"
        _fetch(url, dest, timeout=120 if is_heavy else 30)


# =================================================================
# 4. OECD SDMX API -- automatisable en principe, endpoint a
#    reconfirmer (l'API OCDE a change de structure plusieurs fois
#    ces dernieres annees -- VERIFIER l'URL avant usage)
# =================================================================
# Point d'entree documente: https://data.oecd.org/api/sdmx-json-documentation/

def download_oecd_sdmx(dataset_id: str, dest_name: str):
    print(f"\n=== OCDE SDMX: {dataset_id} ===")
    url = f"https://sdmx.oecd.org/public/rest/data/{dataset_id}/all?format=csvfile"
    dest = DATA_DIR / f"oecd_{dest_name}.csv"
    ok = _fetch(url, dest)
    if not ok:
        print(
            "  -> si echec, l'URL SDMX a probablement change. "
            "Verifier sur data.oecd.org/api ou utiliser le "
            "OECD Data Explorer (data-explorer.oecd.org) manuellement."
        )


# =================================================================
# 4. Sources necessitant telechargement manuel -- le script
#    VERIFIE et INSTRUIT, n'automatise pas ce qui ne peut pas
#    l'etre honnetement
# =================================================================

MANUAL_SOURCES = {
    "timss_advanced_2015": {
        "expected_file": "timss_advanced_2015.sav",
        "url": "https://timssandpirls.bc.edu/timss2015/international-database/",
        "instructions": "9 pays, fichiers Advanced Mathematics/Physics.",
    },
    "pisa_database": {
        "expected_file": "pisa_2000_2025.csv",
        "url": "https://www.oecd.org/en/data/datasets/pisa-datasets.html",
        "instructions": (
            "Telecharger via le PISA Data Explorer, tous cycles "
            "2000-2025, scores maths/lecture/sciences + indices "
            "DISCLIM."
        ),
    },
    "piaac_cycle1": {
        "expected_file": "piaac_cycle1.csv",
        "url": "https://www.oecd.org/en/about/programmes/piaac/piaac-data.html",
        "instructions": "Fichiers publics (PUF), tous pays disponibles.",
    },
    "piaac_cycle2": {
        "expected_file": "piaac_cycle2.csv",
        "url": "https://www.oecd.org/en/about/programmes/piaac/piaac-data.html",
        "instructions": "Verifier la participation francaise avant usage.",
    },
    "talis_2013_math_module": {
        "expected_file": "talis_2013_math.csv",
        "url": "https://www.oecd.org/en/data/datasets/talis-2013-database.html",
        "instructions": "Module Mathematiques couple PISA.",
    },
    "depp_reperes": {
        "expected_file": "depp_reperes_references.csv",
        "url": "https://www.education.gouv.fr/les-depp-9122",
        "instructions": (
            "Reperes et references statistiques -- qualification "
            "des enseignants, salaires, depenses par eleve."
        ),
    },
}

def check_manual_sources():
    print("\n=== Sources a telechargement manuel ===")
    missing = []
    for name, info in MANUAL_SOURCES.items():
        path = DATA_DIR / info["expected_file"]
        if path.exists():
            print(f"  PRESENT  {name} -> {path.name}")
        else:
            print(f"  MANQUANT  {name}")
            print(f"            URL: {info['url']}")
            print(f"            {info['instructions']}")
            missing.append(name)
    return missing


# =================================================================
# Main
# =================================================================

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Tout executer (automatisable + verification)")
    parser.add_argument("--worldbank", action="store_true")
    parser.add_argument("--eurostat", action="store_true")
    parser.add_argument("--timss", action="store_true", help="TIMSS 2023, fichiers legers (xlsx) seulement")
    parser.add_argument("--timss-heavy", action="store_true", help="TIMSS 2023, inclut les microdonnees SPSS completes (~2 Go)")
    parser.add_argument("--timss-historical", action="store_true", help="Curriculum Questionnaire 2015 et 2019 (zip SPSS/SAS) -- pour l'evolution du rang dans le temps")
    parser.add_argument("--oecd", metavar="DATASET_ID", help="Tenter un dataset OCDE par son identifiant SDMX")
    parser.add_argument("--check", action="store_true", help="Verifier seulement les sources manuelles")
    args = parser.parse_args()

    if args.check or args.all:
        missing = check_manual_sources()
        if missing:
            print(f"\n{len(missing)} source(s) manquante(s) -- telechargement manuel requis avant de lancer les diagnostics.")

    if args.worldbank or args.all:
        download_worldbank()

    if args.eurostat or args.all:
        download_eurostat()

    if args.timss or args.timss_heavy or args.all:
        download_timss2023(include_heavy=args.timss_heavy)

    if args.timss_historical or args.all:
        download_timss_historical()

    if args.oecd:
        download_oecd_sdmx(args.oecd, args.oecd.lower())

    if not any([args.all, args.worldbank, args.eurostat, args.timss, args.timss_heavy, args.timss_historical, args.oecd, args.check]):
        parser.print_help()


if __name__ == "__main__":
    main()