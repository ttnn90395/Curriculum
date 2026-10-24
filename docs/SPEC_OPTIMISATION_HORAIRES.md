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


## Amendement 4 (comparaison internationale, taille de classe) -- exploratoire, 22 octobre 2026

Objet: etendre de facon exploratoire la couverture de la comparaison internationale (code/cross_country_net_cost.py) aux pays ayant les heures statutaires et le salaire mais pas la taille de classe (NLD, NOR, NZL). Ecrit AVANT tout calcul d'imputation.

Regle: N_hat_i = STR_i x m, ou STR_i est le ratio eleves/personnel enseignant de l'OCDE (flux DF_UOE_NF_PERS_STR, 1er cycle du secondaire, public si disponible, annee la plus recente) et m la mediane, sur les 22 pays complets, de N_j / STR_j. Les filtres exacts du flux sont fixes apres lecture de son profil et committes avant le calcul.

Validation: erreur relative |N_hat_j - N_j| / N_j en leave-one-out (m recalcule sans le pays j) sur les 22 pays. Critere d'acceptation fixe a l'avance: mediane des erreurs <= 15 % ET 90e centile <= 30 %. Si le critere echoue, aucune imputation n'est utilisee et le resultat est rapporte comme non concluant.

Presentation: pays imputes marques et exclus des rangs, medianes et chiffres principaux (qui restent calcules sur les 22 pays complets). Pays sans heures statutaires (DNK, SWE, IRL, PER): non imputes, aucune route de substitution. Aucune autre variante.


### Precision de l'Amendement 4 (filtres) -- avant calcul

STR: flux DSD_EAG_UOE_NON_FIN_PERS@DF_UOE_NF_PERS_STR, MEASURE STU_PERS, UNIT_MEASURE ST_TCHR, EDUCATION_LEV ISCED11_2; destination INST_EDU_PUB si disponible, sinon INST_EDU; annee la plus recente par pays (2022-2024). N: flux CLS, ISCED11_2, memes regles de destination et d'annee que cross_country_net_cost.py. Pays de reference: les 22 pays de data/processed/cross_country_net_cost.csv disposant de N et de STR. 90e centile au rang le plus proche (indice ceil(0.9 n)). Pays imputables: NLD, NOR, NZL uniquement.


## Amendement 5 (curriculum optimise: horaires par matiere sous contraintes de temps et de cout) -- exploratoire, 23 octobre 2026

Ecrit AVANT toute collecte de preuves et tout calcul d'optimisation. Statut: exploratoire; aucun resultat n'est un pronostic de rang.

**5.1 Cible.** Edition de reference: PISA 2025 (dossier du ministere du 08/09/2026; scores de la France: mathematiques 458, lecture 456, sciences 483; variation 2022-2025: -16, -18, -4 points). Critere principal: RANG GLOBAL = rang de la France parmi les pays de l'OCDE participants de PISA 2025 disposant des trois scores publies, sur la moyenne simple des trois domaines. L'OCDE ne publie pas de tableau des nations: ce rang est reconstruit a partir des scores par pays du Volume I (source a identifier; a defaut, le rang n'est pas calcule et seuls les points sont rapportes). Criteres secondaires: points par domaine. Les autres pays sont gelés a leurs scores 2025; un gain en points est converti en rang en deplacant le score de la France sur cette distribution gelee. Les deux moyennes OCDE trouvees sont divergentes (486/470/466 a echantillon constant de 24 pays selon le document DEPP; 482/463/461 selon un site de presse): aucune n'est utilisee.

**5.2 Discipline confirmatoire.** Aucun parametre n'est ajuste sur PISA 2022 ni 2025 (zone confirmatoire du projet). Ces scores servent de point de depart et de distribution gelee, jamais d'apprentissage.

**5.3 Variables de decision et contraintes.** Horaires hebdomadaires h(m,n) par matiere m et niveau n (elementaire CP-CM2; college 6e-3e; lycee general et technologique 2nde-terminale; lycee professionnel; filieres technologiques), horaires actuels = arretes officiels (parametres sources, statut verified/to_verify). Bornes: |dh| <= 1 h par semaine par matiere et niveau (domaine de validite des estimations causales, aucune extrapolation) et plancher legal par matiere a fixer. Temps: somme hebdomadaire des heures-eleves par niveau <= plafond; scenarios: plafond = actuel (reallocation pure), +1 h, +2 h au total. Cout: budget supplementaire <= B pour B dans {0, 250 M EUR, 500 M EUR, 1 Md EUR}, hors CAS et avec CAS; cout d'une heure hebdomadaire ajoutee = modele deja etabli (college 295, elementaire 322, lycee GT 120 a 153 M EUR hors CAS); reallocation a heures totales constantes = cout nul au premier ordre (differences de service agrege/certifie non modelisees, a declarer).

**5.4 Effet des heures.** Gain en points du domaine d = somme sur (m,n) de beta(m,d,n) x dh(m,n), beta = effet causal en ecart-type d'eleve d'une heure hebdomadaire supplementaire, estime par meta-analyse a effets aleatoires (DerSimonian-Laird) des etudes retenues selon la regle: (i) variation exogene d'horaire (experience, discontinuite, difference de differences autour d'une reforme, variation intra-eleve ou intra-etablissement entre matieres); (ii) test standardise; (iii) publication evaluee par les pairs ou document de travail institutionnel; (iv) population scolaire du niveau concerne. Pour chaque paire (matiere ajoutee, domaine PISA), au moins 3 estimations independantes sont requises, sinon l'effet est declare non estimable et la paire est exclue de l'optimisation et rapportee. Effet transversal entre matieres = 0 sauf estimation retenue. Conversion ecart-type d'eleve en points: ecart-type PISA 2025 publie (a lire dans le Volume I). Linearite dans la plage |dh| <= 1 h; rendements decroissants non modelises (declare). Le module A ne modifie pas beta: il designe les notions prioritaires dans les heures de maths (noyau robuste), rapporte qualitativement.

**5.5 Incertitude et decision.** Monte Carlo de 10 000 tirages, graine 20261023, beta tire dans la distribution predictive de la meta-analyse (tau2 inclus); sorties: mediane et intervalle 5-95 % du gain en points et du rang, probabilite de gagner au moins 1 place. Un curriculum est rapporte comme « soutenu » seulement si P(gain moyen des trois domaines > 0) >= 80 %; sinon « non demontre ». Optimisation lineaire du gain moyen sous les contraintes 5.3, repetee sur chaque tirage; sont rapportes la solution mediane, la frequence de chaque allocation et les prix ombres du temps et du budget.

**5.6 Volet comportement (descriptif).** Indicateurs: indice de climat de discipline PISA et enquete de climat scolaire de la DEPP (RERS 2.15 et 2.16). Associations non causales climat-score entre pays. Le comportement n'entre dans l'optimisation que si une estimation causale de l'effet d'une variable curriculaire sur le comportement satisfait la regle 5.4; sinon il reste descriptif, comme prevu par SCOPE.md.

**5.7 Volet nivellement par le bas (bac, brevet; descriptif).** Taux de reussite et mentions du bac (general, technologique, professionnel) et du brevet, 1995-2025, compares aux tendances de mesures independantes des examens (PISA, CEDRE, evaluations nationales, TIMSS) sur la meme periode; mesure = ecart de tendance en ecart-types (z des taux contre z des scores). Facteurs de confusion a nommer (reforme du bac 2021 et controle continu, changements de bareme, composition de la population). Aucune inference causale.

**5.8 Volet attractivite.** (a) Cotisation employeur CAS Pensions: cout budgetaire sans effet sur le net de l'enseignant; chiffrage de la hausse 74,28 % -> 78,28 % (2025) -> 82,28 % (2026, source unique) sur l'assiette derivee. (b) Retenue salariale (11,10 %, 2023-2026): effet direct sur le net; simulation du net de l'enseignant rapporte au net moyen avec Taxing Wages (22 pays deja calcules). (c) Attractivite: elasticite de l'offre d'enseignants au salaire relatif tiree d'etudes causales selon la regle 5.4 (au moins 3 estimations, sinon descriptif); indicateurs france: rapport candidats/postes aux concours (CAPES, CRPE) et postes non pourvus (DEPP, ministere), a collecter. Resultat en fourchette, jamais en valeur ponctuelle.

**5.9 Ordre d'execution.** (1) cet amendement committe; (2) tables de preuves (data/evidence_*.csv) avec source, extraction et statut, committees avant l'optimisation; (3) code committe avant execution; (4) execution. Toute variante apres coup = nouvel amendement presente comme exploratoire.

## Amendement 6 — Règles de décision après collecte des preuves (pré-enregistré avant toute optimisation)

Statut : rédigé après la collecte de `data/evidence_instruction_time.csv`, `data/evidence_teacher_supply.csv` et `data/evidence_pisa2025.csv`, avant tout calcul d'optimisation. Exploratoire.

### 6.1 Référence PISA 2025
- Moyenne de référence principale : moyenne de tous les membres de l'OCDE publiée dans le Volume I (maths 463, lecture 461, sciences 482).
- Sensibilité : moyenne DEPP sur 24 pays comparables (470, 466, 486). Les deux sont rapportées, aucune n'est choisie après coup.
- Rang global : rang de la France parmi les pays et économies de l'annexe I.B1.2 du Volume I, calculé sur la moyenne simple des trois domaines, et rang par domaine. Le rang est un indicateur descriptif ; l'optimisation cible les points de score, pas le rang.
- Tant que les tableaux annexes de maths et de lecture ne sont pas versés dans `data/evidence_pisa2025.csv` (ligne P11), aucun rang n'est annoncé.

### 6.2 Effet des heures d'enseignement
- La règle 5.4 (au moins 3 estimations indépendantes par couple matière x domaine) n'est pas satisfaite : les études disponibles donnent des effets groupés par heure hebdomadaire.
- Décision : un effet commun theta par heure hebdomadaire et par matière, estimé par méta-analyse à effets aléatoires sur les estimations indépendantes : E01 (Lavy), E06 (Cattaneo et al., heures officielles, préférée à E05 pour éviter le double comptage), E07 à E09 comptées comme une seule étude (forme réduite, signalée), et Rivkin-Schiman (E10) si extraite avant calcul.
- Aucun classement des matières par rendement n'est revendiqué. L'effet d'une heure est attribué au domaine PISA de la matière enseignée (français vers lecture, mathématiques vers maths, sciences vers sciences), sans effet croisé en base. Les effets croisés de Huebener et al. (Table 5) servent uniquement en sensibilité.
- Sensibilités déclarées : (a) rendements décroissants par paliers (Lavy, Table 3 catégorielle) ; (b) effet par filière (Cattaneo, Table 2 : 0,038 / 0,060 / 0,080 selon la filière) ; (c) effet réduit de moitié (cas des pays en développement, E04, comme borne basse prudente).
- Conséquence assumée : sans effet propre à chaque matière, l'optimisation des horaires ne peut pas affirmer qu'une matière est plus rentable qu'une autre. Elle porte sur le volume total d'heures, sa répartition entre niveaux et filières, et son coût.

### 6.3 Attractivité du corps enseignant
- Aucune élasticité française n'est disponible. L'élasticité des candidatures au salaire relatif est traitée comme un paramètre de scénario sur [0,3 ; 2,0] (S01 à S04), jamais comme une prédiction ponctuelle.
- L'effet de la qualité des entrants sur les scores est borné à zéro comme scénario central (S08), avec un scénario positif à titre de sensibilité.
- La retenue salariale (11,10 %) et le taux CAS employeur (74,28 / 78,28 / 82,28 %) sont traités séparément : la retenue modifie le net du salarié, le taux CAS modifie le coût employeur sans modifier le net. L'effet sur l'attractivité ne passe que par le salaire relatif net.

### 6.4 Équité
- Les effets sont rapportés séparément pour le bas et le haut de la distribution quand l'étude le permet (E07 à E09 : les élèves faibles ne bénéficient pas ; E05/E06 : filières). Aucune recommandation ne repose sur la seule moyenne.

### 6.5 Ce qui reste interdit
- Aucune variante de l'estimateur ni de la sélection des études n'est ajoutée après avoir vu les résultats. Toute étude ajoutée après ce commit est signalée et son impact rapporté avec et sans elle.

## Amendement 7 — Difficulté des examens nationaux rapportée au programme, pour l'ensemble des pays (pré-enregistré avant tout codage de sujets)

Statut : rédigé avant tout codage d'énoncés et avant tout calcul. Exploratoire. Complète l'Amendement 5 (volet « nivellement par le bas ») et l'Amendement 6.

### 7.1 Objet
Mesurer, pour chaque pays et chaque année d'examen national de fin de cycle disposant d'un barème public, ce que l'examen exige réellement, rapporté au programme officiel, puis le comparer au taux de réussite et au niveau mesuré indépendamment (CEDRE, PISA, TIMSS).

### 7.2 Périmètre
- Pays : tous les pays pour lesquels existent à la fois (i) un programme officiel projetable sur le graphe de notions du module A, (ii) un examen national de fin de cycle avec sujets et barème publics sur au moins deux années distantes d'au moins 10 ans. La liste est produite par un inventaire (`data/exam_inventory.csv`, statut par pays) committé avant le codage. Un pays absent de la liste est exclu pour absence de données, jamais pour son résultat.
- Examens : épreuves nationales écrites uniquement. Le contrôle continu et les épreuves notées localement sont hors barème national : leur part dans la note finale est rapportée à côté, jamais imputée.

### 7.3 Indices (définis avant calcul)
- I1, exigence de contenu : nombre de notions de l'ensemble minimal qui permet d'atteindre la note de passage d'après le barème, avec le graphe de prérequis (fermeture par prérequis). Problème de sac à dos : minimiser le nombre de notions (fermées par prérequis) sous la contrainte de points obtenus supérieurs ou égaux au seuil. Profondeur maximale dans le graphe rapportée à côté.
- I2, couverture du programme : part des notions du programme évaluées, pondérée par les points du barème.
- I3, indulgence de notation : écart entre note moyenne observée et note moyenne attendue d'après le barème pour une population d'un niveau mesuré par l'évaluation indépendante. Calculé uniquement quand la distribution des notes est publique.
- Les trois indices sont rapportés séparément, aucun indice composite.

### 7.4 Règles de codage
- Allocation des points : les points d'une question sont répartis à parts égales entre les notions qu'elle mobilise (règle unique, fixée ici). Sensibilité : allocation sur la seule notion la plus profonde.
- Exercices au choix : l'ensemble atteignable est celui qui minimise I1 parmi les choix autorisés par la consigne.
- Codage par deux codeurs indépendants (un humain, un modèle de langage utilisé comme codeur supplémentaire, jamais comme arbitre). Accord inter-codeurs rapporté (kappa) ; seuil d'usage fixé à kappa supérieur ou égal à 0,6 sur la correspondance question-notions, sinon l'indice est rapporté comme non fiable.
- Projection des programmes étrangers sur l'échelle commune : table de correspondance publique (`data/curriculum_mapping.csv`), committée avant le codage des sujets, avec statut par ligne (mapping direct, partiel, absent). Les notions sans correspondance sont comptées comme non couvertes et rapportées.

### 7.5 Analyse
- Comparaisons dans le temps au sein d'un pays (principal) et entre pays (secondaire, soumise aux limites de projection).
- Lecture pré-enregistrée : si I1 est stable ou baisse pendant que le taux de réussite monte et que le niveau mesuré baisse, cela est compatible avec une indulgence accrue ou une demande allégée ; I3 distingue les deux quand il est disponible. Aucune conclusion causale.

### 7.6 Interdits
- Pas de recodage ni de nouveau mapping après avoir vu les indices. Tout changement est un nouvel amendement daté, rapporté avec et sans.

### Précision de l'Amendement 7 (périmètre effectif, pré-enregistrée avant tout codage)

Inventaire du dépôt (data/processed/inventory_repo.txt) : la base de programmes par pays provient des questionnaires de curriculum TIMSS (2015, 2019, 2023, 4e et 8e années). Le graphe de notions avec difficulté IRT n'existe que pour les mathématiques de 4e année (19 notions). Il n'existe pas de programmes de fin de lycée par pays ni de barèmes d'examens étrangers dans le dépôt.
- Examens de fin de lycée (bac et équivalents) : comparaison entre pays hors périmètre tant qu'un amendement n'a pas ajouté une base de programmes à ce niveau. Seule la série temporelle française (programme français) est dans le périmètre.
- Examens de fin de collège : dans le périmètre uniquement après construction et validation d'un graphe de notions de 8e année à partir des curricula TIMSS 8e année, selon les mêmes critères de fiabilité que le graphe de 4e année. Cette construction fait l'objet d'un amendement ultérieur.
- Aucun résultat « tous pays » n'est annoncé pour les examens. Les comparaisons entre pays restent limitées aux contenus prévus (TIMSS), sans examen.

## Amendement 8 — Scénarios d'heures hebdomadaires, gain PISA et coût (pré-enregistré avant exécution de code/optimise_hours.py)

Statut : exploratoire. Entrées : méta-analyse de l'effet par heure (Amendement 6.2, data/processed/meta_theta.*), coûts d'une heure hebdomadaire supplémentaire par classe (note comparaison internationale, vérifiés : collège 295 M€ hors CAS / 443 M€ avec CAS ; élémentaire 322,4 / 508,4), grilles horaires (data/instruction_hours_fr_*.csv).

### 8.1 Modèle
- Gain sur le domaine PISA d d'une heure hebdomadaire supplémentaire dans la matière associée : sigma x theta, où sigma est l'écart-type des scores individuels PISA (valeur centrale 100, convention de l'échelle ; sensibilité 90) et theta ~ N(theta_RE, SE^2 + tau^2) (distribution prédictive de la méta-analyse, k = 3 études).
- Correspondance matière-domaine : français vers lecture, mathématiques vers mathématiques, SVT, physique-chimie et technologie vers sciences. Les autres matières n'ont pas d'effet direct sur un domaine PISA dans le scénario de base. Gain sur la moyenne des trois domaines = moyenne des trois gains.
- Monte-Carlo : 20 000 tirages, graine 20261023. Intervalles à 5 et 95 %.

### 8.2 Périmètre et hypothèses de timing
- Seul le collège porte un effet PISA dans ce modèle : les élèves de 15 ans sont en 3e ou en seconde, et aucun coût séparé de la seule seconde n'est disponible. Élémentaire et lycée : coût rapporté, aucun gain PISA revendiqué faute de preuve sur l'effet cumulé.
- T2 (central, conservateur) : l'heure est ajoutée dans les quatre niveaux du collège, coût complet, effet theta une seule fois (pas de cumul sur les années). T1 (borne basse du coût) : l'heure n'est ajoutée qu'en 3e, coût égal à un quart du coût collège (hypothèse d'effectifs de classes égaux entre niveaux), effet theta. T1 et T2 sont toujours rapportés ensemble.

### 8.3 Scénarios
- +1 h hebdomadaire de mathématiques, de français ou de sciences au collège ; +1 h de chacune des trois matières.
- Réallocation à coût nul de 1 h de LV2 vers les mathématiques au collège (T2), avec une fuite (« spillover ») f de la perte sur chacun des trois domaines, f dans {0 ; 0,25 ; 0,5}, exprimée en fraction de sigma x theta. Ce balayage est un paramètre, pas une preuve : les effets croisés de Huebener et al. (Table 5) n'ont pas la même unité et ne sont pas utilisés. Coûts de reconversion des enseignants hors périmètre.
- Contrainte de temps : volume hebdomadaire total de l'élève plafonné à 30 h (collège actuel : 26 h). Aucun scénario ne dépasse 29 h.

### 8.4 Ce que le modèle n'est pas
- Avec un seul effet theta commun à toutes les matières, le « classement » des matières par rendement est trivial (égalité). L'optimisation se réduit à un rapport coût-efficacité (M€ par point de la moyenne des trois domaines) et à l'effet de la réallocation. Aucune matière n'est déclarée plus rentable qu'une autre.
- Les intervalles reflètent l'incertitude sur theta, pas l'incertitude de modèle : extrapolation d'effets mesurés à la marge (Lavy, Cattaneo, Huebener) à une hausse de 1 h par semaine au collège entier.
- Une réallocation qui augmente un score PISA en retirant des heures de langues, d'arts ou d'EPS ne vaut pas recommandation : les objectifs hors PISA ne sont pas valorisés par ce modèle.
- Aucune analyse d'équité : les effets sont plus forts pour les élèves et filières forts (Amendement 6.4).

### 8.5 Interdits
- Aucun changement de sigma, de la distribution de theta, des hypothèses T1/T2 ou des scénarios après avoir vu les sorties. Tout ajout est un nouvel amendement, rapporté avec et sans.

## Amendement 9 — Attractivité du corps enseignant : retenue, taux CAS, salaire brut (pré-enregistré avant tout calcul)

Statut : exploratoire, France uniquement (SCOPE.md, ajout du 2026-10-23). Scénarios paramétrés, jamais une prédiction ponctuelle.

### 9.1 Trois leviers distincts
- L1, hausse du salaire brut de x % : le net du salarié augmente de x % x (net/brut) en relatif au brut, le coût employeur augmente de x % du brut multiplié par (1 + taux CAS) avec CAS, ou de x % du brut hors CAS.
- L2, baisse de la retenue salariale (part salarié de la cotisation pension, 11,10 % du traitement indiciaire) de d points : le net augmente de d points du brut, le brut est inchangé. Coût hors CAS : nul pour la mission budgétaire. Coût avec financement du compte pensions : d points du brut, car le produit de la retenue disparaît. Les deux périmètres sont rapportés.
- L3, variation du taux CAS employeur : aucun effet sur le net, donc aucun effet attendu sur l'attractivité. Il ne modifie que la présentation des coûts « avec CAS » ; il est rapporté pour ne pas confondre transfert comptable et gain de pouvoir d'achat.
- Les gains nets sont rapportés en euros de net par euro de coût dans chaque périmètre, ce qui permet de comparer L1 et L2.

### 9.2 Effet sur l'offre
- Variation relative du salaire net rapporté à l'alternative (net moyen du pays, rapport net enseignant / net moyen déjà calculé, data/processed/cross_country_net_cost.csv) : delta = variation de net en %.
- Variation des candidats présents : epsilon x delta, avec epsilon dans {0,3 ; 1,0 ; 2,0} (bornes des estimations S01 à S04, data/evidence_teacher_supply.csv ; une seule étude anglaise, aucun résultat français).
- Candidats supplémentaires admis : au taux moyen d'admission par perimetre (premier degré 37,4 % ; second degré 24,8 %, data/evidence_attractivite_fr.csv A04/A02 et A12/A10). Sensibilité : moitié de ce taux pour des candidats marginaux. Réduction des postes non pourvus plafonnée au nombre de postes non pourvus observé (premier degré environ 637 en 2025 par différence ; second degré 12 244 postes moins 11 121 admis = 1 123).
- Qualité des entrants : effet nul sur les scores en scénario central (S08), jamais ajouté au calcul des points PISA de l'Amendement 8.

### 9.3 Grille
- Hausses de net : +1 %, +5 %, +10 %. Leviers L1 et L2 (pour L2, d est déduit pour obtenir le même gain de net). Les deux périmètres de coût, les deux degrés.
- Masse salariale : coûts moyens par catégorie hors CAS du RAP 2025 (premier degré 48 944 euros, second degré 52 248 euros) multipliés par les effectifs en équivalent temps plein de data/parameters_teachers_cost.csv ; si l'effectif manque dans ce fichier, le scénario n'est pas calculé et l'absence est rapportée.

### 9.4 Interdits
- Aucune élasticité n'est ajoutée ni retirée après avoir vu les sorties. Toute étude supplémentaire est un nouvel amendement, rapporté avec et sans.
- Aucune conclusion sur l'effet du taux CAS sur l'attractivité (L3) : un transfert comptable n'est pas un gain de pouvoir d'achat.

## Amendement 10 — Hausse ciblée sur les entrants (pré-enregistré avant exécution de code/attractivite_cible.py)

Statut : exploratoire, France uniquement. Complète l'Amendement 9 (hausse générale), qui coûte cher par poste pourvu parce qu'elle s'applique à tous les enseignants.

### 10.1 Levier
- T1 : hausse de x % du salaire d'entrée, pendant Y années de carrière, pour chaque nouvelle cohorte recrutée. Régime permanent : Y cohortes présentes en même temps.
- Coût hors CAS = admis par an (data/evidence_attractivite_fr.csv A04 et A12) x coût moyen chargé hors CAS d'entrée (RAP 2025 : premier degré 38 363, second degré 40 509 euros) x x % x Y. Avec CAS : multiplié par (1 + taux 2026, 82,28 %). Variante L2 : baisse de retenue équivalente en net (x % x rapport net/brut de data/processed/cross_country_net_cost.csv), avec financement du compte pensions.
- L'attrition des cohortes est ignorée : borne haute du coût.

### 10.2 Effet
- Variation des candidats = epsilon x x % x candidats présents, epsilon dans {0,3 ; 1,0 ; 2,0}. L'estimation anglaise (S01 à S04) porte sur le salaire de début de carrière relatif : l'application à la hausse d'entrée est directe, avec les mêmes réserves que l'Amendement 9.2.
- Admis supplémentaires au taux moyen d'admission (sensibilité : moitié), plafonnés aux postes non pourvus observés (premier degré environ 637, second degré 1 123).
- L'effet sur les candidats ne dépend pas de Y : la durée n'est qu'une sensibilité de coût. Aucun effet sur la rétention n'est modélisé (les élasticités de départ -1,5 et -3 sont des citations de seconde main, non lues à la source : hors calcul).

### 10.3 Non calculé
- Ciblage par discipline en pénurie (maths au CAPES, couverture de 71 % ; agrégation de maths, 83 %) : le nombre de postes par discipline n'est pas dans le dépôt. Le scénario n'est pas calculé et l'absence est rapportée, aucune imputation.
- Effet sur la qualité des entrants : nul en scénario central (S08), comme à l'Amendement 9.2.

### 10.4 Interdits
- Aucun ajout d'élasticité, de durée ou de grille de hausse après avoir vu les sorties. Tout ajout est un nouvel amendement, rapporté avec et sans.

## Amendement 11 — Sensibilité sur le temps d'enseignement statutaire de la France (pré-enregistré avant exécution de code/sens_fra_648.py)

Statut : exploratoire. Le diagnostic data/processed/diag_fra_hours.txt montre que la valeur de 720 h par an pour la France (36 semaines, 162 jours) est la valeur déclarée à l'OCDE pour le premier cycle du secondaire général, le second cycle général et le second cycle professionnel. Le service statutaire national des certifiés est de 18 h par semaine, soit 648 h sur 36 semaines. L'écart de 72 h n'est pas expliqué par les sources lues ; pour le premier degré, 900 h déclarées contre 864 h de service national, écart de 36 h compatible avec les 36 h d'activités pédagogiques complémentaires (lecture non confirmée par l'OCDE).
- Valeur principale du tableau international : 720 h (déclarée), pour la cohérence avec les valeurs déclarées des autres pays.
- Sensibilité : 648 h pour la France. Le coût par élève est inversement proportionnel aux heures annuelles : coût(648) = coût(720) x 720/648.
- Rapportés : valeur, rang (1 = moins cher) et position par rapport à la médiane, aux niveaux brut et employeur, avec et sans les pays imputés (Amendement 4), pour les deux valeurs d'heures.
- Le calcul national du coût de l'heure supplémentaire en France (services de 18 h, 15 h et 20 h) n'est pas concerné.
- Aucune des deux valeurs n'est retenue ou écartée après avoir vu les rangs.

## Amendement 12 — Modèle de coût d'entretien et de transition d'un curriculum (pré-enregistré avant exécution de code/cost_model.py)

Statut : exploratoire. Objet : à partir d'un curriculum (heures hebdomadaires par classe, par niveau et par matière) et d'un pays, prédire (i) le coût d'entretien en régime permanent, (ii) le coût de passage d'un curriculum A à un curriculum B.

### 12.1 Coût d'entretien
- Mode national (France) : ETP_s = somme sur les niveaux de (heures hebdomadaires de la matière s x classes du niveau) / service hebdomadaire ; coût = somme des ETP_s x coût annuel moyen chargé d'un ETP (data/parameters_teachers_cost.csv : cout_ens2d_hors_CAS) ; avec CAS : multiplication par le ratio avec/hors CAS du dépôt. Service : 18 h (la pondération par corps de data/evidence_corps_niveau.csv est une sensibilité).
- Mode OCDE (pays du tableau international) : coût par élève et par niveau = heures hebdomadaires x semaines / heures annuelles x salaire brut PPA (x facteur employeur pour le coût employeur) / taille de classe, avec les valeurs de data/processed/cross_country_net_cost.csv. La somme sur les niveaux est le coût d'une cohorte sur les niveaux listés.
- Test de cohérence imposé : +1 h hebdomadaire de mathématiques dans toutes les classes de collège doit donner 295,4 M€ hors CAS et 443,1 M€ avec CAS (mode national), et 4 x 125,8 = 503 $ PPA par élève (mode OCDE, France).

### 12.2 Coût de transition A vers B
- Différence de coût d'entretien entre B et A (positive ou négative).
- Flux d'ETP par matière : surplus = somme des baisses d'ETP_s, besoins = somme des hausses ; reconvertis = min(rho x surplus, besoins), rho étant un paramètre de scénario (central 0,5, balayage 0 à 1) ; recrutés = besoins - reconvertis ; excédentaires = surplus - reconvertis, payés un an tant qu'ils ne sont pas redéployés (règle comptable : un titulaire reste payé).
- Coûts unitaires de reconversion et de recrutement : placeholders non sourcés (data/transition_parameters.csv), à ne jamais citer comme résultat tant que le statut n'est pas remplacé par une source. Les flux d'ETP sont rapportés sans paramètre de coût.
- Passage progressif : non modélisé à ce stade. Aucune actualisation.

### 12.3 Périmètre et limites
- Seul le coût des enseignants est modélisé : ni infrastructures, ni encadrement, ni manuels, ni formation des cadres.
- Coût moyen par ETP identique pour toutes les matières et tous les corps ; coût par corps indisponible (le RAP ne donne que la moyenne du second degré).
- Classes : seul le collège est renseigné ; les niveaux sans nombre de classes sont ignorés et signalés, sans imputation.
- Curriculum des autres pays : à extraire (Eurydice, tableaux D1 de l'OCDE) avant tout usage du mode OCDE hors France. Aucune prédiction n'est publiée pour un pays dont le curriculum n'est pas dans le dépôt.

### 12.4 Interdits
- Aucun changement des formules ou de rho après avoir vu les sorties ; tout ajout est un nouvel amendement.

## Amendement 13 (2026-10-24) : validation externe du modele de cout par Eurydice (pre-enregistre avant tout calcul)

Statut : exploratoire. Aucune valeur Eurydice n'a ete consultee pour fixer ces regles ; elles sont figees avant le code.

Donnees. Temps d'instruction minimal recommande par systeme, Eurydice 2024/2025 (total sur l'enseignement general obligatoire a temps plein, en heures de 60 min, et part par matiere). Depenses observees par eleve : source unique a fixer dans data/ avant le calcul (Eurostat/OCDE, depense des etablissements publics par eleve, primaire et secondaire, annee la plus recente commune, en PPA) ; si cette source est absente, le test 2 n'est pas execute et est declare non realise.

Predit. Pour chaque systeme present dans Eurydice et dans data/processed/cross_country_net_cost.csv : cout enseignant par eleve = heures_eleve_totales x salaire_ppp x facteur_employeur / (heures_statutaires_an x taille_classe), meme formule que le mode oecd de code/cost_model.py ; aucun parametre n'est ajuste.

Tests (seuils fixes ici, sans reglage ulterieur) :
1. Coherence France : total d'heures France du curriculum modelise vs total Eurydice France ; ecart relatif <= 10 %. Les ecarts de perimetre (APC, options) sont listes, pas corriges.
2. Rang : correlation de Spearman entre cout enseignant predit par eleve et depense observee par eleve >= 0,6 (n declare).
3. Part enseignante : part predite (cout enseignant / depense observee) dans [35 %, 85 %] pour la mediane et coefficient de variation < 0,25.
4. Les valeurs aberrantes sont rapportees, jamais retirees ; un test non realise ou echoue est rapporte tel quel et n'est pas remplace par une variante.

Lecture. Succes aux trois tests : le mode oecd est declare utilisable pour des ordres de grandeur comparatifs. Echec : il est declare non valide, sans modification a posteriori du modele.

## Precision de l'Amendement 13 (2026-10-24) : unite et perimetre de la validation Eurydice (pre-enregistre avant tout code)

Donnees fixees. data/evidence_eurydice_annual.csv (annees et heures par annee notionnelle, Figure 3 p.14 du rapport, transcrites de l'image ; produit annees x heures verifie contre data/evidence_eurydice_totals.csv, ecart < 1 % pour tous les systemes communs).

Unite. Heures annuelles moyennes de l'enseignement general obligatoire a temps plein : H = somme(annees_niveau x heures_par_annee_niveau) / somme(annees_niveau), sur les niveaux CITE 1, CITE 24 et CITE 34 lorsque ce dernier est obligatoire. Ces heures sont en heures de 60 min, telles que declarees.

Perimetre. Les systemes a filieres multiples (colonne multitrack = 1 : LU, NL, AT, LI) sont exclus des tests 2 et 3 et rapportes a part ; l'Allemagne, l'Espagne et la Suisse (moyennes ponderees declarees par Eurydice) sont conserves. Le test 2 porte sur les systemes presents a la fois dans Eurydice, dans cross_country_net_cost.csv et dans la source de depenses ; n est declare.

Test 1 (France, remplace la formulation globale de l'Amendement 13) : pour chacun des trois niveaux, heures annuelles du curriculum modelise (heures hebdomadaires x 36 semaines, hors APC) contre 864 h (CITE 1, 5 ans), 973 h (CITE 24, 4 ans) et 1 008 h (CITE 34, 1 an) ; ecart relatif <= 10 % par niveau. La difference d'unite (heure de 60 min contre heure de cours de 55 min) est listee, non corrigee.

Predit. Cout enseignant par eleve et par an = H x salaire_ppp x facteur_employeur / (heures_statutaires_an x taille_classe).

Les seuils des tests 2 et 3 restent ceux de l'Amendement 13.

## Precision 2 de l'Amendement 13 (2026-10-24) : depenses observees et appariement (pre-enregistre avant tout calcul ; aucune valeur de depense consultee)

Depenses observees. Eurostat educ_uoe_fine09 (depenses publiques d'education par eleve en equivalent temps plein), unite PPS, niveaux ED1 et ED24 (premier cycle general du secondaire), frequence annuelle, periode 2021-2023 ; pour chaque pays, derniere valeur disponible sur cette periode, annee rapportee. Aucun autre filtre.

Perimetre des heures (modifie la Precision de l'Amendement 13 avant tout code) : H est calcule sur CITE 1 et CITE 24 uniquement, H = (a1 x h1 + a24 x h24)/(a1 + a24), car la depense observee ne couvre que ces deux niveaux ; CITE 34 n'entre pas dans les tests 2 et 3. Le test 1 France garde ses trois niveaux.

Depense observee par eleve-annee, ponderation par les annees Eurydice : E = (a1 x E_ED1 + a24 x E_ED24)/(a1 + a24).

Appariement. Les codes pays Eurostat/Eurydice a deux lettres sont convertis en codes ISO a trois lettres (EL vers GRC, sinon table ISO 3166 standard) pour joindre cross_country_net_cost.csv ; un pays absent de l'une des trois sources est exclu et liste.

Unites. Le cout predit utilise des PPA en dollars (OCDE) et la depense observee des PPS en euros ; la difference d'unite est un facteur multiplicatif non corrige. Le test 2 (rangs) n'en depend pas ; pour le test 3 la mediane de la part est rapportee telle quelle et le coefficient de variation (invariant par facteur) est le critere robuste ; l'ecart d'unite est signale dans le rapport.

## Resultat de l'Amendement 13 (2026-10-24) : validation du mode oecd par Eurydice et Eurostat

Execution de code/validate_eurydice.py (data/processed/validate_eurydice.txt), seuils et perimetre de l'Amendement 13 et de ses deux precisions, sans modification.

Test 1 (France, heures annuelles contre Eurydice) : college 936 h contre 973 h (-3,8 %), seconde 936 h contre 1 008 h (-7,1 %), les deux dans la tolerance de 10 % ; primaire non realise (niveau absent de data/instruction_hours_fr_secondary.csv).

Test 2 (rangs, n = 15) : Spearman 0,564 pour un seuil de 0,6 : ECHEC.

Test 3 (part enseignante) : mediane 0,548 dans [0,35 ; 0,85] : OK ; coefficient de variation 0,500 pour un seuil de 0,25 : ECHEC.

Valeurs aberrantes rapportees, non retirees : TR (part 1,70, rang predit 10 contre observe 1), IS (rangs 8 contre 15), PL (part 0,77). Les ecarts d'unite (PPA en dollars contre PPS en euros) et les annees de depense (2021 a 2023) ne sont pas corriges.

Lecture, conformement a l'Amendement 13 : le mode oecd est declare non valide pour des comparaisons internationales de cout ; ses sorties internationales ne sont pas utilisees comme resultats. Le mode national (France, cout par ETP) n'est pas concerne par ce test et reste fonde sur ses propres verifications.

## Amendement 14 (2026-10-24) : trajectoire de cout court et long terme d'un curriculum (pre-enregistre avant tout code)

Statut : exploratoire. Objet : passer du cout de regime permanent et du cout ponctuel de transition (Amendement 12) a une trajectoire annuelle C(t), t = 0..T, avec T = 30 ans. Cet amendement ne traite que les couts ; aucun effet sur PISA n'y est modelise et aucune retroaction salaire vers score n'est admise.

Entrees. Un curriculum cible exprime par ecarts d'heures hebdomadaires (format --delta de code/cost_model.py), data/classes_fr.csv, data/transition_parameters.csv et le cout moyen charge par ETP de l'Amendement 12 (hors CAS 52 248 EUR ; avec CAS x 1,5001). Les sorties sont toujours donnees en deux colonnes, hors CAS et avec CAS.

Montee en charge. La part de la reforme en vigueur est p(t) = min(1, t / L), L = 4 ans (central), sensibilites L = 2 et L = 8. Le besoin supplementaire en ETP est DeltaETP(t) = p(t) x DeltaETP_regime, par matiere, d'apres l'identite ETP = classes x heures hebdomadaires / service.

Flux d'ETP. Les surplus de matiere sont reconvertis a la part rho (central 0,5 ; sensibilites 0,25 et 0,75), plafonnee par les besoins ; le reste des besoins est recrute avec un delai de d = 1 an entre recrutement et prise de service (sensibilites 0 et 2) ; les ETP excedentaires non reconvertis sont maintenus en service un an puis resorbes par les departs naturels, au rythme de depart de 3 % de l'effectif par an (parametre non source, declare ici). Un ETP reconverti ou recrute a le cout moyen charge de l'Amendement 12 une fois en service.

Couts ponctuels. T01 (formation de reconversion, fraction du cout annuel d'un ETP) dans {0,05 ; 0,10 ; 0,20}, T02 (recrutement et formation initiale) dans {0,10 ; 0,20 ; 0,40}, centraux 0,10 et 0,20. Aucune de ces valeurs n'est sourcee par un cout par tete ; seul ancrage disponible : la Cour des comptes (refere du 12 mars 2018) estime a 1,1 Md EUR le cout des deux annees de master en ESPE hors remuneration des stagiaires, sans cout par tete ni effectifs. Les resultats sont declares non sources sur ces deux couts, et la regle suivante s'applique : si les couts ponctuels pesent moins de 10 % de la valeur actuelle nette sur toute la grille de sensibilite, la conclusion est declaree robuste a leur valeur ; sinon elle est declaree dependante de couts non sources.

Prime salariale d'equilibre. Pour chaque matiere en tension, le recrutement supplementaire DeltaN par rapport au recrutement annuel actuel N0 exige une hausse du salaire d'entree Dw = (DeltaN / N0) / epsilon, epsilon dans {0,3 ; 1 ; 2} comme dans l'Amendement 10, central 1. Variante centrale : la hausse est ciblee sur les entrants de la matiere et propagee aux cohortes d'entrants successives pendant une carriere de 30 ans, a cout cumule croissant jusqu'au regime ; variante de sensibilite : hausse appliquee a tout le corps de la matiere. Aucune autre reponse d'offre n'est modelisee.

Demographie. Le central est neutre (effectifs d'eleves constants). Une variante demographique n'est executee que si une projection d'effectifs officielle (DEPP ou INSEE) est ajoutee a data/ avec sa source avant le calcul ; sinon elle est declaree non realisee.

Actualisation. Taux central 2 %, sensibilites 0 % et 4 % ; la reference officielle du taux central est a verifier et citer avant publication ; toutes les valeurs actualisees sont affichees avec le taux utilise.

Sorties. Pour chaque cellule de la grille (L, rho, d, epsilon, T01, T02) : cout annuel C(t) sans actualisation, pic, cout de regime permanent, valeur actuelle nette sur T = 30 ans, en M EUR hors CAS et avec CAS. Aucun parametre n'est ajuste a un resultat.

Controle de regression pre-declare. Avec L = 1, d = 0, rho = 0, T01 = T02 = 0, epsilon tendant vers l'infini (aucune prime) et sans reconversion, le cout de regime permanent doit reproduire les deux ecarts verifies de l'Amendement 12 (+295,4 et +73,8 M EUR hors CAS ; +443,1 et +110,8 avec CAS), avec les memes arguments --delta que ceux des executions de validation de code/cost_model.py, a 0,1 M EUR pres ; un ecart superieur invalide le code avant toute autre sortie.

Limites declarees. Pas d'effet de la reforme sur le recrutement futur au-dela de la prime ; pas de cout de construction ni de materiel ; couts ponctuels non sources ; demographie neutre par defaut.

## Precision de l'Amendement 14 (2026-10-24) : recrutement annuel actuel N0 (pre-enregistre avant la grille avec prime)

N0 est le nombre d'admis aux concours externes du second degre public, session 2025 : Agregation 1 617, Capes 4 344, Capet 437, Capeps 670, CAPLP 940, soit N0 = 8 008 (source : data/evidence_concours_2025_second_degre.csv, devenirenseignant.gouv.fr). Sensibilite : postes offerts, soit 8 857 (1 710 + 4 890 + 495 + 670 + 1 092). Ne sont pas comptes : concours speciaux (agregation speciale, Mayotte), contractuels, concours internes et prive ; N0 est donc sous-estime, ce qui surestime la hausse relative DeltaN / N0 et la prime. Le CRPE (premier degre) est hors perimetre de N0. Aucune autre valeur de N0 n'est essayee. Les resultats sont produits pour N0 = 8 008 et N0 = 8 857 et rapportes tous deux.
