"""
sources/finess_commun.py — Couche 1 (acquisition), étape E3.

Facteur commun aux deux connecteurs FINESS. Ce fichier n'est pas une couche
supplémentaire : c'est l'endroit unique où sont déclarés les seize types
d'enregistrements du pivot, dont quatre — `adresse`, `contact`, `engagement`,
`evenement` — sont produits par les deux fichiers sources et ne peuvent donc
appartenir ni à l'un ni à l'autre connecteur.

Les déclarations reproduisent SCHEMA_PIVOT.md version 1.0, dans son ordre.
Toute divergence entre ce fichier et le document est un défaut : le document
fait foi.

Les jeux de clés JSON attendus ont été dérivés du recensement exhaustif des
fichiers 202607, non rédigés à la main. Toute clé rencontrée hors de ces jeux
déclenche une anomalie bloquante : le contrat ne se découvre pas à l'exécution.

Aucune dépendance tierce. Compatible Python 3.9+.
"""

from __future__ import annotations

import re
from typing import Any, Dict, FrozenSet, Optional, Sequence

from contrat_source import (
    DATE, ENTIER_TEXTE, HORODATAGE, TEXTE, BLOQUANT,
    Champ, ContexteSource, TypeEnregistrement, TYPE_ENTETE,
)

# ---------------------------------------------------------------------------
# Domaines de nomenclature
# ---------------------------------------------------------------------------
# Un domaine déclaré déclenche l'alimentation automatique de l'inventaire des
# codes. Les codes territoriaux (cog_commune, code_postal) en sont volontairement
# exclus : ils relèvent de la couche `territoires` alimentée par l'INSEE, et
# leur cardinalité saturerait l'inventaire sans rien apprendre.

D_CATEGORIE = "categorie_etablissement"
D_STATUT_JURIDIQUE = "statut_juridique"
D_TYPE_PERSONNE_MORALE = "type_personne_morale"
D_FONCTION_PUBLIQUE = "fonction_publique"
D_TYPE_GROUPE_GCO = "type_groupe_gco"
D_APE = "code_ape"
D_ESPIC = "espic"
D_MODE_FIXATION_TARIFAIRE = "mode_fixation_tarifaire"
D_TYPE_BUDGET = "type_budget"
D_ETAT_OBJET = "etat_objet"
D_USAGE_ADRESSE = "usage_adresse"
D_TYPE_VOIE = "type_voie"
D_ROLE_CONTACT = "role_contact"
D_TYPE_ENGAGEMENT = "type_engagement"
D_SOUS_TYPE_ENGAGEMENT = "sous_type_engagement"
D_MOTIF_ARRETE = "motif_arrete"
D_AUTORITE_REGULATION = "autorite_regulation"
D_CODE_EVENEMENT = "code_evenement"
D_ETAT_OBJET_EVENEMENT = "etat_objet_evenement"
D_TYPE_OBJET = "type_objet_evenement"
D_SYSTEME_MAITRE = "systeme_maitre"
D_TYPE_GROUPEMENT = "type_groupement"
D_ROLE_MEMBRE = "role_membre_groupement"
D_ROLE_RELATION_EGE = "role_relation_ege"
D_NATURE_ACTIVITE = "nature_activite"
D_TYPE_ACTIVITE_SMSSE = "type_activite_smsse"
D_ACTIVITE_REGULEE = "activite_regulee"
D_MODE_FONCTIONNEMENT = "mode_fonctionnement"
D_PUBLIC = "public"
D_FORME_ACTIVITE = "forme_activite"
D_MODALITE_ACTIVITE = "modalite_activite"
D_MODALITE_AMM = "modalite_amm"
D_ETAT_ARHGOS = "etat_arhgos"
D_STATUT_CAPACITE = "statut_capacite"
D_UNITE_MESURE = "unite_mesure_capacite"
D_HABILITATION = "habilitation"
D_TYPE_LOGEMENT = "type_logement"
D_GENRE = "genre"
D_MODE_FINANCEMENT = "mode_financement"
D_TYPE_APPAREIL = "type_appareil"
D_STATUT_APPAREIL = "statut_appareil"

# ---------------------------------------------------------------------------
# Valeurs de discriminants
# ---------------------------------------------------------------------------

PORTEUR_EJ = "EJ"
PORTEUR_ET = "ET"
PORTEUR_GROUPEMENT = "GROUPEMENT"
PORTEUR_ACTIVITE_EJ = "ACTIVITE_EJ"
PORTEUR_ACTIVITE_ET = "ACTIVITE_ET"

NIVEAU_EJ = "EJ"
NIVEAU_ET = "ET"

GROUPEMENT_GCO = "GCO"
GROUPEMENT_GCC = "GCC"

# ---------------------------------------------------------------------------
# Types d'enregistrements — fichier structures
# ---------------------------------------------------------------------------

TYPE_ENTITE_JURIDIQUE = TypeEnregistrement("entite_juridique", [
    Champ("num_finess_ej", TEXTE, obligatoire=True),
    Champ("pm_smsse_id", TEXTE, obligatoire=True),
    Champ("denomination", TEXTE, obligatoire=True),
    Champ("denomination_longue", TEXTE, obligatoire=True),
    Champ("siren", TEXTE),
    Champ("code_ape", TEXTE, domaine=D_APE),
    Champ("code_statut_juridique", TEXTE, obligatoire=True, domaine=D_STATUT_JURIDIQUE),
    Champ("code_type_personne_morale", TEXTE, obligatoire=True, domaine=D_TYPE_PERSONNE_MORALE),
    Champ("code_fonction_publique", TEXTE, domaine=D_FONCTION_PUBLIQUE),
    Champ("code_type_groupe_gco", TEXTE, domaine=D_TYPE_GROUPE_GCO),
    Champ("complement_adresse", TEXTE),
    Champ("code_categorie", TEXTE, domaine=D_CATEGORIE,
          commentaire="Toujours nul au niveau EJ ; conservé par fidélité au schéma source"),
    Champ("date_creation", DATE, obligatoire=True),
    Champ("date_fermeture", DATE),
    Champ("etat_objet", TEXTE, obligatoire=True, domaine=D_ETAT_OBJET),
    Champ("date_derniere_maj", HORODATAGE, obligatoire=True),
    Champ("id_lot", TEXTE, obligatoire=True),
])

TYPE_ETABLISSEMENT = TypeEnregistrement("etablissement", [
    Champ("num_finess_et", TEXTE, obligatoire=True),
    Champ("ege_id", TEXTE, obligatoire=True),
    Champ("num_finess_ej", TEXTE, obligatoire=True),
    Champ("pm_smsse_id", TEXTE, obligatoire=True),
    Champ("nom_court", TEXTE, obligatoire=True),
    Champ("nom_long", TEXTE, obligatoire=True),
    Champ("complement_denomination", TEXTE),
    Champ("code_categorie", TEXTE, domaine=D_CATEGORIE),
    Champ("siret", TEXTE),
    Champ("code_espic", TEXTE, domaine=D_ESPIC),
    Champ("numero_uai", TEXTE),
    Champ("numero_reference_externe", TEXTE),
    Champ("code_mode_fixation_tarifaire", TEXTE, domaine=D_MODE_FIXATION_TARIFAIRE),
    Champ("code_type_budget", TEXTE, domaine=D_TYPE_BUDGET),
    Champ("date_ouverture", DATE),
    Champ("date_premiere_autorisation", DATE),
    Champ("date_fermeture", DATE),
    Champ("etat_objet", TEXTE, obligatoire=True, domaine=D_ETAT_OBJET),
    Champ("date_derniere_maj", HORODATAGE, obligatoire=True),
    Champ("id_lot", TEXTE, obligatoire=True),
])

TYPE_ADRESSE = TypeEnregistrement("adresse", [
    Champ("type_porteur", TEXTE, obligatoire=True),
    Champ("id_porteur", TEXTE, obligatoire=True),
    Champ("num_finess_porteur", TEXTE, obligatoire=True),
    Champ("rang", ENTIER_TEXTE, obligatoire=True),
    Champ("code_usage_adresse", TEXTE, obligatoire=True, domaine=D_USAGE_ADRESSE),
    Champ("numero_voie", TEXTE),
    Champ("code_type_voie", TEXTE, domaine=D_TYPE_VOIE),
    Champ("libelle_voie", TEXTE),
    Champ("complement_voie", TEXTE),
    Champ("complement_point_geographique", TEXTE),
    Champ("lieu_dit", TEXTE),
    Champ("code_postal", TEXTE, obligatoire=True),
    Champ("cog_commune", TEXTE, obligatoire=True,
          commentaire="Code INSEE ; nomenclature confiée à la couche territoires"),
    Champ("ligne_acheminement", TEXTE),
    Champ("ligne_une", TEXTE),
    Champ("ligne_deux", TEXTE),
    Champ("ligne_trois", TEXTE),
    Champ("ligne_quatre", TEXTE),
    Champ("ligne_cinq", TEXTE),
    Champ("ligne_six", TEXTE),
    Champ("coordonnee_x", TEXTE),
    Champ("coordonnee_y", TEXTE),
    Champ("direction_latitude", TEXTE),
    Champ("direction_longitude", TEXTE),
    Champ("cle_interop_ban", TEXTE),
    Champ("score_ban", TEXTE),
    Champ("id_lot", TEXTE, obligatoire=True),
])

TYPE_CONTACT = TypeEnregistrement("contact", [
    Champ("type_porteur", TEXTE, obligatoire=True),
    Champ("id_porteur", TEXTE, obligatoire=True),
    Champ("num_finess_porteur", TEXTE, obligatoire=True),
    Champ("rang", ENTIER_TEXTE, obligatoire=True),
    Champ("code_role_contact", TEXTE, obligatoire=True, domaine=D_ROLE_CONTACT),
    Champ("telephone", TEXTE),
    Champ("telecopie", TEXTE),
    Champ("courriel", TEXTE),
    Champ("id_lot", TEXTE, obligatoire=True),
])

TYPE_ENGAGEMENT = TypeEnregistrement("engagement", [
    Champ("engagement_id", TEXTE, obligatoire=True),
    Champ("type_porteur", TEXTE, obligatoire=True),
    Champ("id_porteur", TEXTE, obligatoire=True),
    Champ("num_finess_porteur", TEXTE),
    Champ("rang", ENTIER_TEXTE, obligatoire=True),
    Champ("code_type_engagement", TEXTE, domaine=D_TYPE_ENGAGEMENT),
    Champ("code_sous_type_engagement", TEXTE, domaine=D_SOUS_TYPE_ENGAGEMENT,
          commentaire="DISP/DIT = fonctionnement en dispositif intégré"),
    Champ("nom_engagement", TEXTE),
    Champ("identifiant_engagement", TEXTE),
    Champ("code_motif_arrete", TEXTE, domaine=D_MOTIF_ARRETE),
    Champ("date_effet", DATE),
    Champ("date_signature", DATE),
    Champ("date_fin", DATE),
    Champ("date_notification", DATE),
    Champ("date_caducite", DATE),
    Champ("id_lot", TEXTE, obligatoire=True),
])

TYPE_ENGAGEMENT_AUTORITE = TypeEnregistrement("engagement_autorite", [
    Champ("engagement_id", TEXTE, obligatoire=True),
    Champ("rang", ENTIER_TEXTE, obligatoire=True),
    Champ("code_autorite_regulation", TEXTE, obligatoire=True, domaine=D_AUTORITE_REGULATION),
    Champ("id_lot", TEXTE, obligatoire=True),
])

TYPE_EVENEMENT = TypeEnregistrement("evenement", [
    Champ("evenement_id", TEXTE, obligatoire=True),
    Champ("type_porteur", TEXTE, obligatoire=True),
    Champ("id_porteur", TEXTE, obligatoire=True),
    Champ("rang", ENTIER_TEXTE, obligatoire=True),
    Champ("code_evenement", TEXTE, obligatoire=True, domaine=D_CODE_EVENEMENT),
    Champ("date_evenement", DATE, obligatoire=True),
    Champ("date_enregistrement", HORODATAGE, obligatoire=True),
    Champ("code_etat_objet_1", TEXTE, domaine=D_ETAT_OBJET_EVENEMENT),
    Champ("code_type_objet_1", TEXTE, obligatoire=True, domaine=D_TYPE_OBJET),
    Champ("identifiant_objet_1", TEXTE, obligatoire=True),
    Champ("code_type_objet_2", TEXTE, domaine=D_TYPE_OBJET),
    Champ("identifiant_objet_2", TEXTE),
    Champ("code_systeme_maitre", TEXTE, obligatoire=True, domaine=D_SYSTEME_MAITRE),
    Champ("id_lot", TEXTE, obligatoire=True),
])

TYPE_GROUPEMENT = TypeEnregistrement("groupement", [
    Champ("nature_groupement", TEXTE, obligatoire=True),
    Champ("groupement_id", TEXTE, obligatoire=True),
    Champ("num_finess_groupement", TEXTE),
    Champ("nom_groupement", TEXTE),
    Champ("code_type_groupement", TEXTE, obligatoire=True, domaine=D_TYPE_GROUPEMENT),
    Champ("etat_objet", TEXTE, domaine=D_ETAT_OBJET),
    Champ("date_derniere_maj", HORODATAGE),
    Champ("id_lot", TEXTE, obligatoire=True),
])

TYPE_GROUPEMENT_MEMBRE = TypeEnregistrement("groupement_membre", [
    Champ("groupement_id", TEXTE, obligatoire=True),
    Champ("nature_groupement", TEXTE, obligatoire=True),
    Champ("type_membre", TEXTE, obligatoire=True),
    Champ("id_membre", TEXTE, obligatoire=True),
    Champ("code_role_membre", TEXTE, obligatoire=True, domaine=D_ROLE_MEMBRE),
    Champ("rang", ENTIER_TEXTE, obligatoire=True),
    Champ("id_lot", TEXTE, obligatoire=True),
])

TYPE_RELATION_ETABLISSEMENT = TypeEnregistrement("relation_etablissement", [
    Champ("ege_id", TEXTE, obligatoire=True),
    Champ("rang", ENTIER_TEXTE, obligatoire=True),
    Champ("ege_id_porteuse", TEXTE, obligatoire=True),
    Champ("ege_id_non_porteuse", TEXTE, obligatoire=True),
    Champ("code_role_relation", TEXTE, obligatoire=True, domaine=D_ROLE_RELATION_EGE),
    Champ("id_lot", TEXTE, obligatoire=True),
])

# ---------------------------------------------------------------------------
# Types d'enregistrements — fichier activités (déclarés ici, utilisés en E4)
# ---------------------------------------------------------------------------

TYPE_ACTIVITE = TypeEnregistrement("activite", [
    Champ("niveau", TEXTE, obligatoire=True),
    Champ("activite_ae_id", TEXTE, obligatoire=True),
    Champ("num_finess_ej", TEXTE, obligatoire=True),
    Champ("pm_smsse_id", TEXTE, obligatoire=True),
    Champ("ege_id", TEXTE),
    Champ("num_finess_et", TEXTE),
    Champ("rang", ENTIER_TEXTE, obligatoire=True),
    Champ("code_nature", TEXTE, obligatoire=True, domaine=D_NATURE_ACTIVITE),
    Champ("code_type_activite_smsse", TEXTE, obligatoire=True, domaine=D_TYPE_ACTIVITE_SMSSE),
    Champ("etat_objet", TEXTE, obligatoire=True, domaine=D_ETAT_OBJET),
    Champ("identifiant_autorisation", TEXTE),
    Champ("num_autorisation_arhgos", TEXTE),
    Champ("date_debut_activite_autorisee", DATE),
    Champ("date_fin_activite_autorisee", DATE),
    Champ("date_fin_effective_activite", DATE),
    Champ("date_caducite_autorisation", DATE),
    Champ("pm_smsse_exploitante_id", TEXTE),
    Champ("ege_exploitante_id", TEXTE),
    Champ("ege_facturante", TEXTE),
    Champ("identifiant_nature", TEXTE,
          commentaire="Fente unique : aaSocialeReguleeId, aaSanitaireDiverseReguleeId, "
                      "aaSoinAmmId, aaSoinAmfId, aaAutreActSoinId ou aaEmlId"),
    Champ("code_activite_regulee", TEXTE, domaine=D_ACTIVITE_REGULEE,
          commentaire="Fente unique ; nomenclature déterminée par code_nature"),
    Champ("code_mode_fonctionnement", TEXTE, domaine=D_MODE_FONCTIONNEMENT),
    Champ("code_public", TEXTE, domaine=D_PUBLIC),
    Champ("age_min_autorise", ENTIER_TEXTE),
    Champ("age_max_autorise", ENTIER_TEXTE),
    Champ("age_min_installe", ENTIER_TEXTE),
    Champ("age_max_installe", ENTIER_TEXTE),
    Champ("code_forme_activite", TEXTE, domaine=D_FORME_ACTIVITE),
    Champ("code_modalite_activite", TEXTE, domaine=D_MODALITE_ACTIVITE),
    Champ("code_modalite_amm", TEXTE, domaine=D_MODALITE_AMM),
    Champ("code_mention_amm", TEXTE),
    Champ("code_pts_amm", TEXTE),
    Champ("code_declaration_amm", TEXTE),
    Champ("type_eml_id", TEXTE),
    Champ("marque", TEXTE),
    Champ("numero_serie", TEXTE),
    Champ("code_etat_arhgos", TEXTE, domaine=D_ETAT_ARHGOS),
    Champ("num_decision", TEXTE),
    Champ("date_lim_dep", DATE),
    Champ("date_lim_visite_conformite", DATE),
    Champ("date_visite", DATE),
    Champ("code_resultat_visite", TEXTE),
    Champ("activite_ae_id_specifique", TEXTE),
    Champ("id_lot", TEXTE, obligatoire=True),
])

TYPE_CAPACITE = TypeEnregistrement("capacite", [
    Champ("id_capacite", TEXTE, obligatoire=True),
    Champ("niveau", TEXTE, obligatoire=True),
    Champ("activite_ae_id", TEXTE, obligatoire=True),
    Champ("rang", ENTIER_TEXTE, obligatoire=True),
    Champ("nombre", ENTIER_TEXTE),
    Champ("code_statut_capacite", TEXTE, obligatoire=True, domaine=D_STATUT_CAPACITE),
    Champ("code_unite_mesure", TEXTE, obligatoire=True, domaine=D_UNITE_MESURE),
    Champ("code_habilitation", TEXTE, domaine=D_HABILITATION),
    Champ("code_type_logement", TEXTE, domaine=D_TYPE_LOGEMENT),
    Champ("code_genre", TEXTE, domaine=D_GENRE),
    Champ("code_mode_financement", TEXTE, domaine=D_MODE_FINANCEMENT),
    Champ("precision", TEXTE),
    Champ("variation", TEXTE),
    Champ("engagement_id", TEXTE),
    Champ("id_lot", TEXTE, obligatoire=True),
])

TYPE_APPAREIL = TypeEnregistrement("appareil", [
    Champ("activite_ae_id", TEXTE, obligatoire=True),
    Champ("rang", ENTIER_TEXTE, obligatoire=True),
    Champ("code_type_appareil", TEXTE, obligatoire=True, domaine=D_TYPE_APPAREIL),
    Champ("nombre_appareil", ENTIER_TEXTE, obligatoire=True),
    Champ("code_statut_appareil", TEXTE, obligatoire=True, domaine=D_STATUT_APPAREIL),
    Champ("id_lot", TEXTE, obligatoire=True),
])

TYPE_ZONE_INTERVENTION = TypeEnregistrement("zone_intervention", [
    Champ("zone_intervention_id", TEXTE, obligatoire=True),
    Champ("activite_ae_id", TEXTE, obligatoire=True),
    Champ("libelle_zone", TEXTE),
    Champ("id_lot", TEXTE, obligatoire=True),
])

TYPE_ZONE_INTERVENTION_COMMUNE = TypeEnregistrement("zone_intervention_commune", [
    Champ("zone_intervention_id", TEXTE, obligatoire=True),
    Champ("rang", ENTIER_TEXTE, obligatoire=True),
    Champ("cog_commune", TEXTE, obligatoire=True),
    Champ("id_lot", TEXTE, obligatoire=True),
])

# ---------------------------------------------------------------------------
# Regroupements par connecteur
# ---------------------------------------------------------------------------

TYPES_STRUCTURES = (
    TYPE_ENTETE, TYPE_ENTITE_JURIDIQUE, TYPE_ETABLISSEMENT, TYPE_ADRESSE,
    TYPE_CONTACT, TYPE_ENGAGEMENT, TYPE_ENGAGEMENT_AUTORITE, TYPE_EVENEMENT,
    TYPE_GROUPEMENT, TYPE_GROUPEMENT_MEMBRE, TYPE_RELATION_ETABLISSEMENT,
)

TYPES_ACTIVITES = (
    TYPE_ENTETE, TYPE_ACTIVITE, TYPE_CAPACITE, TYPE_APPAREIL,
    TYPE_ZONE_INTERVENTION, TYPE_ZONE_INTERVENTION_COMMUNE,
    TYPE_ENGAGEMENT, TYPE_ENGAGEMENT_AUTORITE, TYPE_EVENEMENT,
)

TOUS_LES_TYPES = (
    TYPE_ENTETE, TYPE_ENTITE_JURIDIQUE, TYPE_ETABLISSEMENT, TYPE_ADRESSE,
    TYPE_CONTACT, TYPE_ENGAGEMENT, TYPE_ENGAGEMENT_AUTORITE, TYPE_EVENEMENT,
    TYPE_GROUPEMENT, TYPE_GROUPEMENT_MEMBRE, TYPE_RELATION_ETABLISSEMENT,
    TYPE_ACTIVITE, TYPE_CAPACITE, TYPE_APPAREIL, TYPE_ZONE_INTERVENTION,
    TYPE_ZONE_INTERVENTION_COMMUNE,
)

# ---------------------------------------------------------------------------
# Jeux de clés JSON partagés, dérivés du recensement exhaustif de 202607
# ---------------------------------------------------------------------------

CLES_ADRESSE = frozenset({
    "usageAdresse", "numeroVoie", "typeVoie", "libelleVoie", "complementVoie",
    "complementPointGeographique", "lieuDit", "cogCommune", "codePostal",
    "ligneAcheminement", "ligneUne", "ligneDeux", "ligneTrois", "ligneQuatre",
    "ligneCinq", "ligneSix", "coordonneesGeographique",
})
CLES_COORDONNEES = frozenset({
    "coordonneeX", "coordonneeY", "directionLatitude", "directionLongitude",
    "cleInInteropBAN", "scoreBAN",
})
CLES_CONTACT = frozenset({"typeContact", "telecom"})
CLES_TYPE_CONTACT = frozenset({"roleContact"})
CLES_TELECOM = frozenset({"telephone", "telecopie", "courriel"})
CLES_ENGAGEMENT = frozenset({
    "engagementId", "typeEngagement", "sousTypeEngagement", "nomEngagement",
    "identifiantEngagement", "motifArrete", "dateEffetEngagement",
    "dateSignatureEngagement", "dateFinEngagement", "dateNotificationEngagement",
    "dateCaduciteEngagement", "autoriteRegulationEngagement",
})
CLES_AUTORITE = frozenset({"autoriteRegulationid"})
CLES_EVENEMENT = frozenset({
    "evenementId", "codeEvenement", "dateEvenement", "dateEnregistrement",
    "etatObjet1", "typeObjet1", "identifiantObjet1", "typeObjet2",
    "identifiantObjet2", "systemeMaitre",
})
CLES_MEMBRE_GROUPEMENT = frozenset({"pmSmsseId", "typeRoleEntiteGroupe"})

_MOTIF_MILLESIME = re.compile(r"(\d{6})")


# ---------------------------------------------------------------------------
# Outils partagés
# ---------------------------------------------------------------------------

def extraire_millesime(nom_fichier: str) -> str:
    """Millésime AAAAMM lu dans le nom du fichier.

    Le millésime n'est pas dans le document : `generatedAt` est une date de
    génération, pas une date d'arrêté des données.
    """
    trouve = _MOTIF_MILLESIME.findall(nom_fichier)
    return trouve[-1] if trouve else "inconnu"


def controler_cles(contexte: ContexteSource, chemin: str, objet: Dict[str, Any],
                   attendues: FrozenSet[str]) -> None:
    """Vérifie qu'un objet JSON porte exactement les clés déclarées.

    Toute clé nouvelle ou disparue est bloquante : c'est le filet qui rend
    visible un changement de schéma au lieu de le laisser passer en silence.
    """
    presentes = objet.keys()
    if presentes == attendues:
        return
    for clef in sorted(set(presentes) - attendues):
        contexte.signaler("cle_json_non_declaree", BLOQUANT,
                          type_enregistrement=chemin, champ=clef)
    for clef in sorted(attendues - set(presentes)):
        contexte.signaler("cle_json_absente", BLOQUANT,
                          type_enregistrement=chemin, champ=clef)


def valeur_unique(liste: Optional[Sequence[Any]], contexte: ContexteSource,
                  chemin: str) -> Optional[str]:
    """Aplatit une liste de cardinalité 0 ou 1 en une valeur.

    `typeBudget` et `espic` sont mesurés à cardinalité au plus 1 sur la
    totalité du fichier 202607. Une cardinalité supérieure signalerait que
    l'aplatissement en colonne n'est plus valide : elle est donc bloquante.
    """
    if not liste:
        return None
    if len(liste) > 1:
        contexte.signaler("cardinalite_inattendue", BLOQUANT,
                          type_enregistrement=chemin, detail=str(len(liste)))
    return liste[0]


# ---------------------------------------------------------------------------
# Relations de rattachement du pivot (ajout E6)
# ---------------------------------------------------------------------------
# Déclarations seules ; l'évaluation appartient à `controles`. Les relations
# locales tirent parti du fait que l'enfant suit immédiatement son parent dans
# le flux, ce que garantit l'ordre du document préservé par les connecteurs.

from controles import DIFFEREE, LOCALE, Relation  # noqa: E402

RELATIONS_PIVOT = (
    # Internes à un enregistrement racine : fenêtre d'un élément.
    Relation("capacite", "activite_ae_id", "activite", "activite_ae_id", LOCALE),
    Relation("appareil", "activite_ae_id", "activite", "activite_ae_id", LOCALE),
    Relation("zone_intervention", "activite_ae_id", "activite", "activite_ae_id", LOCALE),
    Relation("zone_intervention_commune", "zone_intervention_id",
             "zone_intervention", "zone_intervention_id", LOCALE),
    Relation("engagement_autorite", "engagement_id", "engagement", "engagement_id", LOCALE),
    Relation("relation_etablissement", "ege_id", "etablissement", "ege_id", LOCALE),
    # Différées, au sein du fichier structures.
    Relation("relation_etablissement", "ege_id_porteuse", "etablissement", "ege_id", DIFFEREE),
    Relation("relation_etablissement", "ege_id_non_porteuse", "etablissement", "ege_id", DIFFEREE),
    Relation("groupement_membre", "id_membre", "entite_juridique", "pm_smsse_id", DIFFEREE),
    # Différées, du fichier activités vers le fichier structures.
    Relation("activite", "num_finess_ej", "entite_juridique", "num_finess_ej", DIFFEREE),
    Relation("activite", "pm_smsse_id", "entite_juridique", "pm_smsse_id", DIFFEREE),
    Relation("activite", "num_finess_et", "etablissement", "num_finess_et", DIFFEREE),
    Relation("activite", "ege_id", "etablissement", "ege_id", DIFFEREE),
)
