"""
Projet Education -- Diagnostics A.4
=====================================
Deux regressions de diagnostic a executer AVANT de figer les features
du graphe de notions (Phase 2). Conditionnent si g_{i,n} et p_{i,n}
restent des variables separees ou doivent etre fusionnees/retravaillees.

Statut: SPECIFICATION PRETE A L'EMPLOI, donnees non chargees.
Aucun reseau vers oecd.org / timss2023.org / iea.org n'est disponible
depuis ce sandbox -- fichiers a fournir par l'utilisateur (voir
REQUIRED_FILES ci-dessous) ou a brancher sur une autre machine.

Dependances: pandas, statsmodels, numpy
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf

# ---------------------------------------------------------------
# Fichiers requis (non fournis) -- a adapter aux formats reels
# une fois telecharges depuis timss2023.org/data, TALIS, DEPP, etc.
# ---------------------------------------------------------------
REQUIRED_FILES = {
    "timss_curriculum_nrc": "Couverture 'prevue' (NRC) par pays x notion x grade",
    "timss_teacher_coverage": "Couverture 'implementee' (% eleves, Teacher Questionnaire) par pays x notion x grade",
    "timss_instructional_hours": "Heures totales allouees a la matiere par pays x grade",
    "talis_teacher_background": "Part des enseignants ayant une formation disciplinaire adequate, par pays (module maths 2013 + cycles recents)",
    "national_teacher_salary": "Salaire relatif des enseignants (vs professions comparables), par pays -- DEPP/NCES/NEPS/etc. pour les pays 'en profondeur', OCDE/Eurostat sinon",
    "oecd_gdp_education_spend": "PIB/habitant et depense educative totale par pays -- controle pour le confondant richesse nationale (point de rigueur deja souleve)",
}


# =================================================================
# DIAGNOSTIC 1 -- g_{i,n} (ecart prevu-implemente) vs temps total
# =================================================================
# Hypothese testee: l'ecart intended-implemented reflete-t-il
# principalement une contrainte de temps total, ou des causes
# distinctes (formation des enseignants, manuels, alignement
# examens) ?
#
# Modele:
#   g_{i,n} = alpha + gamma * H_i^total + epsilon_{i,n}
#
# Decision:
#   |gamma| fort et significatif -> fusionner g et le temps total
#     (redondance confirmee, simplifier le feature set)
#   |gamma| faible ou non significatif -> garder g_{i,n} et le
#     temps d'instruction comme variables separees dans le graphe
#     (Section 5.3 du plan)

def diagnostic_1_gap_vs_time(df: pd.DataFrame) -> dict:
    """
    df attendu avec colonnes:
        country, notion, grade,
        coverage_intended   (0/1, NRC, Curriculum Questionnaire)
        coverage_implemented (0-1, % eleves, Teacher Questionnaire)
        instructional_hours_total (heures/an, pays x grade x matiere)

    Erreurs standard clusterisees par pays (observations repetees
    par notion au sein d'un meme pays ne sont pas independantes).
    """
    df = df.copy()
    df["g"] = df["coverage_intended"] - df["coverage_implemented"]

    model = smf.ols(
        "g ~ instructional_hours_total",
        data=df,
    ).fit(cov_type="cluster", cov_kwds={"groups": df["country"]})

    gamma = model.params["instructional_hours_total"]
    pval = model.pvalues["instructional_hours_total"]
    r2 = model.rsquared

    decision = (
        "FUSIONNER (redondance confirmee)"
        if (pval < 0.05 and abs(gamma) > 0)  # seuil de magnitude a
        # affiner une fois la distribution reelle de g observee --
        # ne pas se fier au seul p-value avec un panel de cette
        # taille (cf. power analysis, rappel: panel pays x cycle
        # recommande pour ce diagnostic aussi, pas seulement pour
        # le modele principal)
        else "GARDER SEPAREES (causes distinctes)"
    )

    return {
        "model": model,
        "gamma": gamma,
        "pvalue": pval,
        "r2": r2,
        "decision": decision,
        "summary": model.summary(),
    }


# =================================================================
# DIAGNOSTIC 2 -- qualite des enseignants vs couverture (mediation)
# =================================================================
# Hypothese testee: la qualite des enseignants (salaire relatif,
# adequation disciplinaire) agit-elle VIA la couverture p_{i,n}
# (mediation), ou en parallele (effet direct independant) ?
#
# Point de rigueur deja souleve: les mettre comme deux regresseurs
# independants dans le meme modele sans tester ca d'abord risque
# de controler pour une variable intermediaire du mecanisme qu'on
# veut mesurer.
#
# Approche: test de mediation simple (Baron & Kenny, 1986) --
# suffisant ici vu la taille d'echantillon; pas besoin d'un modele
# d'equations structurelles complet avec N aussi petit.
#
#   Etape a: p_{i,n} = alpha_a + a * TeacherQuality_i + eps_a
#   Etape b: Score_i  = alpha_b + b * TeacherQuality_i
#                        + c * p_{i,n} + eps_b
#
#   Mediation totale   si: a significatif, c significatif,
#                          b (effet direct controle) non significatif
#   Mediation partielle si: a, b, c tous significatifs
#   Pas de mediation    si: a non significatif

def diagnostic_2_teacher_quality_mediation(
    df: pd.DataFrame, outcome_col: str = "pisa_timss_score"
) -> dict:
    """
    df attendu avec colonnes:
        country, notion (ou agrege par pays si pas de variation
        par notion dans TeacherQuality),
        coverage_implemented (p_{i,n}),
        teacher_quality_index (salaire relatif + adequation
            disciplinaire, composite a construire -- cf. TALIS +
            sources nationales),
        pisa_timss_score (CIBLE -- rappel A.1: construire cette
            fonction deux fois, une par cible, cf. double piste
            PISA/TIMSS actee)
        gdp_per_capita, education_spend_pct_gdp (CONTROLES --
            confondant richesse nationale, point de rigueur deja
            souleve pour le lien salaire-qualite)
    """
    # Etape a
    step_a = smf.ols(
        "coverage_implemented ~ teacher_quality_index "
        "+ gdp_per_capita + education_spend_pct_gdp",
        data=df,
    ).fit(cov_type="cluster", cov_kwds={"groups": df["country"]})

    # Etape b
    step_b = smf.ols(
        f"{outcome_col} ~ teacher_quality_index + coverage_implemented "
        "+ gdp_per_capita + education_spend_pct_gdp",
        data=df,
    ).fit(cov_type="cluster", cov_kwds={"groups": df["country"]})

    a = step_a.params["teacher_quality_index"]
    a_p = step_a.pvalues["teacher_quality_index"]
    b = step_b.params["teacher_quality_index"]
    b_p = step_b.pvalues["teacher_quality_index"]
    c = step_b.params["coverage_implemented"]
    c_p = step_b.pvalues["coverage_implemented"]

    if a_p >= 0.05:
        verdict = (
            "PAS DE MEDIATION -- garder comme regresseurs "
            "potentiellement independants (mais revoir la "
            "specification, l'hypothese de depart n'est pas "
            "soutenue)"
        )
    elif b_p >= 0.05 and c_p < 0.05:
        verdict = (
            "MEDIATION TOTALE -- ne PAS mettre teacher_quality et "
            "coverage_implemented comme deux regresseurs "
            "independants dans le modele principal (Partie 3); "
            "garder coverage_implemented seul, teacher_quality "
            "comme variable explicative de coverage uniquement"
        )
    elif b_p < 0.05 and c_p < 0.05:
        verdict = (
            "MEDIATION PARTIELLE -- les deux variables apportent "
            "de l'information distincte, peuvent rester toutes les "
            "deux dans le modele principal, avec cette dependance "
            "documentee explicitement"
        )
    else:
        verdict = "RESULTAT AMBIGU -- a examiner cas par cas"

    return {
        "step_a": step_a,
        "step_b": step_b,
        "a": a, "a_pvalue": a_p,
        "b": b, "b_pvalue": b_p,
        "c": c, "c_pvalue": c_p,
        "verdict": verdict,
    }


if __name__ == "__main__":
    print(__doc__)
    print("Fichiers requis (aucun charge actuellement):")
    for k, v in REQUIRED_FILES.items():
        print(f"  - {k}: {v}")
    print(
        "\nCe script ne s'execute pas tel quel -- fournir les "
        "donnees reelles (voir REQUIRED_FILES) pour lancer les "
        "deux diagnostics."
    )
