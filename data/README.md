# Sources de données

Aucun fichier de données brutes n'est versionné dans ce dépôt
(voir `.gitignore`). Ce document liste où les trouver et ce qui
est attendu dans `data/raw/`.

## Accès réseau : aucun outil ici ne peut télécharger depuis les
portails OCDE/IEA. Téléchargement manuel requis.

## Priorité 1 -- bloquant pour toute la Partie 2/3

| Source | Où | Fichier attendu dans `data/raw/` |
|---|---|---|
| TIMSS 2023 (Curriculum Questionnaire + Teacher Questionnaire) | timss2023.org/data (R/SPSS/SAS) | `timss2023_curriculum.*`, `timss2023_teacher.*` |
| TIMSS Advanced 2015 | timssandpirls.bc.edu | `timss_advanced_2015.*` |
| PISA database (2000-2025) | OCDE, PISA data explorer | `pisa_<cycle>.*` |

**Avant d'aller plus loin** : la couverture TIMSS 2023 pays x cycle
n'a pas pu être confirmée par recherche web (tableau Exhibit A.1,
structure de colonnes perdue à l'extraction). À vérifier en premier
à partir du fichier réel téléchargé -- conditionne la liste finale
de pays du panel.

## Priorité 2 -- qualité des enseignants, canal emploi

| Source | Où | Fichier attendu |
|---|---|---|
| TALIS (2013 module maths, 2018, 2024) | OCDE | `talis_<cycle>.*` |
| PIAAC Cycles 1-2 | OCDE | `piaac_cycle1.*`, `piaac_cycle2.*` |
| PIAAC Cycle 2 : vérifier couverture de la France avant usage |

## Priorité 3 -- sources nationales (pays "en profondeur")

| Pays | Agence | Lien |
|---|---|---|
| France | DEPP | education.gouv.fr/les-depp |
| États-Unis | NCES / IPEDS | nces.ed.gov |
| Allemagne | NEPS | neps-data.de |
| Finlande | Statistics Finland | stat.fi |
| Japon | MEXT | mext.go.jp |
| Corée | KEDI | kedi.re.kr |
| Canada | StatCan / CMEC | statcan.gc.ca, cmec.ca |
| Australie | ABS / ACARA | abs.gov.au, acara.edu.au |
| Nouvelle-Zélande | Education Counts | educationcounts.govt.nz |
| Reste de l'Europe | Eurydice (point d'entrée unique) | eurydice.eacea.ec.europa.eu |

Pologne, Colombie, Mexique, Chili, Costa Rica, Israël : pas de
source nationale confirmée -- traités via OCDE/IEA uniquement.

## Priorité 4 -- macro et coût

- OECD Education at a Glance (dépense, diplômés par domaine)
- World Bank Open Data (chômage, PIB hors France)
- INSEE (France)
- Eurostat (`isoc_sks_itspt`, spécialistes TIC)
- France Stratégie (taux d'actualisation, Valeur de l'Action pour
  le Climat)

## Convention de nommage

`<source>_<périmètre>_<année_ou_cycle>.<ext>` -- exemple :
`timss2023_curriculum_grade8.sav`, `piaac_cycle2_fra.csv`.

## Une fois les fichiers présents

Les scripts de `code/diagnostic_regressions.py` indiquent
précisément les colonnes attendues dans leurs docstrings -- les
adapter au format réel des fichiers une fois téléchargés, les noms
de colonnes ci-dessus sont indicatifs.
