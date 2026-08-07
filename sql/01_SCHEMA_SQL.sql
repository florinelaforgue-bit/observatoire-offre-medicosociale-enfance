-- Schéma engendré par schema.py depuis les types d'enregistrements
-- de la couche 1. Ne pas modifier à la main.
-- Aucun index de performance : voir DECISIONS_SCHEMA.md.

CREATE TABLE entete (
    id_lot TEXT NOT NULL,
    source TEXT NOT NULL,
    millesime TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    genere_le TEXT,
    nom_fichier TEXT NOT NULL,
    empreinte TEXT NOT NULL,
    octets TEXT NOT NULL,
    PRIMARY KEY (id_lot)
);

CREATE TABLE entite_juridique (
    num_finess_ej TEXT NOT NULL,
    pm_smsse_id TEXT NOT NULL,
    denomination TEXT NOT NULL,
    denomination_longue TEXT NOT NULL,
    siren TEXT,
    code_ape TEXT,
    code_statut_juridique TEXT NOT NULL,
    code_type_personne_morale TEXT NOT NULL,
    code_fonction_publique TEXT,
    code_type_groupe_gco TEXT,
    complement_adresse TEXT,
    code_categorie TEXT,
    date_creation TEXT NOT NULL,
    date_fermeture TEXT,
    etat_objet TEXT NOT NULL,
    date_derniere_maj TEXT NOT NULL,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (num_finess_ej),
    UNIQUE (pm_smsse_id)
);

CREATE TABLE etablissement (
    num_finess_et TEXT NOT NULL,
    ege_id TEXT NOT NULL,
    num_finess_ej TEXT NOT NULL,
    pm_smsse_id TEXT NOT NULL,
    nom_court TEXT NOT NULL,
    nom_long TEXT NOT NULL,
    complement_denomination TEXT,
    code_categorie TEXT,
    siret TEXT,
    code_espic TEXT,
    numero_uai TEXT,
    numero_reference_externe TEXT,
    code_mode_fixation_tarifaire TEXT,
    code_type_budget TEXT,
    date_ouverture TEXT,
    date_premiere_autorisation TEXT,
    date_fermeture TEXT,
    etat_objet TEXT NOT NULL,
    date_derniere_maj TEXT NOT NULL,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (num_finess_et),
    UNIQUE (ege_id),
    FOREIGN KEY (num_finess_ej) REFERENCES entite_juridique (num_finess_ej)
);

CREATE TABLE adresse (
    type_porteur TEXT NOT NULL,
    id_porteur TEXT NOT NULL,
    num_finess_porteur TEXT NOT NULL,
    rang TEXT NOT NULL,
    code_usage_adresse TEXT NOT NULL,
    numero_voie TEXT,
    code_type_voie TEXT,
    libelle_voie TEXT,
    complement_voie TEXT,
    complement_point_geographique TEXT,
    lieu_dit TEXT,
    code_postal TEXT NOT NULL,
    cog_commune TEXT NOT NULL,
    ligne_acheminement TEXT,
    ligne_une TEXT,
    ligne_deux TEXT,
    ligne_trois TEXT,
    ligne_quatre TEXT,
    ligne_cinq TEXT,
    ligne_six TEXT,
    coordonnee_x TEXT,
    coordonnee_y TEXT,
    direction_latitude TEXT,
    direction_longitude TEXT,
    cle_interop_ban TEXT,
    score_ban TEXT,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (type_porteur, id_porteur, rang)
);

CREATE TABLE contact (
    type_porteur TEXT NOT NULL,
    id_porteur TEXT NOT NULL,
    num_finess_porteur TEXT NOT NULL,
    rang TEXT NOT NULL,
    code_role_contact TEXT NOT NULL,
    telephone TEXT,
    telecopie TEXT,
    courriel TEXT,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (type_porteur, id_porteur, rang)
);

CREATE TABLE engagement (
    engagement_id TEXT NOT NULL,
    type_porteur TEXT NOT NULL,
    id_porteur TEXT NOT NULL,
    num_finess_porteur TEXT,
    rang TEXT NOT NULL,
    code_type_engagement TEXT,
    code_sous_type_engagement TEXT,
    nom_engagement TEXT,
    identifiant_engagement TEXT,
    code_motif_arrete TEXT,
    date_effet TEXT,
    date_signature TEXT,
    date_fin TEXT,
    date_notification TEXT,
    date_caducite TEXT,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (engagement_id, type_porteur, id_porteur)
);

CREATE TABLE engagement_autorite (
    engagement_id TEXT NOT NULL,
    rang TEXT NOT NULL,
    code_autorite_regulation TEXT NOT NULL,
    id_lot TEXT NOT NULL
);

CREATE TABLE evenement (
    evenement_id TEXT NOT NULL,
    type_porteur TEXT NOT NULL,
    id_porteur TEXT NOT NULL,
    rang TEXT NOT NULL,
    code_evenement TEXT NOT NULL,
    date_evenement TEXT NOT NULL,
    date_enregistrement TEXT NOT NULL,
    code_etat_objet_1 TEXT,
    code_type_objet_1 TEXT NOT NULL,
    identifiant_objet_1 TEXT NOT NULL,
    code_type_objet_2 TEXT,
    identifiant_objet_2 TEXT,
    code_systeme_maitre TEXT NOT NULL,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (evenement_id)
);

CREATE TABLE groupement (
    nature_groupement TEXT NOT NULL,
    groupement_id TEXT NOT NULL,
    num_finess_groupement TEXT,
    nom_groupement TEXT,
    code_type_groupement TEXT NOT NULL,
    etat_objet TEXT,
    date_derniere_maj TEXT,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (groupement_id)
);

CREATE TABLE groupement_membre (
    groupement_id TEXT NOT NULL,
    nature_groupement TEXT NOT NULL,
    type_membre TEXT NOT NULL,
    id_membre TEXT NOT NULL,
    code_role_membre TEXT NOT NULL,
    rang TEXT NOT NULL,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (groupement_id, rang),
    FOREIGN KEY (groupement_id) REFERENCES groupement (groupement_id),
    FOREIGN KEY (id_membre) REFERENCES entite_juridique (pm_smsse_id)
);

CREATE TABLE relation_etablissement (
    ege_id TEXT NOT NULL,
    rang TEXT NOT NULL,
    ege_id_porteuse TEXT NOT NULL,
    ege_id_non_porteuse TEXT NOT NULL,
    code_role_relation TEXT NOT NULL,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (ege_id, rang),
    FOREIGN KEY (ege_id) REFERENCES etablissement (ege_id),
    FOREIGN KEY (ege_id_porteuse) REFERENCES etablissement (ege_id),
    FOREIGN KEY (ege_id_non_porteuse) REFERENCES etablissement (ege_id)
);

CREATE TABLE activite (
    niveau TEXT NOT NULL,
    activite_ae_id TEXT NOT NULL,
    num_finess_ej TEXT NOT NULL,
    pm_smsse_id TEXT NOT NULL,
    ege_id TEXT,
    num_finess_et TEXT,
    rang TEXT NOT NULL,
    code_nature TEXT NOT NULL,
    code_type_activite_smsse TEXT NOT NULL,
    etat_objet TEXT NOT NULL,
    identifiant_autorisation TEXT,
    num_autorisation_arhgos TEXT,
    date_debut_activite_autorisee TEXT,
    date_fin_activite_autorisee TEXT,
    date_fin_effective_activite TEXT,
    date_caducite_autorisation TEXT,
    pm_smsse_exploitante_id TEXT,
    ege_exploitante_id TEXT,
    ege_facturante TEXT,
    identifiant_nature TEXT,
    code_activite_regulee TEXT,
    code_mode_fonctionnement TEXT,
    code_public TEXT,
    age_min_autorise TEXT,
    age_max_autorise TEXT,
    age_min_installe TEXT,
    age_max_installe TEXT,
    code_forme_activite TEXT,
    code_modalite_activite TEXT,
    code_modalite_amm TEXT,
    code_mention_amm TEXT,
    code_pts_amm TEXT,
    code_declaration_amm TEXT,
    type_eml_id TEXT,
    marque TEXT,
    numero_serie TEXT,
    code_etat_arhgos TEXT,
    num_decision TEXT,
    date_lim_dep TEXT,
    date_lim_visite_conformite TEXT,
    date_visite TEXT,
    code_resultat_visite TEXT,
    activite_ae_id_specifique TEXT,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (activite_ae_id),
    FOREIGN KEY (num_finess_ej) REFERENCES entite_juridique (num_finess_ej),
    FOREIGN KEY (pm_smsse_id) REFERENCES entite_juridique (pm_smsse_id),
    FOREIGN KEY (num_finess_et) REFERENCES etablissement (num_finess_et),
    FOREIGN KEY (ege_id) REFERENCES etablissement (ege_id)
);

CREATE TABLE capacite (
    id_capacite TEXT NOT NULL,
    niveau TEXT NOT NULL,
    activite_ae_id TEXT NOT NULL,
    rang TEXT NOT NULL,
    nombre TEXT,
    code_statut_capacite TEXT NOT NULL,
    code_unite_mesure TEXT NOT NULL,
    code_habilitation TEXT,
    code_type_logement TEXT,
    code_genre TEXT,
    code_mode_financement TEXT,
    precision TEXT,
    variation TEXT,
    engagement_id TEXT,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (id_capacite),
    FOREIGN KEY (activite_ae_id) REFERENCES activite (activite_ae_id)
);

CREATE TABLE appareil (
    activite_ae_id TEXT NOT NULL,
    rang TEXT NOT NULL,
    code_type_appareil TEXT NOT NULL,
    nombre_appareil TEXT NOT NULL,
    code_statut_appareil TEXT NOT NULL,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (activite_ae_id, rang),
    FOREIGN KEY (activite_ae_id) REFERENCES activite (activite_ae_id)
);

CREATE TABLE zone_intervention (
    zone_intervention_id TEXT NOT NULL,
    activite_ae_id TEXT NOT NULL,
    libelle_zone TEXT,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (zone_intervention_id),
    FOREIGN KEY (activite_ae_id) REFERENCES activite (activite_ae_id)
);

CREATE TABLE zone_intervention_commune (
    zone_intervention_id TEXT NOT NULL,
    rang TEXT NOT NULL,
    cog_commune TEXT NOT NULL,
    id_lot TEXT NOT NULL,
    PRIMARY KEY (zone_intervention_id, rang),
    FOREIGN KEY (zone_intervention_id) REFERENCES zone_intervention (zone_intervention_id)
);
