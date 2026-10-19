"""Extension du graphe pilote KST aux sujets de la 4e annee TIMSS (maths):
mesure, geometrie, donnees, et notions arithmetiques manquantes.
STATUT: relations de prerequis a DIRE D'EXPERT, non validees contre un referentiel externe.
Les notions du pilote (n01..n20) ne sont PAS modifiees: on AJOUTE des notions et des aretes.
Aretes candidates vers des notions existantes (non appliquees, a valider): n13 <- n22 (inconnue/phrases numeriques).
Usage: python code/kst_extension.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pilot_knowledge_graph import GRAPH, Notion, topological_levels, is_valid_state

NEW = [
    # arithmetique manquante (sujets TIMSS N3, N6, N7)
    Notion("n21", "Multiples, facteurs, pair/impair", ["n04", "n05"], typical_grade=4),
    Notion("n22", "Phrases numeriques / nombre manquant (pre-algebre)", ["n02", "n04"], typical_grade=3),
    Notion("n23", "Suites et regularites", ["n02", "n04"], typical_grade=3),
    # mesure (G1-G3)
    Notion("m01", "Mesure de longueurs", ["n02"], typical_grade=2),
    Notion("m02", "Masse, volume (capacite), temps", ["m01", "n02"], typical_grade=3),
    # geometrie (G4-G6)
    Notion("g01", "Proprietes elementaires des figures planes", ["m01"], typical_grade=2),
    Notion("g02", "Droites paralleles/perpendiculaires et angles", ["g01"], typical_grade=4),
    Notion("g03", "Solides 3D et representations 2D", ["g01"], typical_grade=3),
    Notion("m03", "Perimetre, aire, volume", ["m01", "n04", "g01"], typical_grade=4),
    # donnees (D1-D2)
    Notion("d01", "Lire et representer des donnees", ["n01", "n02"], typical_grade=2),
    Notion("d02", "Tirer des conclusions de representations de donnees", ["d01", "n02"], typical_grade=3),
]

EXT = dict(GRAPH)
for n in NEW:
    assert n.id not in EXT, f"identifiant deja pris: {n.id}"
    EXT[n.id] = n

# sujets communs du tableau data/crosswalk_g4_math.csv -> notions du graphe
TOPIC_TO_NOTIONS = {
    "N1": ["n03"], "N2": ["n02", "n04", "n05"], "N3": ["n21"], "N4": ["n06", "n07"],
    "N5": ["n08"], "N6": ["n22"], "N7": ["n23"],
    "G1": ["m01"], "G2": ["m02"], "G3": ["m03"], "G4": ["g02"], "G5": ["g01"], "G6": ["g03"],
    "D1": ["d01"], "D2": ["d02"],
}
# NB: n01 (comptage) est un prerequis du pilote sans sujet TIMSS G4 propre (acquis avant la 4e annee).


def audit():
    problems = []
    for n in EXT.values():
        for p in n.prerequisites:
            if p not in EXT:
                problems.append(f"{n.id}: prerequis inconnu {p}")
            elif n.typical_grade is not None and EXT[p].typical_grade is not None and EXT[p].typical_grade > n.typical_grade:
                problems.append(f"{n.id} (grade {n.typical_grade}) depend de {p} (grade {EXT[p].typical_grade})")
    for t, ns in TOPIC_TO_NOTIONS.items():
        for x in ns:
            if x not in EXT:
                problems.append(f"sujet {t}: notion inconnue {x}")
    try:
        levels = topological_levels(EXT)
    except ValueError as e:
        problems.append(str(e)); levels = []
    return problems, levels


if __name__ == "__main__":
    problems, levels = audit()
    print(f"Graphe etendu: {len(EXT)} notions ({len(GRAPH)} pilote + {len(NEW)} ajoutees)")
    print("Audit:", "OK (acyclique, prerequis existants, grades coherents)" if not problems else "")
    for p in problems:
        print("  PROBLEME:", p)
    for i, lv in enumerate(levels):
        print(f"  Niveau {i}: {', '.join(lv)}")
    used = {x for ns in TOPIC_TO_NOTIONS.values() for x in ns}
    g4 = {k for k, n in EXT.items() if (n.typical_grade or 99) <= 4}
    print(f"\nSujets TIMSS G4 relies au graphe: {len(TOPIC_TO_NOTIONS)}/15; notions utilisees: {len(used)}")
    print("Notions de grade <= 4 sans sujet TIMSS G4:", sorted(g4 - used) or "aucune")
    print("Notions au-dela de la 4e annee SANS sujet TIMSS G4:", sorted(k for k in EXT if k not in g4 and k not in used))
    print("Notions de grade pilote > 4 mais couvertes par un sujet TIMSS G4 (a revoir, typical_grade du pilote):",
          sorted(k for k in used if (EXT[k].typical_grade or 0) > 4))
    print(f"Etat complet valide: {is_valid_state(set(EXT), EXT)}")
