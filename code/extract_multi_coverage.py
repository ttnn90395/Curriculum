"""
Projet Education -- Extraction multi-cycle de la couverture curriculaire
===========================================================================
Construit sur ce qui a ete verifie reellement (pas suppose) sur les
3 cycles G4 (2015, 2019, 2023), tous disponibles pour France/
Allemagne/Pologne.

PRINCIPE CLE: les codes de question changent de cycle en cycle
(MA408 en 2015/2023, MA407 en 2019, pour les MEMES domaines) --
la correspondance se fait par LIBELLE de domaine (texte de la
ligne 1), jamais par code.

ENCODAGE: 3 systemes differents selon le cycle, harmonises ici.
2019 reste INCOMPLET tant que le codebook n'a pas ete inspecte
(TODO explicite ci-dessous, pas une supposition).
"""

from __future__ import annotations
import zipfile
import tempfile
from pathlib import Path
from dataclasses import dataclass
import openpyxl
import pandas as pd


DOMAIN_PATTERNS = {
    "Nombre": ["number"],
    "Mesure_Geometrie": ["measurement and geometry"],
    "Donnees": ["data display", "data and chance", "data"],
}

# Encodage confirme par cycle, a partir des valeurs reellement
# observees (inspect_timss_file.py) -- PAS suppose entre cycles
ENCODING_2023 = {
    "All or almost all students": 1.0,
    "Only the more advanced students": 0.5,
    "Not included in the curriculum through Grade 4": 0.0,
}
ENCODING_2015 = {
    "Topics Taught to All or Almost All Students": 1.0,
    "Topics Taught to Only the More Able Students (Top Track)": 0.5,
    "Not Included in the Curriculum Through Grade 4": 0.0,
}
# TODO -- NON RESOLU: 2019 utilise des codes numeriques {1,2,3} sans
# legende visible dans le fichier de donnees lui-meme. Inspecter
# data/raw/timss2019_codebooks_g4.zip pour la correspondance exacte
# avant d'utiliser ENCODING_2019 -- NE PAS SUPPOSER que 1=1.0, etc.
# (l'ordre pourrait tres bien etre invers par rapport aux deux
# autres cycles).
ENCODING_2019 = None  # explicitement vide tant que non verifie

ENCODINGS_BY_CYCLE = {2023: ENCODING_2023, 2019: ENCODING_2019, 2015: ENCODING_2015}

# Valeurs admises dans une colonne de couverture, par cycle. Sert a
# FILTRER les colonnes par leur contenu (pas par leur position):
# une colonne dont une valeur sort de cet ensemble n'est pas un item
# de couverture (ex: reponses Y/N, numeros de grade) et est ecartee.
# 2019: seule la STRUCTURE {1,2,3} est exploitee ici, pas le sens.
VALID_VALUES_BY_CYCLE = {
    2023: set(ENCODING_2023),
    2015: set(ENCODING_2015),
    2019: {1, 2, 3},
}


@dataclass
class CycleFile:
    cycle: int
    path: Path
    sheet_name: str  # ex: "T23_G4_Mathematics Module"


def _open_module_sheet(cf: CycleFile) -> openpyxl.worksheet.worksheet.Worksheet:
    path = cf.path
    if path.suffix == ".zip":
        tmpdir = Path(tempfile.mkdtemp())
        with zipfile.ZipFile(path) as z:
            xlsx_names = [n for n in z.namelist() if n.lower().endswith(".xlsx")]
            if len(xlsx_names) != 1:
                raise ValueError(f"{path}: attendu 1 xlsx, trouve {xlsx_names}")
            z.extract(xlsx_names[0], tmpdir)
            path = tmpdir / xlsx_names[0]
    wb = openpyxl.load_workbook(path, data_only=True)
    return wb[cf.sheet_name]


def _find_country_col(headers_code: list) -> int:
    for i, code in enumerate(headers_code):
        if code == "Country":
            return i
    raise ValueError("Colonne 'Country' introuvable (ligne 3)")


def _find_domain_columns(headers_r1: list, headers_r2: list, headers_code: list) -> dict[str, list[int]]:
    """Associe chaque domaine (par libelle, pas par code) a la
    liste des colonnes qui lui appartiennent -- toutes les colonnes
    entre un en-tete de domaine et le suivant, en excluant les
    colonnes de commentaires (suffixe T/TA/TB dans le code)."""
    domain_starts: list[tuple[int, str]] = []
    for i, q in enumerate(headers_r1):
        if not q:
            continue
        q_lower = str(q).lower()
        for domain_name, patterns in DOMAIN_PATTERNS.items():
            if any(p in q_lower for p in patterns) and "proportion" in q_lower:
                domain_starts.append((i, domain_name))
                break

    if not domain_starts:
        return {}

    domain_cols: dict[str, list[int]] = {name: [] for _, name in domain_starts}
    sorted_starts = sorted(domain_starts, key=lambda x: x[0])
    for idx, (start_col, domain_name) in enumerate(sorted_starts):
        end_col = sorted_starts[idx + 1][0] if idx + 1 < len(sorted_starts) else len(headers_code)
        for col in range(start_col, end_col):
            code = headers_code[col]
            if code and not str(code).endswith(("T", "TA", "TB", "CP", "EP")):
                domain_cols[domain_name].append(col)
    return domain_cols


def extract_cycle(cf: CycleFile) -> pd.DataFrame:
    ws = _open_module_sheet(cf)
    headers_r1 = [c.value for c in ws[1]]
    headers_code = [c.value for c in ws[3]]

    country_col = _find_country_col(headers_code)
    candidate_cols = _find_domain_columns(headers_r1, [c.value for c in ws[2]], headers_code)

    data_rows = [r for r in ws.iter_rows(min_row=4, values_only=True) if r[country_col]]

    # FILTRE PAR CONTENU: ne garder que les colonnes dont TOUTES les
    # valeurs non nulles appartiennent aux valeurs admises du cycle
    valid = VALID_VALUES_BY_CYCLE[cf.cycle]
    domain_cols: dict[str, list[int]] = {}
    for domain_name, cols in candidate_cols.items():
        kept = []
        for c in cols:
            vals = {r[c] for r in data_rows if c < len(r) and r[c] is not None}
            if vals and vals <= valid:
                kept.append(c)
        domain_cols[domain_name] = kept
        print(f"  [{cf.cycle}] {domain_name}: {len(kept)} items retenus "
              f"sur {len(cols)} colonnes candidates")

    encoding = ENCODINGS_BY_CYCLE.get(cf.cycle)

    rows = []
    for row in data_rows:
        country = row[country_col]
        for domain_name, cols in domain_cols.items():
            raw_vals = [row[c] for c in cols if c < len(row) and row[c] is not None]
            if encoding is not None:
                numeric_vals = [encoding[v] for v in raw_vals]  # sur: filtre amont
            else:
                numeric_vals = []  # 2019: encodage non resolu (cf. TODO)

            rows.append(dict(
                cycle=cf.cycle,
                country=country,
                domain=domain_name,
                n_items=len(raw_vals),
                raw_values=raw_vals,
                mean_coverage=(sum(numeric_vals) / len(numeric_vals)) if numeric_vals else None,
            ))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

    cycle_files = [
        CycleFile(2015, DATA_DIR / "timss2015_curriculum_g4.zip", "T15_G4_Mathematics Module"),
        CycleFile(2019, DATA_DIR / "timss2019_curriculum_g4.zip", "T19_G4_Mathematics Module"),
        CycleFile(2023, DATA_DIR / "timss2023_curriculum_g4.xlsx", "T23_G4_Mathematics Module"),
    ]

    all_data = []
    for cf in cycle_files:
        if not cf.path.exists():
            print(f"MANQUANT: {cf.path} -- ignore")
            continue
        print(f"Extraction cycle {cf.cycle}...")
        df = extract_cycle(cf)
        all_data.append(df)

    full = pd.concat(all_data, ignore_index=True)
    print(f"\nTotal: {len(full)} lignes ({full['cycle'].nunique()} cycles)")

    print("\n" + "=" * 70)
    print("FRANCE / ALLEMAGNE / POLOGNE -- evolution 2015-2023 (Grade 4, maths)")
    print("=" * 70)
    targets = full[full["country"].isin(["France", "Germany", "Poland"])]
    pivot = targets.pivot_table(
        index=["country", "domain"], columns="cycle", values="mean_coverage"
    )
    print(pivot.round(3).to_string())

    print("\nNombre d'items retenus par cycle (comparabilite: les moyennes de "
          "domaine ne sont comparables entre cycles que si ces nombres sont proches):")
    n_pivot = targets.pivot_table(
        index=["country", "domain"], columns="cycle", values="n_items", aggfunc="first"
    )
    print(n_pivot.to_string())

    n_2019_missing = full[(full["cycle"] == 2019) & (full["mean_coverage"].isna())].shape[0]
    print(f"\nNOTE: {n_2019_missing} lignes 2019 sans valeur numerique -- "
          f"encodage 2019 non resolu (cf. TODO dans le code), "
          f"a completer apres inspection du codebook 2019.")