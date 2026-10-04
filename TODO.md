# TODO consolidé

## Bloquant -- à faire avant toute collecte de données

- [ ] **Couverture TIMSS 2023 par pays et par cycle.** Non résolu
      par recherche web (perte de structure du tableau à
      l'extraction). Télécharger la base internationale TIMSS 2023
      (R/SPSS/SAS, timss2023.org/data) et vérifier directement.
      Conditionne la liste finale de pays de tout le panel.
- [ ] **Cible du modèle Partie 3 : PISA et TIMSS en parallèle**
      (décidé). Construire les deux pistes, comparer l'ajustement
      comme test de cohérence du cadre (un indice curriculaire
      devrait mieux coller à TIMSS qu'à PISA si le cadre est
      cohérent).
- [ ] Statut exact du Royaume-Uni dans TIMSS (England seul confirmé
      deux fois ; pas d'Écosse/Irlande du Nord séparées trouvées).

## Avant de figer les features du graphe (conditionnent Phase 2)

- [ ] Exécuter `code/diagnostic_regressions.py` : diagnostic 1
      (g_{i,n} vs temps total) et diagnostic 2 (médiation
      qualité-enseignant / couverture) dès que les données sont
      chargées.
- [ ] Valider `code/pilot_knowledge_graph.py` contre le TIMSS 2023
      Mathematics Framework (liste de sujets officielle par grade)
      -- actuellement construit à dire d'expert, non confronté à
      une source externe.
- [ ] Étendre le graphe pilote aux sciences (actuellement maths
      seul, 20 notions) et, si le scope le permet, à la pensée
      computationnelle (PISA 2025, "Learning in the Digital World").

## Références à vérifier (texte intégral, pas juste citées)

- [ ] Gustafsson (2016) : r=0,70 confirmé, coefficient β=0,55
      **non confirmé** -- ne pas citer tant que non vérifié.
- [ ] Dolton & Marcenaro-Gutierrez (2011) : citation complète
      confirmée, élasticité salaire->compétence précise non trouvée.
- [ ] Référence exacte (auteurs) de Daus & Braeken (2018) --
      CONFIRMÉE : *Large-scale Assessments in Education* 6(1),
      DOI 10.1186/s40536-018-0054-1.
- [ ] Note de vie scolaire (France, 2006-2014, intégrée au DNB) --
      citée de mémoire, existence et modalités à confirmer (DEPP).
- [ ] Score PISA 2025 France en "computational problem solving" --
      résultats publiés le 8 sept. 2026, chiffre précis non trouvé.

## Couverture de données à vérifier pays par pays

- [ ] TALIS, participation au niveau primaire (jugée insuffisante
      par l'OCDE dans plusieurs pays en 2018).
- [ ] Classes préparatoires françaises : comptées comme
      établissements distincts dans ETER ?
- [ ] Équivalent Eurostat (spécialistes TIC) pour les pays OCDE
      hors Europe (Japon, Corée, Canada, Australie...).
- [ ] Granularité NEPS pour l'âge de bifurcation par Land
      (Allemagne).
- [ ] Équivalent NCES pour la qualification disciplinaire des
      enseignants (comparable à Villani-Torossian).

## Décisions méthodologiques déjà prises (ne pas rouvrir sans raison)

- Discipline confirmatoire/exploratoire : holdout temporel sur les
  cycles 2022/2025, exploration sur ≤ 2018.
- Indice $Q$ : perte de **rang**, pas perte quadratique -- $Q$ reste
  un outil descriptif (classement), n'alimente PAS directement la
  VAN (Section 9) ; la calibration macro utilise le modèle
  empirique cardinal.
- Canal diplômés STEM -> high-tech : reformulé via l'âge de
  bifurcation (Section 7, "capture des jeunes talents"), volet
  "manque d'info" qualitatif uniquement.
- Diversification général/professionnel : traitée en registre
  descriptif (Section 7), pas comme nouveau bras empirique.
- EMC/SEL : hors périmètre, en ouverture seulement.
- H3 (entrée en écoles sélectives) : abandonnée, places saturées.
- Benchmark interne France 2018 (Villani-Torossian) : traité comme
  qualitatif, pas de test causal valide avant PISA 2028-2031
  (t_impl de 5+ ans pour la formation initiale des enseignants).

## Non bloquant, scope potentiellement à couper

Voir `Plan.txt`, section "Limites" -- le projet a été audité comme
probablement trop large pour un seul rapport (cf. discussion sur
la dérive de scope). Décision de coupe à prendre explicitement
avant la rédaction finale, pas par accrétion continue.
