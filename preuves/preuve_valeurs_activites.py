"""Preuve d'absence de perte au niveau des valeurs, connecteur activites.

Les effectifs attendus ne sont pas recopies a la main : ils sont lus dans le
recensement exhaustif du JSON, puis confrontes aux colonnes du pivot.
"""
import sys
from pathlib import Path
from contrat_source import (CONTROLE_MINIMAL, InventaireCodes, Lot, RapportIngestion,
                            RegistreAnomalies, parcourir_source)
import finess_commun as fc
from finess_activites import SourceFinessActivites

FICHIER = Path("/mnt/user-data/uploads/finess-activites-mensuel-202607_json.gz")
RECENSEMENT = Path("recens_activites.txt")

# --- lecture du recensement : chemin -> (present, nuls) ---------------------
recens = {}
for ligne in RECENSEMENT.read_text(encoding="utf-8").splitlines():
    if not ligne.strip() or ligne.startswith("#") or ligne.startswith("CHEMIN"):
        continue
    if " -> " in ligne:
        break
    m = ligne.split()
    if len(m) >= 3 and m[1].isdigit() and m[2].isdigit():
        recens[m[0]] = (int(m[1]), int(m[2]))

EJ = "pmej.activitesAutorisees[]"
ET = "pmej.ege[].activitesExercees[]"

def non_nuls(*suffixes, niveaux=(EJ, ET)):
    """Valeurs non nulles cumulees sur les chemins indiques, aux niveaux indiques."""
    total = 0
    trouves = 0
    for niveau in niveaux:
        for suffixe in suffixes:
            chemin = f"{niveau}.{suffixe}"
            if chemin in recens:
                present, nuls = recens[chemin]
                total += present - nuls
                trouves += 1
    if trouves == 0:
        raise AssertionError(f"chemins introuvables au recensement : {suffixes}")
    return total

BLOCS = ["typeActiviteAMSR", "typeActiviteASOCR", "typeActiviteASDR", "typeActiviteAER",
         "typeActiviteAASA", "typeActiviteAMF", "typeActiviteAMM", "typeActiviteEML"]
SPEC = "nature.caracteristiquesSpecifiques"
GEN = "caracteristiquesGeneriques"
CODES = ["activiteSocialeRegulee", "activiteSanitaireDiverseRegulee",
         "activiteEnseignementRegulee", "activiteSanitaireRegulee",
         "activiteAMF", "activiteAMM"]
IDS = ["aaSocialeReguleeId", "aaSanitaireDiverseReguleeId", "aaSoinAmmId",
       "aaSoinAmfId", "aaAutreActSoinId", "aaEmlId"]

ATTENDU = {
    ("activite", "code_type_activite_smsse"): non_nuls(f"{GEN}.typeActiviteSMSSE"),
    ("activite", "ege_id"): non_nuls(f"{GEN}.egeId"),
    ("activite", "identifiant_autorisation"): non_nuls(f"{GEN}.identifiantAutorisation"),
    ("activite", "num_autorisation_arhgos"): non_nuls(f"{GEN}.numAutorisationArhgos"),
    ("activite", "date_debut_activite_autorisee"): non_nuls(f"{GEN}.dateDebutActiviteAutorisee"),
    ("activite", "date_fin_activite_autorisee"): non_nuls(f"{GEN}.dateFinActiviteAutorisee"),
    ("activite", "date_fin_effective_activite"): non_nuls(f"{GEN}.dateFinEffectiveActivite"),
    ("activite", "date_caducite_autorisation"): non_nuls(f"{GEN}.dateCaduciteAutorisation"),
    ("activite", "pm_smsse_exploitante_id"): non_nuls(f"{GEN}.pmSmsseExploitanteId", niveaux=(EJ,)),
    ("activite", "ege_exploitante_id"): non_nuls(f"{GEN}.egeExploitanteId", niveaux=(ET,)),
    ("activite", "ege_facturante"): non_nuls(f"{GEN}.egeFacturante", niveaux=(ET,)),
    ("activite", "activite_ae_id_specifique"): non_nuls(f"{SPEC}.activiteAeId"),
    ("activite", "age_min_autorise"): non_nuls(f"{SPEC}.ageMinAutorise"),
    ("activite", "age_max_autorise"): non_nuls(f"{SPEC}.ageMaxAutorise"),
    ("activite", "age_min_installe"): non_nuls(f"{SPEC}.ageMinInstalle"),
    ("activite", "age_max_installe"): non_nuls(f"{SPEC}.ageMaxInstalle"),
    ("activite", "marque"): non_nuls(f"{SPEC}.marque"),
    ("activite", "numero_serie"): non_nuls(f"{SPEC}.numeroSerie"),
    ("activite", "code_etat_arhgos"): non_nuls(f"{SPEC}.etatArhgos"),
    ("activite", "num_decision"): non_nuls(f"{SPEC}.numDecision"),
    ("activite", "date_lim_dep"): non_nuls(f"{SPEC}.dateLimDep"),
    ("activite", "date_lim_visite_conformite"): non_nuls(f"{SPEC}.dateLimVisiteConformite"),
    ("activite", "date_visite"): non_nuls(f"{SPEC}.dateVisite"),
    ("activite", "code_resultat_visite"): non_nuls(f"{SPEC}.resultatVisite"),
    ("activite", "identifiant_nature"): non_nuls(*[f"{SPEC}.{i}" for i in IDS]),
    ("activite", "code_activite_regulee"): non_nuls(
        *[f"{SPEC}.{b}.{c}" for b in BLOCS for c in CODES]),
    ("activite", "code_mode_fonctionnement"): non_nuls(
        *[f"{SPEC}.{b}.modeFonctionnement" for b in BLOCS]),
    ("activite", "code_public"): non_nuls(*[f"{SPEC}.{b}.public" for b in BLOCS]),
    ("activite", "code_forme_activite"): non_nuls(*[f"{SPEC}.{b}.formeActivite" for b in BLOCS]),
    ("activite", "code_modalite_activite"): non_nuls(
        *[f"{SPEC}.{b}.modaliteActivite" for b in BLOCS]),
    ("activite", "code_modalite_amm"): non_nuls(f"{SPEC}.typeActiviteAMM.modaliteAMM"),
    ("activite", "code_mention_amm"): non_nuls(f"{SPEC}.typeActiviteAMM.mentionAMM"),
    ("activite", "code_pts_amm"): non_nuls(f"{SPEC}.typeActiviteAMM.ptsAMM"),
    ("activite", "code_declaration_amm"): non_nuls(f"{SPEC}.typeActiviteAMM.declarationAMM"),
    ("activite", "type_eml_id"): non_nuls(f"{SPEC}.typeActiviteEML.typeEmlId"),
    ("capacite", "nombre"): non_nuls("capacite[].nombre"),
    ("capacite", "code_statut_capacite"): non_nuls("capacite[].statutCapacite"),
    ("capacite", "code_unite_mesure"): non_nuls("capacite[].uniteMesureCapacite"),
    ("capacite", "code_habilitation"): non_nuls("capacite[].habilitation"),
    ("capacite", "code_type_logement"): non_nuls("capacite[].typeLogement"),
    ("capacite", "code_genre"): non_nuls("capacite[].genre"),
    ("capacite", "code_mode_financement"): non_nuls("capacite[].modeFinancement"),
    ("capacite", "precision"): non_nuls("capacite[].precision"),
    ("capacite", "variation"): non_nuls("capacite[].variation"),
    ("capacite", "engagement_id"): non_nuls("capacite[].engagementId"),
    # Nul par construction : au niveau activite, le porteur n'a pas de numero FINESS.
    # SCHEMA_PIVOT.md declare ce champ nullable pour cette raison precise.
    ("engagement", "num_finess_porteur"): 0,
    ("zone_intervention", "libelle_zone"): non_nuls("zoneIntervention.libelleZI", niveaux=(EJ,)),
    ("appareil", "code_type_appareil"): non_nuls(
        f"{SPEC}.appareil[].typeAppareilAMM", niveaux=(ET,)),
    ("appareil", "nombre_appareil"): non_nuls(
        f"{SPEC}.appareil[].nombreAppareilAMM", niveaux=(ET,)),
    ("appareil", "code_statut_appareil"): non_nuls(
        f"{SPEC}.appareil[].statutAppareilAMM", niveaux=(ET,)),
}

rap = RapportIngestion(Lot("", "", "", "", 0), RegistreAnomalies(), InventaireCodes(),
                       CONTROLE_MINIMAL)
mesure = {}
for nom_type, ligne in parcourir_source(SourceFinessActivites(), FICHIER,
                                        controle=CONTROLE_MINIMAL, rapport=rap,
                                        inventorier_codes=False):
    compte = mesure.get(nom_type)
    if compte is None:
        compte = mesure[nom_type] = [0] * len(ligne)
    for i, v in enumerate(ligne):
        if v is not None:
            compte[i] += 1

types = {t.nom: t for t in fc.TYPES_ACTIVITES}
ecarts, vides = [], []
for nom_type, compte in sorted(mesure.items()):
    for i, champ in enumerate(types[nom_type].noms):
        if compte[i] == 0:
            vides.append((nom_type, champ))
        attendu = ATTENDU.get((nom_type, champ))
        if attendu is not None and attendu != compte[i]:
            ecarts.append((nom_type, champ, attendu, compte[i]))

print(f"Colonnes confrontees au recensement : {len(ATTENDU)}")
if ecarts:
    print(f"ECHEC : {len(ecarts)} ecarts")
    for t, c, a, r in ecarts:
        print(f"   {t}.{c:<34} recensement {a:>9} · pivot {r:>9}")
else:
    print("OK : chaque colonne confrontee porte exactement le nombre de valeurs du JSON")

print(f"\nColonnes entierement nulles : {len(vides)}")
for t, c in vides:
    justifie = ATTENDU.get((t, c)) == 0
    print(f"   {t}.{c:<34} {'conforme au recensement' if justifie else 'A JUSTIFIER'}")
sys.exit(1 if ecarts or any(ATTENDU.get(x) != 0 for x in vides) else 0)
