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
