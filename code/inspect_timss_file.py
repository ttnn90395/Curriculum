"""
Projet Education -- Inspecteur generique de fichiers TIMSS Curriculum
========================================================================
Deux erreurs deja commises en travaillant a l'aveugle sur ces fichiers
(onglets Status peu fiables ; mauvais index de colonne pays) montrent
qu'il ne faut plus deviner la structure -- l'inspecter d'abord,
systematiquement, cycle par cycle, avant d'ecrire du code
d'extraction specifique.

Usage:
    python inspect_timss_file.py data/raw/timss2019_curriculum_g4.zip
    python inspect_timss_file.py data/raw/timss2023_curriculum_g4.xlsx
"""

import sys
import zipfile
import tempfile
from pathlib import Path
import openpyxl


def find_xlsx_in_zip(zip_path: Path) -> Path:
    """Extrait le xlsx d'un zip TIMSS vers un dossier temporaire,
    retourne son chemin. Echoue explicitement si zero ou plusieurs
    xlsx trouves (pas de choix silencieux)."""
    tmpdir = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(zip_path) as z:
        xlsx_names = [n for n in z.namelist() if n.lower().endswith(".xlsx")]
        if len(xlsx_names) != 1:
            raise ValueError(
                f"Attendu exactement 1 xlsx dans {zip_path.name}, "
                f"trouve {len(xlsx_names)}: {xlsx_names}. "
                f"Contenu complet: {z.namelist()}"
            )
        z.extract(xlsx_names[0], tmpdir)
        return tmpdir / xlsx_names[0]


def inspect(filepath: str) -> None:
    path = Path(filepath)
    if not path.exists():
        print(f"Fichier introuvable: {path}")
        sys.exit(1)

    if path.suffix == ".zip":
        print(f"Extraction du zip {path.name}...")
        xlsx_path = find_xlsx_in_zip(path)
        print(f"  -> {xlsx_path.name}")
    elif path.suffix == ".xlsx":
        xlsx_path = path
    else:
        print(f"Extension non geree: {path.suffix}")
        sys.exit(1)

    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    print(f"\nFeuilles: {wb.sheetnames}")

    module_sheets = [s for s in wb.sheetnames if "Module" in s]
    print(f"\nOnglets de module (DONNEES REELLES, pas les onglets Status): {module_sheets}")

    for sheet_name in module_sheets:
        ws = wb[sheet_name]
        print(f"\n{'=' * 70}\n{sheet_name} -- dimensions {ws.dimensions}")

        headers_r1 = [c.value for c in ws[1]]
        headers_r3 = [c.value for c in ws[3]]

        print(f"  En-tete ligne 1, colonnes 0-2: {headers_r1[:3]}")
        print(f"  En-tete ligne 3 (codes), colonnes 0-5: {headers_r3[:5]}")

        # Colonne pays: cherche la colonne dont le code/header
        # vaut litteralement 'Country' (ne PAS supposer l'index)
        country_col = None
        for i, code in enumerate(headers_r3):
            if code == "Country":
                country_col = i
                break
        if country_col is None:
            print("  ATTENTION: aucune colonne 'Country' trouvee en ligne 3 "
                  "-- verifier manuellement, structure inattendue")
            continue

        print(f"  Colonne pays trouvee a l'index {country_col} (pas suppose)")

        countries = sorted(set(
            row[country_col] for row in ws.iter_rows(min_row=4, values_only=True)
            if row[country_col]
        ))
        print(f"  {len(countries)} pays avec donnees reelles")
        for target in ("France", "Germany", "Poland"):
            present = target in countries
            print(f"    {target}: {'present' if present else 'ABSENT'}")

        # Codes de questions de couverture (contenant "proportion")
        coverage_codes = []
        for i, (q, code) in enumerate(zip(headers_r1, headers_r3)):
            if q and "proportion" in str(q).lower() and code:
                coverage_codes.append((code, str(q)[:70]))
        print(f"\n  Questions de couverture ('proportion'): {len(coverage_codes)} domaines trouves")
        for code, q in coverage_codes[:10]:
            print(f"    {code}: {q}")

        # Valeurs uniques rencontrees dans les colonnes de couverture
        # (prend la premiere colonne de chaque domaine comme echantillon)
        if coverage_codes:
            sample_code = coverage_codes[0][0]
            sample_idx = headers_r3.index(sample_code)
            values = set(
                row[sample_idx] for row in ws.iter_rows(min_row=4, values_only=True)
                if row[sample_idx] is not None
            )
            print(f"\n  Valeurs uniques pour {sample_code} (echantillon d'encodage): {values}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python inspect_timss_file.py <chemin_vers_fichier>")
        sys.exit(1)
    inspect(sys.argv[1])