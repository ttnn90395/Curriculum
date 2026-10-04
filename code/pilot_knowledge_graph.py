"""
Projet Education -- Graphe pilote KST (A.5)
=============================================
Premiere esquisse concrete du graphe de prerequis (Knowledge Space
Theory, Doignon & Falmagne) sur un sous-domaine pilote: arithmetique
-> algebre, correspondant approximativement au tronc commun avant
bifurcation (grades 1-9 selon les pays).

STATUT: ebauche a dire d'expert (sequencement pedagogique standard),
PAS encore validee contre un referentiel externe. A faire avant
utilisation dans le modele:
  1. Confronter cette liste au TIMSS 2023 Mathematics Framework
     (topic list officielle par grade) pour verifier la couverture
     et la granularite -- non fait ici, aucun acces reseau IEA
     depuis ce sandbox
  2. Faire valider les relations de prerequis par au moins une
     source pedagogique independante (programme officiel francais,
     Common Core US, etc.) -- la subjectivite de cette etape a
     deja ete signalee comme limite du modele (Partie 3, Section
     "Limites")
  3. Les coefficients IRT/BLIM sont des PLACEHOLDERS (None) --
     a remplacer par des parametres estimes sur des items publics
     PISA/TIMSS une fois les donnees chargees

20 notions, coherent avec la cible de 20-40 notions par domaine
actee pour le scope maths+sciences.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Notion:
    id: str
    label: str
    prerequisites: list[str] = field(default_factory=list)
    # Coefficient IRT (difficulte) -- a estimer, None = non disponible
    irt_difficulty: Optional[float] = None
    irt_discrimination: Optional[float] = None
    # Niveau approximatif (grade) d'introduction standard -- indicatif,
    # PAS une donnee TIMSS reelle, juste un repere de construction
    typical_grade: Optional[int] = None


# -----------------------------------------------------------------
# Le graphe pilote
# -----------------------------------------------------------------
GRAPH: dict[str, Notion] = {
    n.id: n
    for n in [
        Notion("n01", "Sens du nombre / comptage", [], typical_grade=1),
        Notion("n02", "Addition et soustraction", ["n01"], typical_grade=1),
        Notion("n03", "Valeur positionnelle (numeration decimale)", ["n01"], typical_grade=2),
        Notion("n04", "Multiplication", ["n02"], typical_grade=3),
        Notion("n05", "Division", ["n04"], typical_grade=3),
        Notion("n06", "Fractions (concept)", ["n02", "n03"], typical_grade=4),
        Notion("n07", "Operations sur les fractions", ["n06", "n04", "n05"], typical_grade=5),
        Notion("n08", "Nombres decimaux", ["n03", "n06"], typical_grade=5),
        Notion("n09", "Nombres negatifs", ["n02"], typical_grade=5),
        Notion("n10", "Priorite des operations", ["n04", "n02"], typical_grade=5),
        Notion("n11", "Rapports et proportions", ["n06", "n04"], typical_grade=6),
        Notion("n12", "Pourcentages", ["n06", "n11"], typical_grade=6),
        Notion("n13", "Notation algebrique / variables", ["n02", "n04", "n09"], typical_grade=6),
        Notion("n14", "Equations lineaires a une inconnue", ["n13", "n10"], typical_grade=7),
        Notion("n15", "Puissances et exposants", ["n04"], typical_grade=7),
        Notion("n16", "Simplification d'expressions algebriques", ["n13", "n09", "n15"], typical_grade=7),
        Notion("n17", "Systemes d'equations lineaires", ["n14"], typical_grade=8),
        Notion("n18", "Notion de fonction", ["n13", "n11"], typical_grade=8),
        Notion("n19", "Fonctions lineaires / representation graphique", ["n18", "n14"], typical_grade=8),
        Notion("n20", "Expressions quadratiques", ["n16", "n15"], typical_grade=9),
    ]
}


# -----------------------------------------------------------------
# Operations Knowledge Space Theory
# -----------------------------------------------------------------

def is_valid_state(state: set[str], graph: dict[str, Notion]) -> bool:
    """Un etat de connaissance est valide si chaque notion maitrisee
    a tous ses prerequis egalement maitrises (relation de surmise)."""
    for notion_id in state:
        prereqs = set(graph[notion_id].prerequisites)
        if not prereqs.issubset(state):
            return False
    return True


def fringe(state: set[str], graph: dict[str, Notion]) -> set[str]:
    """Notions immediatement accessibles depuis un etat donne:
    pas encore maitrisees, mais dont tous les prerequis le sont.
    Utilise pour la sequentialisation (Section 'Proposition de
    reforme') et pour detecter les violations de prerequis
    (Partie 3, score de violation)."""
    accessible = set()
    for notion_id, notion in graph.items():
        if notion_id in state:
            continue
        if set(notion.prerequisites).issubset(state):
            accessible.add(notion_id)
    return accessible


def prerequisite_violation_score(
    teaching_order: list[str], graph: dict[str, Notion]
) -> float:
    """Score de violation des prerequis (Partie 3, Section 1.2).

    Pour chaque notion enseignee, verifie si tous ses prerequis ont
    deja ete enseignes avant elle dans l'ordre reel observe. Retourne
    la proportion de notions enseignees AVANT au moins un de leurs
    prerequis (0 = aucune violation, 1 = toutes violees).

    teaching_order attendu: liste des notion_id dans l'ordre reel
    d'enseignement observe pour un pays donne (a construire a partir
    des donnees de curriculum implemente, TIMSS Teacher Questionnaire
    + National Curriculum documents selon le pays).
    """
    taught_so_far: set[str] = set()
    violations = 0
    for notion_id in teaching_order:
        prereqs = set(graph[notion_id].prerequisites)
        if not prereqs.issubset(taught_so_far):
            violations += 1
        taught_so_far.add(notion_id)
    return violations / len(teaching_order) if teaching_order else 0.0


def topological_levels(graph: dict[str, Notion]) -> list[list[str]]:
    """Organise le graphe en niveaux (notions sans prerequis
    restants a chaque etape) -- donne une sequence d'enseignement
    minimale valide, utile comme base pour comparer a l'ordre
    reel d'un pays (cf. prerequisite_violation_score)."""
    remaining = dict(graph)
    levels = []
    mastered: set[str] = set()
    while remaining:
        level = [
            nid for nid, n in remaining.items()
            if set(n.prerequisites).issubset(mastered)
        ]
        if not level:
            raise ValueError(
                "Cycle detecte dans le graphe -- relation de "
                "surmise invalide (un prerequis depend de lui-meme "
                "indirectement)"
            )
        levels.append(sorted(level))
        mastered.update(level)
        for nid in level:
            del remaining[nid]
    return levels


if __name__ == "__main__":
    print(f"Graphe pilote: {len(GRAPH)} notions\n")

    print("=== Niveaux topologiques (sequence minimale valide) ===")
    for i, level in enumerate(topological_levels(GRAPH)):
        labels = [f"{nid} ({GRAPH[nid].label})" for nid in level]
        print(f"  Niveau {i}: {labels}")

    print("\n=== Verification: le graphe est acyclique et coherent ===")
    all_state = set(GRAPH.keys())
    print(f"  Etat complet valide: {is_valid_state(all_state, GRAPH)}")

    print("\n=== Exemple de fringe depuis l'etat vide ===")
    print(f"  {fringe(set(), GRAPH)}  (devrait etre {{'n01'}})")

    print("\n=== Exemple de violation de prerequis ===")
    # Ordre hypothetique ou l'algebre (n13) est enseignee AVANT
    # les negatifs (n09), alors que n13 en depend -- simule un
    # pays qui "saute" un prerequis
    bad_order = ["n01", "n02", "n03", "n04", "n13", "n09", "n05"]
    score = prerequisite_violation_score(bad_order, GRAPH)
    print(f"  Ordre teste: {bad_order}")
    print(f"  Score de violation: {score:.2%}")

    print("\n=== Coefficients IRT/BLIM ===")
    missing = [n.id for n in GRAPH.values() if n.irt_difficulty is None]
    print(
        f"  {len(missing)}/{len(GRAPH)} notions sans coefficient IRT "
        f"-- PLACEHOLDER, a estimer sur items publics PISA/TIMSS"
    )
