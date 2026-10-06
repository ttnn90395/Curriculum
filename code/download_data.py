"""
Projet Education -- Telechargement des donnees
==================================================
STATUT: URLs TIMSS verifiees par recuperation complete des pages
reelles (pas des extraits de recherche) le 2026-10-06, pour les
cycles 2023, 2019 et 2015. Script lui-meme NON TESTE en execution
dans ce sandbox (reseau restreint) -- teste par l'utilisateur sur
Codespace, --timss et --timss-historical confirmes fonctionnels.

Deux categories:
  1. APIs publiques (World Bank, Eurostat) + fichiers statiques TIMSS
     (IEA, tous cycles) -> telechargement automatise
  2. Portails necessitant navigation (PISA, PIAAC, TALIS, DEPP) ->
     pas d'API simple trouvee ; le script VERIFIE et INSTRUIT

Usage:
    python download_data.py --all                    # tout, sans les gros fichiers
    python download_data.py --timss 2023 2019 2015    # TIMSS, cycles choisis, fichiers legers
    python download_data.py --timss 2023 --timss-heavy  # + microdonnees completes
    python download_data.py --worldbank --eurostat
    python download_data.py --check                  # verifie les sources manuelles
"""

import argparse
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (research script, projet-education)"

# ATTENTION licence IEA (TIMSS, tous cycles): usage non commercial,
# educatif et de recherche uniquement ; citation requise. Voir
# https://timss2023.org/data pour le texte exact.


def _fetch(url: str, dest: Path, timeout: int = 60) -> bool:
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
WORLDBANK_INDICATORS = {
    "unemployment_total": "SL.UEM.TOTL.ZS",
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "education_spend_pct_gdp": "SE.XPD.TOTL.GD.ZS",
}

def download_worldbank(countries: str = "all", start_year: int = 2000, end_year: int = 2025):
    print("\n=== World Bank API ===")
    for name, code in WORLDBANK_INDICATORS.items():
        url = (
            f"https://api.worldbank.org/v2/country/{countries}/indicator/{code}"
            f"?date={start_year}:{end_year}&format=json&per_page=20000"
        )
        _fetch(url, DATA_DIR / f"worldbank_{name}.json", timeout=30)


# =================================================================
# 2. Eurostat API -- automatisable
# =================================================================
EUROSTAT_DATASETS = {"ict_specialists": "isoc_sks_itspt"}

def download_eurostat():
    print("\n=== Eurostat API ===")
    for name, dataset_code in EUROSTAT_DATASETS.items():
        url = (
            f"https://ec.europa.eu/eurostat/api/dissemination/"
            f"statistics/1.0/data/{dataset_code}?format=JSON&lang=FR"
        )
        _fetch(url, DATA_DIR / f"eurostat_{name}.json", timeout=30)


# =================================================================
# 3. TIMSS -- tous cycles, URLs verifiees sur les vraies pages
#    (timss2023.org/data, timss2019.org/international-database,
#    timssandpirls.bc.edu/timss2015/international-database)
#    le 2026-10-06.
# =================================================================

TIMSS_CYCLES = {
    2023: {
        "base": "https://timss2023.org/wp-content/uploads/data/",
        "light": {
            "curriculum_g4": "T23_CurriculumData_G4.xlsx",
            "curriculum_g8": "T23_CurriculumData_G8.xlsx",
            "tcma_g4": "T23_TCMAData_G4.xlsx",
            "tcma_g8": "T23_TCMAData_G8.xlsx",
            "codebook_g4": "T23_Codebook_G4.xlsx",
            "codebook_g8": "T23_Codebook_G8.xlsx",
            "almanacs_achievement_g4": "T23_Almanacs_Achievement_G4.zip",
            "almanacs_achievement_g8": "T23_Almanacs_Achievement_G8.zip",
            "almanacs_context_g4": "T23_Almanacs_Context_G4.zip",
            "almanacs_context_g8": "T23_Almanacs_Context_G8.zip",
            "item_info_g4": "T23_ItemInformation_G4.xlsx",
            "item_info_g8": "T23_ItemInformation_G8.xlsx",
            "irt_params_g4": "T23_IRTParameters_G4.xlsx",
            "irt_params_g8": "T23_IRTParameters_G8.xlsx",
            "context_questionnaires_g4": "T23_ContextQuestionnaires_G4.zip",
            "context_questionnaires_g8": "T23_ContextQuestionnaires_G8.zip",
            "national_adaptations_g4": "T23_NationalAdaptations_G4.zip",
            "national_adaptations_g8": "T23_NationalAdaptations_G8.zip",
            "derived_context_g4": "T23_DerivedContextVariables_G4.zip",
            "derived_context_g8": "T23_DerivedContextVariables_G8.zip",
        },
        "heavy": {
            "spss_g4": "T23_Data_SPSS_G4.zip",   # 991 Mo
            "spss_g8": "T23_Data_SPSS_G8.zip",   # 949 Mo
        },
    },
    2019: {
        "base": "https://timss2019.org/international-database/downloads/",
        "light": {
            "item_info_g4": "T19_G4_Item Information.zip",
            "item_info_g8": "T19_G8_Item Information.zip",
            "irt_params_g4": "T19_G4_IRT Item Parameters.zip",
            "irt_params_g8": "T19_G8_IRT Item Parameters.zip",
            "item_pct_correct_g4": "T19_G4_Item Percent Correct Statistics.zip",
            "item_pct_correct_g8": "T19_G8_Item Percent Correct Statistics.zip",
            "curriculum_g4": "T19_G4_Curriculum Data.zip",
            "curriculum_g8": "T19_G8_Curriculum Data.zip",
            "codebooks_g4": "T19_G4_Codebooks.zip",
            "codebooks_g8": "T19_G8_Codebooks.zip",
            "almanacs_g4": "T19_G4_Almanacs.zip",
            "almanacs_g8": "T19_G8_Almanacs.zip",
            "tcma_g4": "T19_G4_TCMA Item Selection.zip",
            "tcma_g8": "T19_G8_TCMA Item Selection.zip",
        },
        "heavy": {
            "spss_g4": "T19_G4_SPSS Data.zip",   # 781 Mo
            "spss_g8": "T19_G8_SPSS Data.zip",   # 703 Mo
        },
    },
    2015: {
        "base": "https://timssandpirls.bc.edu/timss2015/international-database/downloads/",
        "light": {
            "item_info_g4": "T15_G4_ItemInformation.zip",
            "item_info_g8": "T15_G8_ItemInformation.zip",
            "irt_params_g4": "T15_G4_IRTItemParameters.zip",
            "irt_params_g8": "T15_G8_IRTItemParameters.zip",
            "item_pct_correct_g4": "T15_G4_ItemPercentCorrectStatistics.zip",
            "item_pct_correct_g8": "T15_G8_ItemPercentCorrectStatistics.zip",
            "curriculum_g4": "T15_G4_CQ_Data.zip",
            "curriculum_g8": "T15_G8_CQ_Data.zip",
            "codebook_g4": "T15_G4_Codebook.zip",
            "codebook_g8": "T15_G8_Codebook.zip",
            "almanacs_g4": "T15_G4_Almanacs.zip",
            "almanacs_g8": "T15_G8_Almanacs.zip",
            "tcma_g4": "T15_G4_TCMAItemSelection.zip",
            "tcma_g8": "T15_G8_TCMAItemSelection.zip",
        },
        "heavy": {
            # Fichiers scindes en plusieurs parties sur le site source
            "spss_g4_pt1": "T15_G4_SPSSData_pt1.zip",   # 161 Mo
            "spss_g4_pt2": "T15_G4_SPSSData_pt2.zip",   # 144 Mo
            "spss_g4_pt3": "T15_G4_SPSSData_pt3.zip",   # 144 Mo
            "spss_g8_pt1": "T15_G8_SPSSData_pt1.zip",   # 148 Mo
            "spss_g8_pt2": "T15_G8_SPSSData_pt2.zip",   # 129 Mo
            "spss_g8_pt3": "T15_G8_SPSSData_pt3.zip",   # 134 Mo
            "spss_g8_pt4": "T15_G8_SPSSData_pt4.zip",   # 130 Mo
        },
    },
}


def download_timss(cycles: list[int], include_heavy: bool = False):
    """Telecharge les fichiers TIMSS pour les cycles demandes.
    Par defaut, fichiers legers uniquement (xlsx/zip de quelques
    Mo). include_heavy=True ajoute les microdonnees completes
    (plusieurs centaines de Mo a ~1 Go par grade et par cycle)."""
    for year in cycles:
        if year not in TIMSS_CYCLES:
            print(f"\nCycle {year} non reconnu (disponibles: {list(TIMSS_CYCLES)})")
            continue

        info = TIMSS_CYCLES[year]
        print(f"\n=== TIMSS {year} -- fichiers legers ===")
        for key, filename in info["light"].items():
            url = info["base"] + quote(filename)
            suffix = Path(filename).suffix
            dest = DATA_DIR / f"timss{year}_{key}{suffix}"
            _fetch(url, dest, timeout=60)

        if include_heavy:
            print(f"\n=== TIMSS {year} -- microdonnees completes ===")
            for key, filename in info["heavy"].items():
                url = info["base"] + quote(filename)
                dest = DATA_DIR / f"timss{year}_{key}.zip"
                _fetch(url, dest, timeout=300)
        else:
            n_heavy = len(info["heavy"])
            print(f"  ({n_heavy} fichier(s) lourd(s) ignores pour {year} -- "
                  f"utiliser --timss-heavy pour les inclure)")


# =================================================================
# 4. OECD SDMX API -- endpoint a reconfirmer avant usage, l'API a
#    change de structure plusieurs fois
# =================================================================

def download_oecd_sdmx(dataset_id: str, dest_name: str):
    print(f"\n=== OCDE SDMX: {dataset_id} ===")
    url = f"https://sdmx.oecd.org/public/rest/data/{dataset_id}/all?format=csvfile"
    ok = _fetch(url, DATA_DIR / f"oecd_{dest_name}.csv", timeout=60)
    if not ok:
        print(
            "  -> si echec, l'URL SDMX a probablement change. "
            "Verifier sur data.oecd.org/api ou data-explorer.oecd.org."
        )


# =================================================================
# 5. Sources a telechargement manuel -- le script VERIFIE et
#    INSTRUIT, n'automatise pas ce qui ne peut pas l'etre honnetement
# =================================================================

MANUAL_SOURCES = {
    "pisa_database": {
        "expected_file": "pisa_2000_2025.csv",
        "url": "https://www.oecd.org/en/data/datasets/pisa-datasets.html",
        "instructions": (
            "Telecharger via le PISA Data Explorer, tous cycles "
            "2000-2025, scores maths/lecture/sciences + indices DISCLIM."
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
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true", help="Tout executer (automatisable, fichiers legers + verification)")
    parser.add_argument("--worldbank", action="store_true")
    parser.add_argument("--eurostat", action="store_true")
    parser.add_argument("--timss", nargs="*", type=int, metavar="ANNEE",
                         help="TIMSS, cycles choisis parmi 2023 2019 2015 (ex: --timss 2023 2019). Sans argument: les trois.")
    parser.add_argument("--timss-heavy", action="store_true",
                         help="Avec --timss: inclut aussi les microdonnees completes (plusieurs centaines de Mo par cycle/grade)")
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

    if args.timss is not None or args.all:
        cycles = args.timss if args.timss else list(TIMSS_CYCLES)
        download_timss(cycles, include_heavy=args.timss_heavy)

    if args.oecd:
        download_oecd_sdmx(args.oecd, args.oecd.lower())

    if not any([args.all, args.worldbank, args.eurostat, args.timss is not None, args.oecd, args.check]):
        parser.print_help()


if __name__ == "__main__":
    main()