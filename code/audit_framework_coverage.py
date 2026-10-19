"""Audit: couverture du cadre TIMSS 2023 (4e annee, maths) par le graphe KST etendu.
Entrees: data/framework_timss2023_g4_math.csv, code/kst_extension.py. Rien n'est ecrit.
Source du cadre: T23_Frameworks_Ch1_Mathematics.pdf (elvis.bc.edu/timss2023/frameworks/pdf/).
Objectifs transcrits depuis un RESUME (paraphrase) du texte: a confronter au PDF avant citation.
"""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kst_extension as k

f = pd.read_csv("data/framework_timss2023_g4_math.csv").fillna("")
bad = []
for r in f.itertuples():
    for n in filter(None, r.notions.split(";")):
        if n not in k.EXT:
            bad.append((r.obj_id, n))
    if r.crosswalk_topic and r.crosswalk_topic not in k.TOPIC_TO_NOTIONS:
        bad.append((r.obj_id, r.crosswalk_topic))
    elif r.crosswalk_topic and set(r.notions.split(";")) - set(k.TOPIC_TO_NOTIONS[r.crosswalk_topic]):
        bad.append((r.obj_id, "notion hors correspondance du sujet", r.notions))
print(f"{len(f)} objectifs du cadre TIMSS 2023 (4e annee, maths)")
print(f.coverage.value_counts().to_string())
print("incoherences:", bad or "aucune")
used = {n for s in f.notions for n in s.split(";") if n}
print("notions du graphe etendu absentes du cadre G4:", sorted(set(k.EXT) - used))
print("sujets du tableau d'appariement non rattaches a un objectif:", sorted(set(k.TOPIC_TO_NOTIONS) - set(f.crosswalk_topic)))
print("objectifs partiels ou non couverts:")
print(f[f.coverage != "full"][["obj_id", "coverage", "note"]].to_string(index=False))
