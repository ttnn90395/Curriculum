"""
Projet Education -- Extraction de la couverture curriculaire reelle
======================================================================
Lit les fichiers TIMSS 2023 Curriculum Questionnaire (xlsx legers,
telecharges via download_data.py --timss) et produit une table
propre pays x sous-item x proportion.

TESTE sur les fichiers reels timss2023_curriculum_g4.xlsx et
timss2023_curriculum_g8.xlsx (uploades et verifies le 2026-10-05).

Statut par rapport a g_{i,n}: ce fichier donne x_{i,n} (curriculum
PREVU, NRC) uniquement. p_{i,n} (curriculum IMPLEMENTE, declare
par les enseignants) necessite le Teacher Questionnaire, absent
des fichiers legers -- probablement dans T23_Data_SPSS_G4.zip.

IMPORTANT: utiliser uniquement les onglets '..._Module' pour
compter les pays -- les onglets 'Status' ne reflètent PAS
fiablement les donnees reelles (ecart confirme empiriquement:
France absente du G8 Status mais presente dans les vraies donnees).
"""

from __future__ import annotations
from pathlib import Path
import openpyxl
import pandas as pd


# Mapping topic_code -> (domaine, libelle complet, notion du
# graphe pilote correspondante si applicable)
# Construit a partir des lignes 1-2 des fichiers reels (grade 4,
# module Mathematiques, question MA408)
G4_MATH_TOPICS = {
    "MA408AA": ("Nombre", "Valeur de position, comparaison de nombres", "n01/n03"),
    "MA408AB": ("Nombre", "Addition et soustraction (jusqu'a 4 chiffres)", "n02"),
    "MA408AC": ("Nombre", "Multiplication et division", "n04/n05"),
    "MA408AD": ("Nombre", "Multiples, facteurs, arrondis, estimations", "n04 (proche)"),
    "MA408AE": ("Nombre", "Combiner proprietes des nombres/operations", "n10 (proche)"),
    "MA408AF": ("Nombre", "Nombre manquant dans une equation", "n13 (proche, pre-algebre)"),
    "MA408AG": ("Nombre", "Ecrire des expressions representant un probleme", "n13 (proche)"),
    "MA408AH": ("Nombre", "Suites et relations", "non couvert par le pilote -- A AJOUTER"),
    "MA408AI": ("Nombre", "Fractions: representation, comparaison, operations simples", "n06/n07"),
    "MA408AJ": ("Nombre", "Decimaux: representation, comparaison, operations", "n08"),
    "MA408BA": ("Mesure/Geometrie", "Longueurs: mesurer, estimer, additionner", "hors scope pilote (geometrie)"),
    "MA408BB": ("Mesure/Geometrie", "Masse, volume, temps", "hors scope pilote"),
    "MA408BC": ("Mesure/Geometrie", "Perimetres, aires, volumes", "hors scope pilote"),
    "MA408BD": ("Mesure/Geometrie", "Droites paralleles/perpendiculaires, angles", "hors scope pilote"),
    "MA408BE": ("Mesure/Geometrie", "Symetrie, formes 2D", "hors scope pilote"),
    "MA408BF": ("Mesure/Geometrie", "Formes 3D", "hors scope pilote"),
    "MA408CA": ("Donnees", "Lire des tableaux/graphiques", "hors scope pilote"),
    "MA408CB": ("Donnees", "Creer des tableaux/graphiques", "hors scope pilote"),
    "MA408CC": ("Donnees", "Interpreter des donnees au-dela de la lecture directe", "hors scope pilote"),
    "MA408CD": ("Donnees", "Combiner/comparer des donnees de plusieurs sources", "hors scope pilote"),
}

# NOTE DE RIGUEUR: le graphe pilote (pilot_knowledge_graph.py) ne
# couvre QUE l'arithmetique/algebre -- il manque entierement le
# domaine Mesure/Geometrie et Donnees, qui representent 10 des 20
# sous-items reels du Grade 4 TIMSS. A etendre avant de pretendre
# que le graphe couvre "les maths" -- actuellement il ne couvre
# que la moitie du domaine Nombre.


def extract_g4_math_coverage(filepath: str | Path) -> pd.DataFrame:
    """Retourne un DataFrame long: country, topic_code, domaine,
    libelle, proportion (valeur brute du fichier -- verifier le
    type exact, probablement un code categoriel 1-5 plutot qu'un
    pourcentage continu, A CONFIRMER sur les vraies valeurs)."""
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb["T23_G4_Mathematics Module"]

    headers_code = [c.value for c in ws[3]]
    topic_cols = {
        i: code for i, code in enumerate(headers_code)
        if code in G4_MATH_TOPICS
    }

    rows = []
    for row in ws.iter_rows(min_row=4, values_only=True):
        country = row[1]
        if not country:
            continue
        for col_idx, code in topic_cols.items():
            domaine, libelle, pilot_match = G4_MATH_TOPICS[code]
            rows.append(dict(
                country=country,
                topic_code=code,
                domaine=domaine,
                libelle=libelle,
                pilot_graph_match=pilot_match,
                value=row[col_idx] if col_idx < len(row) else None,
            ))
    return pd.DataFrame(rows)


def real_oecd_countries(filepath: str | Path, sheet: str) -> set[str]:
    """Pays reellement presents dans un module de donnees --
    PAS dans l'onglet Status, qui s'est revele peu fiable."""
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb[sheet]
    return {row[1] for row in ws.iter_rows(min_row=4, values_only=True) if row[1]}


if __name__ == "__main__":
    import sys
    g4_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "timss2023_curriculum_g4.xlsx"
    if not g4_path.exists():
        print(f"Fichier non trouve: {g4_path}")
        print("Lancer d'abord: python download_data.py --timss")
        sys.exit(1)

    df = extract_g4_math_coverage(g4_path)
    print(f"Table extraite: {len(df)} lignes ({df['country'].nunique()} pays x {df['topic_code'].nunique()} sous-items)")
    print("\nType de valeur observe (5 premieres lignes non-nulles):")
    print(df[df["value"].notna()].head())

    print("\nValeurs uniques rencontrees (pour comprendre le codage):")
    print(sorted(df["value"].dropna().unique(), key=str)[:20])

    print("\nSous-items du pilote non couverts par le graphe actuel:")
    missing = df[df["pilot_graph_match"].str.contains("hors scope|A AJOUTER", na=False)]["topic_code"].unique()
    print(f"  {len(missing)}/20: {list(missing)}")