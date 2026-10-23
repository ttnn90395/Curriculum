# Décision de scope

Actée le 2026-10-04. Motif : le projet a accumulé des extensions
par accrétion sur plusieurs dizaines d'échanges sans jamais couper
explicitement -- cf. audit méthodologique dans `TODO.md`. Cette
décision remplace toute ambiguïté précédente. Elle peut être
révisée, mais par une décision écrite ici, pas par dérive.

## Cœur du rapport -- fait avec rigueur complète

1. **Partie 1** -- diagnostic léger (littérature existante, pas de
   ré-estimation causale)
2. **Benchmark de réformes** (Pologne, Allemagne) par contrôle
   synthétique -- donne le gain PISA attendu d'une réforme
3. **Graphe de notions maths + sciences seulement** (pas toutes
   matières, pas de fusion avec un graphe SEL)
4. **Partie 3, cible PISA en priorité** -- TIMSS reste une piste de
   robustesse secondaire, pas un deuxième modèle complet construit
   au même niveau d'effort. Si le temps manque, TIMSS est la
   première chose qu'on abandonne, pas PISA.
5. **Modèle empirique simple** (OLS/ridge/lasso/PLS, panel pays x
   cycle) -- le HLM multi-niveaux et les priors bayésiens
   informatifs restent documentés comme extensions possibles, pas
   construits par défaut
6. **Analyse coût-bénéfice** (Section 12) -- VAN, taux
   d'actualisation Quinet/Gollier, coût écologique

## Traité en registre descriptif, pas comme bras empirique séparé

- Diversification général/professionnel (Section 7) -- un
  paragraphe citant Hanushek, Schwerdt, Woessmann & Zhang (2017),
  pas un modèle
- Canal STEM -> high-tech -- gardé seulement s'il "marche"
  facilement en exploratoire ; abandonné sans drame sinon
- Qualité des enseignants (salaire, adéquation disciplinaire) --
  gardée comme section descriptive avec les deux diagnostics déjà
  codés, mais PAS étendue à une collecte de données enseignants
  dans les 9 pays "en profondeur"

## Hors périmètre de ce rapport -- extension future uniquement

- EMC/SEL (déjà acté en ouverture)
- Variable comportement / note de vie scolaire -- mentionnée comme
  piste, pas vérifiée ni construite
- Les 9 pays "en profondeur" avec sources nationales fines
  (DEPP/NCES/NEPS/etc.) -- **réduit à la France uniquement** pour
  ce rapport. Les sources des 8 autres pays restent documentées
  dans `data/README.md` pour un travail futur, mais ne sont pas
  collectées maintenant.
- Estonie en tant que cas quantitatif (absente de TIMSS) -- reste
  une référence qualitative (ProgeTiiger), pas un point de donnée
  du modèle

## Conséquence directe sur `data/README.md` et `TODO.md`

La Priorité 3 (sources nationales fines) de `data/README.md` est
reclassée "extension future, non bloquante" -- seule la ligne
France (DEPP) reste active pour ce rapport.

## Ajout du 2026-10-19 -- precisions de perimetre
- Climat disciplinaire PISA (2015, 2018, 2022): explore en registre DESCRIPTIF seulement
  (France vs OCDE par cycle). Il reste hors du modele de prevision et hors de la VAN.
  La matiere des cours differe selon le cycle: aucune tendance n'est calculee.
- Curriculum mis en oeuvre (almanacs enseignants TIMSS 2019/2023): utilise comme controle de
  coherence du curriculum prevu, pas comme variable du modele.
- Seule la prevision PISA 2028 (gelee dans forecasts/) est prospective; les tests A/B ne le sont pas.

## Ajout du 2026-10-23 -- extensions demandees explicitement (decision ecrite)
- Optimisation du curriculum et de la repartition des horaires sous contrainte de cout et de temps (module A et heures -> PISA via l'effet par heure, SPEC Amendements 5 a 7) : fait partie du coeur du rapport (Partie 2).
- Attractivite du corps enseignant (retenue et taux CAS, salaire relatif) : passe de descriptif a scenarios parametres sur l'elasticite [0,3 ; 2,0] (SPEC Amendement 6.3), France uniquement, jamais une prediction ponctuelle.
- Comportement : le climat disciplinaire PISA reste descriptif (ajout du 2026-10-19) ; la note de vie scolaire reste hors perimetre.
- Nivellement par le bas (bac, brevet) : France uniquement, serie temporelle, mesure independante du niveau (CEDRE, PISA) ; aucune comparaison d'examens entre pays (Precision de l'Amendement 7).
- Sources nationales fines : France uniquement, inchange.
- Comparaison internationale des couts (22 pays OCDE) : volet de l'analyse cout-benefice, deja realise, sans extension supplementaire.
