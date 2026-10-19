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

## Ajouts du 2026-10-19 (etat d'avancement PISA / TIMSS)

Fait
- PISA 2000-2025 assemble: data/processed/pisa_scores_long.csv (World Bank <= 2018 + sources
  secondaires 2022/2025 pour les pays OCDE). Les valeurs 2025 ne sont ancrees de facon
  independante que pour la France (maths 458, lecture 456, sciences 483).
- Tests confirmatoires maths/lecture/sciences executes une fois (spec v2, hash 01380f8d5cffac57;
  verrous forecasts/confirmatory_<matiere>.lock.json). L'AR(1) a la meme erreur de rang que la
  persistance dans les 6 comparaisons (2 plis par matiere): aucun gain observe.
- Previsions PISA 2028 figees: forecasts/pisa_<matiere>_2028_from_le2025.csv. France, rang
  median [p10-p90]: maths 23 [16-27], lecture 18 [13-21], sciences 21 [13-28]; P(top 10) <= 4 %.
- TIMSS G4 maths: tendances par sujet commun (run_crosswalk_trends.py); curriculum MIS EN OEUVRE
  par les almanacs enseignants 2019/2023 (extract_teacher_topics.py); prevu vs mis en oeuvre
  (run_intended_vs_implemented.py, table data/crosswalk_teacher_g4_math.csv).
- Climat disciplinaire PISA (fetch_pisa_discipline.py, data/processed/pisa_discipline_means.csv):
  2015 DISCLISCI (sciences), 2018 DISCLIMA (langue d'enseignement), 2022 DISCLIM (maths).
  France 38/38, 38/38, 32/37 (OCDE). Matieres differentes: PAS de tendance entre cycles.

Resultats a retenir (descriptifs)
- Le saut de couverture PREVUE de la France 2019->2023 (rang 1/52) n'apparait pas chez les
  enseignants (%avant: rang 18/52; Spearman entre pays -0,03). A traiter avec mefiance
  (hypothese de changement de maniere de repondre des coordinateurs, NON testee).
- A un cycle donne, le prevu predit le mis en oeuvre (Spearman prevu/%pas encore: -0,35 en 2019,
  -0,27 en 2023).

A faire
- [ ] Verifier quelques valeurs PISA 2025 (maths, lecture) contre l'annexe OCDE (403 aux scripts).
- [ ] Relire et geler data/crosswalk_g4_math.csv ET data/crosswalk_teacher_g4_math.csv.
- [ ] Rapport: tests A/B non aveugles; spec v2 commitee avant le premier run (commit 8dceeb1
      pour les maths); verifier par git log les dates des verrous lecture/sciences.
- [ ] Rapport: France TIMSS 2023, ~20 % d'eleves sans reponse enseignant (Omitted+Not administered),
      5,7 % en 2019; categorie "pas encore enseigne" non comparable 2019/2023 (2019 inclut
      "just introduced"); almanacs enseignants 2015 en PDF seulement.
- [ ] Rapport: climat disciplinaire = descriptif, hors modele; sens "valeur haute = meilleur
      climat" a confirmer dans le codebook; cycles 2000-2012 non traites (texte a largeur fixe).
- [ ] Prevision TIMSS 2027 (modele gele): non faite.
- [ ] Note de vie scolaire (DEPP): existence toujours a confirmer.
- [ ] Graphe KST: 11 des 20 sous-items TIMSS G4 non couverts; parametres IRT a renseigner.

## Verification PISA 2025 (2026-10-19) -- FAIT
- Valeurs 2025 recoupees avec une seconde source de presse reprenant les tableaux OCDE
  (Notes from Poland, Estonian World, Northern Voices): 13 pays en maths, 10 en lecture,
  12 en sciences, 0 ecart > 1 point; France 458/456/483 conforme.
- Moyenne simple des 38 pays du fichier: 463,1 / 460,9 / 481,9 contre OCDE publiee 463 / 461 / 482.
- Limite a ecrire dans le rapport: sources secondaires, annexes OCDE non lues (403 aux scripts).
