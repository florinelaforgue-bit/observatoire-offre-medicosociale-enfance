"""Preuve d'absence de perte au niveau des valeurs, connecteur structures.

Le controle de cles garantit que toute cle JSON est declaree. Il ne garantit
pas qu'elle est lue : une faute de frappe dans un .get() produirait None en
silence sur un champ nullable. On compte donc les valeurs non nulles de chaque
colonne du pivot et on les confronte au recensement exhaustif du JSON.
"""
import sys
from pathlib import Path
from contrat_source import (CONTROLE_MINIMAL, InventaireCodes, Lot, RapportIngestion,
                            RegistreAnomalies, parcourir_source)
import finess_commun as fc
from finess_structures import SourceFinessStructures

FICHIER = Path("/mnt/user-data/uploads/finess-structures-mensuel-202607_json.gz")

# Valeurs non nulles attendues, tirees du recensement exhaustif du JSON.
# (colonne du pivot -> effectif attendu)
ATTENDU = {
    ("etablissement", "siret"): 174508 - 35294,
    ("etablissement", "code_espic"): 21310,
    ("etablissement", "numero_uai"): 174508 - 169948,
    ("etablissement", "numero_reference_externe"): 174508 - 151208,
    ("etablissement", "code_categorie"): 174508 - 5,
    ("etablissement", "code_mode_fixation_tarifaire"): 174508 - 5,
    ("etablissement", "code_type_budget"): 174508 - 5,
    ("etablissement", "date_fermeture"): 174508 - 104822,
    ("etablissement", "complement_denomination"): 174508 - 157985,
    ("entite_juridique", "siren"): 98168 - 16375,
    ("entite_juridique", "code_ape"): 98168 - 16375,
    ("entite_juridique", "code_fonction_publique"): 98168 - 82602,
    ("entite_juridique", "code_type_groupe_gco"): 98168 - 96312,
    ("entite_juridique", "complement_adresse"): 98168 - 92045,
    ("entite_juridique", "date_fermeture"): 98168 - 54164,
    ("entite_juridique", "code_categorie"): 0,          # toujours nul, conforme au schema
    ("adresse", "libelle_voie"): 278615 - 19081,
    ("adresse", "numero_voie"): 278615 - 63677,
    ("adresse", "code_type_voie"): 278615 - 71928,
    ("adresse", "lieu_dit"): 278615 - 252742,
    ("adresse", "complement_voie"): 278615 - 270382,
    ("adresse", "complement_point_geographique"): 278615 - 237642,
    ("adresse", "ligne_acheminement"): 278615 - 3781,
    ("adresse", "cle_interop_ban"): 278615 - 91682,
    ("adresse", "score_ban"): 278615 - 91682,
    ("adresse", "coordonnee_x"): 278615 - 91682,
    ("adresse", "ligne_trois"): 0,                      # toujours nulle, conforme au recensement
    ("contact", "telephone"): 222505 - 410,
    ("contact", "telecopie"): 222505 - 126549,
    ("contact", "courriel"): 222505 - 222401,
    ("engagement", "code_type_engagement"): 77268 - 144,
    ("engagement", "code_sous_type_engagement"): 77268 - 60,
    ("engagement", "nom_engagement"): 0,
    ("engagement", "identifiant_engagement"): 0,
    ("engagement", "date_effet"): 77268 - 24,
    ("engagement", "date_caducite"): 77268 - 77266,
    ("evenement", "code_etat_objet_1"): 629075 - 1095,
    ("evenement", "identifiant_objet_2"): 169,
    ("groupement", "num_finess_groupement"): 135,
    ("groupement", "nom_groupement"): 135,
}

rap = RapportIngestion(Lot("", "", "", "", 0), RegistreAnomalies(), InventaireCodes(),
                       CONTROLE_MINIMAL)
non_nuls = {}
for nom_type, ligne in parcourir_source(SourceFinessStructures(), FICHIER,
                                        controle=CONTROLE_MINIMAL, rapport=rap,
                                        inventorier_codes=False):
    compte = non_nuls.setdefault(nom_type, None)
    if compte is None:
        compte = non_nuls[nom_type] = [0] * len(ligne)
    for i, v in enumerate(ligne):
        if v is not None:
            compte[i] += 1

types = {t.nom: t for t in fc.TYPES_STRUCTURES}
ecarts, colonnes_vides = [], []
for nom_type, compte in sorted(non_nuls.items()):
    noms = types[nom_type].noms
    for i, nom_champ in enumerate(noms):
        if compte[i] == 0:
            colonnes_vides.append((nom_type, nom_champ))
        attendu = ATTENDU.get((nom_type, nom_champ))
        if attendu is not None and attendu != compte[i]:
            ecarts.append((nom_type, nom_champ, attendu, compte[i]))

print(f"Colonnes confrontees au recensement : {len(ATTENDU)}")
if ecarts:
    print(f"ECHEC : {len(ecarts)} ecarts")
    for t, c, a, r in ecarts:
        print(f"   {t}.{c:<32} attendu {a:>8} · obtenu {r:>8}")
else:
    print("OK : chaque colonne confrontee porte exactement le nombre de valeurs du JSON")

print(f"\nColonnes entierement nulles : {len(colonnes_vides)}")
for t, c in colonnes_vides:
    justifie = ATTENDU.get((t, c)) == 0
    print(f"   {t}.{c:<32} {'conforme au recensement' if justifie else 'A JUSTIFIER'}")

sys.exit(1 if ecarts or any(ATTENDU.get(x) != 0 for x in colonnes_vides) else 0)
