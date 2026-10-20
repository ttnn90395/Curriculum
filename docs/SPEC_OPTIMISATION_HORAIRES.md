# Specification : curriculum optimal a nombre d'heures donne, enseignants, budget

Statut : EXPLORATOIRE. Conception ecrite le 2026-10-20 AVANT tout calcul ; le commit horodate la conception.
Module de decision et de comptabilite sous hypotheses, pas une estimation causale.

## 1. Question
Etant donne un volume d'heures H, quel ensemble de notions enseigner (quel etat du graphe KST), comment repartir H
entre matieres, de combien de professeurs et de formation cela depend, et quel budget par poste (part de la mission
Enseignement scolaire) ?

## 2. Module A : KST optimal pour H heures (une matiere, un cycle)
- Graphe G = (N, E), arete p -> n : p prerequis de n. Un etat de connaissance valide K est un sous-ensemble ferme
  par les prerequis (downset).
- Variables : x_n in {0,1}. Maximiser sum_n w_n x_n  sous  sum_n tau_n x_n <= H  et  x_n <= x_p pour toute arete p -> n.
  (sac a dos avec contraintes de precedence ; 31 notions : resolution exacte par programmation lineaire en nombres entiers.)
- tau_n = temps de classe pour amener un eleve type a la maitrise de n, CONDITIONNELLEMENT a la maitrise des prerequis.
  Point cle (remarque du 2026-10-20) : tau_n n'est pas une difficulte. Une notion qui parait difficile mais qui s'appuie
  sur des bases solides peut avoir un tau_n faible ; une arete p -> n avec difficulte(p) > difficulte(n) n'est donc pas
  une anomalie. Les difficultes IRT TIMSS ne servent pas a valider les aretes.
- Variante A2 (profondeur) : t_n continu, maitrise q_n = 1 - exp(-t_n / tau_n), couplee aux prerequis par
  m_n = min(q_n, min_{p in pre(n)} m_p) ; objectif sum_n w_n m_n sous sum_n t_n <= H.
- Poids w_n : defaut = poids du cadre TIMSS 2023 G4 (part de l'aire de contenu divisee entre ses objectifs) ;
  alternatives : poids egaux ; poids de pertinence PISA. Le choix est une VARIABLE DE SENSIBILITE, pas une donnee.

## 3. Parametres : ce qui est connu et ce qui ne l'est pas
- Connus : graphe (31 notions, audite) ; horaires officiels par cycle et matiere (data/instruction_hours_fr_primary.csv) ;
  structure budgetaire par programme (data/budget_enseignement_scolaire_plf2026.csv, PLF 2026, a verifier).
- INCONNUS et aujourd'hui non observes : tau_n par notion ; q_n en fonction du temps ; reponse de la lecture au temps.
  Sources envisagees pour tau_n, a trancher avant calcul :
  (i) modele empirique : couverture implementee (almanachs enseignants) en fonction du volume horaire total entre pays et
      cycles (hypothese de l'utilisateur : l'ecart prevu-implemente reflete le temps) ; identifie au plus des
      elasticites par domaine, pas par notion ;
  (ii) variables PISA de temps d'apprentissage par matiere (minutes hebdomadaires) ;
  (iii) elicitation didactique avec source publique.
  Tant qu'aucune n'est retenue, les resultats portent sur des scenarios tau_n = tau0_n * m, m dans [0.5, 2], et sur la
  liste des notions presentes dans l'optimum sur tous les tirages (solution robuste).

## 4. Module B : repartition des heures entre matieres
Maximiser sum_s V_s(H_s)  sous  sum_s H_s = H_tot (864 h par an) et planchers statutaires. V_s vient du module A pour
maths (et sciences) ; il n'existe aucun graphe pour le francais : V_lecture reste inconnue. B n'est donc execute qu'en
scenarios de transfert (par exemple +-1 h hebdomadaire entre maths et une autre matiere), pas en optimum global.

## 5. Module C : enseignants
- Premier degre : professeurs generalistes. Le nombre d'ETP depend du nombre de classes et du service, pas de la repartition
  entre matieres. Redistribuer les horaires change la FORMATION a prevoir (heures x enseignants a former), pas l'effectif.
- Second degre : ETP_s = somme sur niveaux (classes_l x heures_{s,l}) / service_s. Les services (18 h, 15 h, etc.)
  sont a verifier sur source officielle avant usage.
- Stock d'enseignants a former : besoin de donnees de profil (formation initiale scientifique ou litteraire) ; non collectees.

## 6. Module D : budget
Delta budget = somme des Delta ETP x cout complet par ETP + heures de formation x cout + manuels et materiel.
Part de chaque programme (P140, P141, P139, P214, P230) avant/apres ; part de P140+P141 dans la mission
(70.41 % au PLF 2026). Choix a documenter : avec ou sans CAS Pensions. Retard d'implementation (formation, manuels)
distinct du lag x, deja prevu au plan. Les cout-benefices restent ceux de la Section 9 du plan.

## 7. Limites declarees
- Aucune validation par resultats : les tau_n ne sont pas identifies ; les sorties sont conditionnelles aux scenarios.
- w_n arbitraire : sensibilite obligatoire.
- Un optimum a H fixe n'est pas un effet causal sur PISA ; le lien notions -> score reste a la Partie 3.
- Donnees budgetaires : PLF 2026, pas la LFI 2026 adoptee ; a remplacer.

## 8. Prochaines etapes (ordre)
1. Verifier le budget sur le document primaire et obtenir la LFI 2026 ; details des actions de P140.
2. Cout complet d'un ETP (primaire, secondaire), services reglementaires, effectifs de classes.
3. Choisir la source de tau_n (section 3) ; coder le module A (ILP) avec les scenarios.

## 3bis. Identification de tau_n par identite budgetaire (amendement du 2026-10-20, avant toute donnee)
Origine : remarque de l'utilisateur, les heures par matiere sont publiees pour tous les pays.
Ces heures donnent le BUDGET H_c d'une matiere dans le pays c, pas sa repartition par notion. Elles n'identifient tau_n
que sous une hypothese : les heures de maths d'un pays servent a couvrir les notions de son programme, a un cout tau_n
commun a tous les pays :  H_c = alpha + sum_n tau_n x_{c,n} + eps_c.
- x_{c,n} : couverture prevue (questionnaire curriculum TIMSS, codee 0 / 0.5 / 1, appariement par crosswalk).
- H_c : heures cumulees de mathematiques de la 1re a la 4e annee. Sources : Eurydice 2024/25 (temps recommande, pays
  europeens), Education at a Glance (OCDE), TIMSS questionnaires ecole/enseignant (heures reellement enseignees).
  Les trois sont des mesures distinctes (prevu / implemente) et ne sont pas melangees.
- Estimation : moindres carres non negatifs, alpha >= 0 ; incertitude par bootstrap sur les pays.
- Specification primaire : 3 domaines (Nombre ; Mesure et geometrie ; Donnees). Secondaire, exploratoire : 15 notions apparies.
Diagnostics fixes AVANT lecture des donnees :
- D1 : R2 predictif en laissant un pays de cote, compare a un nul par permutation (1000 permutations des lignes de x entre
  pays). Identification declaree ECHOUEE si le R2 observe est sous le 95e percentile du nul.
- D2 : holdout temporel. Ajuster sur 2015 et 2019, predire 2023, une seule fois ; erreur absolue moyenne comparee a celle de
  la prediction par la moyenne des pays.
- D3 : conditionnement de la matrice X rapporte ; au-dela de 30, seule la specification a 3 domaines est conservee.
- D4 (descriptif) : alpha + sum_n tau_n x_{FR,n} compare aux heures reelles de la France, France exclue de l'ajustement.
Regle : tau_n n'est interprete ni utilise dans le module A que si D1 et D2 passent ; sinon retour aux scenarios (section 3).
Limites : les heures de maths contiennent revisions, evaluations et temps mort (alpha n'absorbe que la part constante) ;
tau est un cout moyen, l'heterogeneite entre pays (niveau des eleves, taille des classes, langue d'enseignement) n'est pas
modelisee ; la couverture prevue est une declaration de coordinateur national, bruitee (environ 11 % de bascules entre
cycles) ; 27 pays OCDE seulement en 4e annee, puissance faible pour 15 parametres.

## 3ter. Hypothese H_prop : tau proportionnel a la difficulte (amendement du 2026-10-20, avant toute donnee)
Proposition de l'utilisateur : tau_n proportionnel a la difficulte IRT. Retenue comme HYPOTHESE TESTABLE, pas comme donnee.
Reserve de fond : la difficulte mesuree en 4e annee est observee APRES enseignement ; plus une notion a ete enseignee
longtemps, plus elle est maitrisee, donc plus sa difficulte mesuree est basse (signe possiblement inverse de tau).
tau_n est un temps conditionnel aux prerequis ; la difficulte melange complexite et exposition.
Forme : tau_t = kappa * g(b_t), b_t = difficulte poolee par sujet du crosswalk (data/processed/difficulty_by_objective_g4.csv
via la colonne crosswalk_topic du cadre), g fixee parmi trois familles : g_exp(b) = exp(b - moyenne), g_lin(b) = b - min(b) + 1,
g_rang(b) = rang de b. Les trois sont executees ; l'optimum du module A est rapporte pour chacune.
Test (reutilise D1 et D2 de la section 3bis) : H_c = alpha + kappa * sum_t g(b_t) x_{c,t}, kappa >= 0 libre, alpha >= 0.
- P1 : R2 predictif en laissant un pays de cote, compare au nul par permutation (95e percentile) ET au modele libre a 3 domaines.
- P2 : holdout temporel 2015 + 2019 -> 2023, une seule fois ; b_t gele a sa valeur 2023.
- P3 : rejet immediat si kappa estime vaut 0 (borne) ou si le signe de la relation est inverse.
H_prop est retenue seulement si P1 et P2 passent ; sinon, scenarios (section 3).
Limite de couverture declaree : seulement les sujets a difficulte fiable (>= 5 items par objectif, seuil post hoc deja declare),
soit environ 16 notions sur 31. n06/n07 (fractions, 1 item) et les notions sans item TIMSS (n01, n09 a n20) sont hors H_prop :
le module A ne s'y applique qu'au sous-graphe couvert, ou avec une autre source de tau.

## 3quater. Mesures de H disponibles et pre-requis (amendement du 2026-10-20, apres inspection des fichiers d'heures, AVANT toute regression)
- TIMSS 2019, exhibit 12.2 : heures de maths enseignees PAR AN en 4e annee (implemente ; directeurs et enseignants).
  Pas de cumul des annees 1 a 4. Variante V_T : H_c = heures annuelles de 4e annee, sans multiplication par 4 (evite une hypothese).
  Couverture x_{c,n} pour V_T : questionnaire curriculum 2019, G4. Le codage 2019 n'est valide en G4 que pour le code 1
  (tous ou presque) : x = 1 si code 1, sinon 0 ; sensibilite avec 0.5 pour le code 2.
- Eurydice 2024/25 : heures RECOMMANDEES par annee et par matiere (38 systemes). Variante V_E : H_c = cumul des annees 1 a 4
  si les tableaux donnent l'annee par annee ; sinon V_E est abandonnee (pas de conversion depuis des tranches). Couverture : cycle 2023.
- V_T (implemente) et V_E (prevu) ne sont jamais melangees ni mises en commun.
- Pre-requis de puissance : la regression n'est executee que si au moins 25 pays ont a la fois heures et couverture ; sinon,
  rapport descriptif seulement.
- Drapeaux TIMSS (r, s) : conserves en analyse principale ; sensibilite sans les pays marques 's' ; legende lue sur le fichier avant usage.
- Ponderation : non ponderee en principal ; sensibilite ponderee par 1 / ES^2.
- Recoupement de lecture deja observe : France 182 h/an (ES 2.5, TIMSS 2019) contre 180 h officielles (5 h x 36 semaines).

## 3quinquies. Revision de D2 (amendement du 2026-10-20, cause : disponibilite des donnees, pas des resultats ; AVANT toute regression)
- Constat : les heures de maths TIMSS en 4e annee sont disponibles pour 2015 (exhibit 9.1) et 2019 (exhibit 12.2). Aucun exhibit
  equivalent n'a ete trouve pour 2023. D2 tel qu'ecrit en 3bis (ajuster 2015 + 2019, predire 2023) n'est pas executable.
- D2' (remplace D2 tant que 2023 est indisponible) : ajuster sur 2015 seule, predire 2019, UNE seule fois (sens temporel avant),
  pour les pays ayant heures et couverture en 2019 ; erreur absolue moyenne comparee a celle de la prediction par la moyenne
  des heures 2015. Si des heures 2023 deviennent disponibles, D2 d'origine est execute EN PLUS, sans remplacer D2'.
- Information deja vue avant cette revision : valeurs descriptives des heures 2015 et 2019 pour France, Allemagne, Pologne,
  Finlande, Japon, Coree (stables d'un cycle a l'autre, ex. France 193 h puis 182 h). Aucun resultat de regression.
- D1 inchange : sur 2019 (V_T), 54 pays communs heures et couverture ; Norvege, Afrique du Sud et Turquie (note 5, 5e annee),
  l'Angleterre (heures absentes) et les participants benchmarking sont exclus ; la moyenne internationale n'est pas un pays.
- Regle d'usage de tau_n : D1 ET D2' doivent passer (identique a 3bis avec D2 remplace par D2').

## 3sexies. Ensemble de sujets de la regression d'identification (amendement du 2026-10-20, avant tout resultat reel)
Constat (liste des sujets des fichiers crosswalk, aucune sortie de modele) : le fichier primaire ne contient que les 7 sujets
a confiance elevee (N1, N2, N4, N7, G2, G3, G6) ; le domaine Donnees y est vide. G2 n'a pas de donnees en 2015.
Decision : la specification utilise crosswalk_topic_values_robustesse.csv (confiance elevee + moyenne ; G1 'low' exclu par le gel),
privee de G2 faute de 2015, soit 13 sujets : Nombre N1-N7 (7), Mesure et geometrie G3-G6 (4), Donnees D1-D2 (2).
Raison : disponibilite des donnees et domaine Donnees non vide, pas un resultat. H_prop : sujets a difficulte fiable parmi ces 13.
Sensibilite S4 : 6 sujets a confiance elevee communs aux trois cycles (N1, N2, N4, N7, G3, G6), 2 domaines (Nombre ; Mesure et geometrie).
D3 et la regle D1 + D2' inchangees. Une conclusion negative sur S4 seule ne tranche pas (puissance plus faible, 6 sujets).
