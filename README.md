# Projet Education

Recherche sur le lien entre qualité de l'éducation (tronc commun,
primaire + secondaire) et déclin économique de la France, avec
comparaison OCDE/IEA. Objectif final : proposer une réforme
curriculaire chiffrée (impact PISA/TIMSS projeté, coût, analyse
coût-bénéfice), avec un modèle prédictif de qualité éducative
construit à partir d'un graphe de prérequis (Knowledge Space Theory).

## Structure du dépôt

```
.
├── Plan.txt                  Plan détaillé du rapport (3 parties),
│                              avec TODO intégrés section par section
├── TODO.md                   Liste consolidée des vérifications
│                              restantes, par priorité
├── Liste_références.txt      Toutes les références (articles,
│                              rapports, bases de données)
├── code/
│   ├── pilot_knowledge_graph.py   Graphe KST pilote (20 notions,
│   │                               arithmétique -> algèbre) avec
│   │                               fringe() et score de violation
│   │                               de prérequis -- testé, tourne
│   │                               sans données externes
│   └── diagnostic_regressions.py  Spécification des deux régressions
│                                   de diagnostic (A.4) -- prêtes à
│                                   l'emploi, nécessitent les
│                                   données listées dans data/README.md
├── data/
│   ├── README.md              Sources exactes, liens de
│   │                           téléchargement, format attendu
│   └── raw/                   Fichiers bruts téléchargés (non
│                               versionnés, voir .gitignore)
└── references/                PDF des articles cités
```

## Périmètre du projet

Strictement limité au tronc commun (primaire + secondaire) et à
l'âge de spécialisation. L'enseignement supérieur est hors réforme,
utilisé uniquement comme variable de résultat (taux de diplômés,
diplômés STEM).

## Structure en trois parties

- **Partie 1** -- Diagnostic léger (littérature existante,
  Hanushek & Woessmann), pas de ré-estimation causale propre.
- **Partie 2** -- Benchmark de réformes (Pologne, Allemagne, France
  2018), graphe de notions KST, qualité des enseignants, coût.
- **Partie 3** -- Modèle prédictif (empirique + indice théorique
  $Q$ calibré par optimisation convexe), cible double PISA/TIMSS.

## Discipline exploratoire/confirmatoire

Point méthodologique central, à respecter dans tout le code ajouté
au dépôt : la construction du graphe et le réglage des modèles se
font exclusivement sur les cycles PISA/TIMSS **≤ 2018**. Les cycles
2022 et 2025 sont un holdout, touché **une seule fois**, une fois
toute spécification gelée. Voir `Plan.txt`, section "Analyse
coût-bénéfice" / discipline confirmatoire pour le détail.

## État d'avancement

Voir `TODO.md`. En résumé : le plan méthodologique est stabilisé,
le graphe pilote et les diagnostics sont codés et testés sur données
synthétiques, aucune donnée réelle n'est encore chargée.

## Usage de l'IA dans ce projet

Une partie de la revue de littérature, de la conception méthodologique
et de ce code a été assistée par IA (Claude). Chaque référence listée
dans `Liste_références.txt` doit être vérifiée contre la source
primaire avant citation dans le rapport final -- les références
marquées `[non vérifié]` ne l'ont pas encore été.
