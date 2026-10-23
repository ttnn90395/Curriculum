import csv
S1 = "education.gouv.fr 'Les horaires par cycle au college' (page datee 2019; arretes 19/05/2015 et 16/06/2017)"
S2 = "digischool.fr citing eduscol (maj janv. 2026; arrete 16/07/2018)"
rows = []
col = {
 "6e": [("francais",4.5,"reading"),("mathematiques",4.5,"math"),("histoire-geo-EMC",3,""),("LV1",4,""),("SVT+physique-chimie",3,"science"),("arts plastiques",1,""),("education musicale",1,""),("EPS",4,""),("soutien/approfondissement francais-maths",1,"reading+math")],
 "5e": [("francais",4.5,"reading"),("mathematiques",3.5,"math"),("histoire-geo-EMC",3,""),("LV1",3,""),("LV2",2.5,""),("SVT",1.5,"science"),("physique-chimie",1.5,"science"),("technologie",1.5,"science"),("arts plastiques",1,""),("education musicale",1,""),("EPS",3,"")],
 "4e": [("francais",4.5,"reading"),("mathematiques",3.5,"math"),("histoire-geo-EMC",3,""),("LV1",3,""),("LV2",2.5,""),("SVT",1.5,"science"),("physique-chimie",1.5,"science"),("technologie",1.5,"science"),("arts plastiques",1,""),("education musicale",1,""),("EPS",3,"")],
 "3e": [("francais",4,"reading"),("mathematiques",3.5,"math"),("histoire-geo-EMC",3.5,""),("LV1",3,""),("LV2",2.5,""),("SVT",1.5,"science"),("physique-chimie",1.5,"science"),("technologie",1.5,"science"),("arts plastiques",1,""),("education musicale",1,""),("EPS",3,"")],
}
for g, L in col.items():
    t = sum(x[1] for x in L); assert t == 26, (g, t)
    for s, h, d in L: rows.append(["college", g, s, h, d, S1, "extracted", "total 26 h; EPI/AP integres aux lignes; verifier les changements posterieurs a 2019 (groupes de niveau 6e-5e, soutien)"])
sec = [("francais",4,"reading"),("mathematiques",4,"math"),("histoire-geo",3,""),("physique-chimie",3,"science"),("LV A+B",5.5,""),("SES",1.5,""),("SVT",1.5,"science"),("SNT",1.5,"science"),("EPS",2,"")]
assert sum(x[1] for x in sec) == 26
for s, h, d in sec: rows.append(["lycee GT", "2de", s, h, d, S2, "secondary_press", "tronc commun; EMC 18 h/an hors total; la page annonce 26 h 30 mais les lignes donnent 26 h"])
prem = [("francais",4,"reading"),("histoire-geo",3,""),("LV A+B",4.5,""),("enseignement scientifique",2,"science"),("EPS",2,"")]
term = [("philosophie",4,""),("histoire-geo",3,""),("LV A+B",4,""),("enseignement scientifique",2,"science"),("EPS",2,"")]
for g, L, note in [("1re", prem, "tronc commun 15 h 30 ; 3 specialites de 4 h (12 h) non detaillees ici; enseignement scientifique 3 h 30 sans specialite maths"), ("terminale", term, "tronc commun 15 h ; 2 specialites de 6 h non detaillees ici")]:
    for s, h, d in L: rows.append(["lycee GT", g, s, h, d, S2, "secondary_press", note])
with open("data/instruction_hours_fr_secondary.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["level","grade","subject","weekly_hours","pisa_domain","source","status","note"]); w.writerows(rows)
print(len(rows))
