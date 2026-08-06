import csv
from pathlib import Path

DATA = Path(__file__).parent / "data"

# --- structureet complets (32 champs), destinés à finess.csv --------------
# champs[0]=type, champs[1..31] = les 31 champs nommés d'Etablissement
etabs = [
    # nofinesset, nofinessej, raison_sociale, ..., libelle_categorie_etablissement, ...
    ["structureet", "010000001", "010000002", "IME Test Un", "Institut Medico Educatif Test Un",
     "", "", "12", "RUE", "DE LA PAIX", "", "", "01001", "01", "AIN",
     "01000 BOURG EN BRESSE", "0400000000", "", "183", "Institut Médico-Educatif (I.M.E.)",
     "800", "Handicap Enfance", "12345678900012", "8790A", "00", "", "", "",
     "01/01/2000", "01/01/2000", "01/01/2026", ""],

    ["structureet", "010000003", "010000002", "MECS Test Deux", "Maison Enfants Caractere Social Deux",
     "", "", "5", "AVENUE", "VICTOR HUGO", "", "", "01001", "01", "AIN",
     "01000 BOURG EN BRESSE", "0400000001", "", "175", "Maison d'Enfants à Caractère Social",
     "801", "Protection Enfance", "12345678900029", "8790B", "00", "", "", "",
     "01/06/2005", "01/06/2005", "15/03/2026", ""],

    # Categorie absente de la taxonomie (non classee attendu)
    ["structureet", "010000004", "010000005", "EHPAD Test Trois", "Etablissement Herbergement Personnes Agees Trois",
     "", "", "1", "PLACE", "DE LA MAIRIE", "", "", "01002", "01", "AIN",
     "01000 BOURG EN BRESSE", "0400000002", "", "500", "Etablissement d'Hébergement pour Personnes Agées Dépendantes",
     "900", "Personnes Agees", "12345678900036", "8710A", "00", "", "", "",
     "01/01/1998", "01/01/1998", "01/02/2026", ""],

    # 2e IME rattache a la MEME EJ que le premier IME (pour tester le comptage EJ distincts)
    ["structureet", "010000006", "010000002", "IME Test Quatre", "Institut Medico Educatif Test Quatre",
     "", "", "8", "RUE", "DES ECOLES", "", "", "01003", "01", "AIN",
     "01000 BOURG EN BRESSE", "0400000003", "", "183", "Institut Médico-Educatif (I.M.E.)",
     "800", "Handicap Enfance", "12345678900043", "8790A", "00", "", "", "",
     "01/01/2010", "01/01/2010", "01/01/2026", ""],
]

assert all(len(row) == 32 for row in etabs), [len(r) for r in etabs]

# --- equipementsocial (>=8 champs), destines a etablissements.csv --------
equipements = [
    ["equipementsocial", "010000001", "901", "Accueil de jour", "11", "Internat", "010", "Deficience intellectuelle",
     "AAA", "20", "01/01/2000", "0"],
    ["equipementsocial", "010000001", "902", "Semi-internat", "16", "Semi-internat", "010", "Deficience intellectuelle",
     "BBB", "15", "01/01/2000", "0"],
    ["equipementsocial", "010000003", "903", "Hebergement", "11", "Internat", "020", "Enfance en danger",
     "CCC", "30", "01/06/2005", "0"],
]

# --- structureet reduits (3 champs), table de correspondance ET<->EJ -----
correspondances_reduites = [["structureet", row[1], row[2]] for row in etabs]

DATA.mkdir(parents=True, exist_ok=True)

with open(DATA / "finess.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["finess", "etalab", "113", "2026-05-12"])
    for row in etabs:
        w.writerow(row)

with open(DATA / "etablissements.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["finess", "etalab", "113", "2026-05-12"])
    for row in correspondances_reduites:
        w.writerow(row)
    for row in equipements:
        w.writerow(row)

print("Fichiers générés :")
print(" -", DATA / "finess.csv", f"({len(etabs)} structureet)")
print(" -", DATA / "etablissements.csv",
      f"({len(correspondances_reduites)} structureet réduits + {len(equipements)} equipementsocial)")
