# DECISIONS_SCHEMA.md

**Registre des justifications du schéma de la couche 2.**

Ce document est **engendré** par `schema.py` depuis les déclarations elles-mêmes. Il n'est jamais rédigé à la main : toute déclaration dépourvue de justification fait échouer la construction du schéma.

Trois natures de justification sont admises : `artefact` — un fait mesuré sur les fichiers FINESS ; `mesure` — une mesure expérimentale ; `besoin` — un besoin fonctionnel documenté.

## Règles générales

**Type de toutes les colonnes : `TEXT`.** [artefact] La couche 1 émet toute valeur en texte, verbatim. 898 numéros FINESS d'établissement et 460 d'entité juridique commencent par 2A ou 2B et ne sont donc pas des entiers. Les onze colonnes numériques par nature ne portent ni zéro de tête, ni valeur négative, ni valeur non numérique sur 4 767 700 valeurs : leur conversion en entier serait possible sans perte, mais elle constituerait une interprétation, que la couche 2 s'interdit. Elle pourra être introduite plus tard sur justification de nature besoin (passe F1, profiler_colonnes.py, fichiers complets 202607)

**Contraintes de non-nullité.** [artefact] Les colonnes portant NOT NULL sont exactement celles déclarées obligatoires dans SCHEMA_PIVOT.md. Le contrôle strict sur les deux fichiers complets n'a relevé aucune valeur nulle sur ces colonnes, sur 5 242 334 lignes (passe F1, profiler_colonnes.py, fichiers complets 202607)

**Aucun index de performance.** [mesure] Aucun index de performance n'est déclaré, et la mesure confirme qu'aucun n'est justifiable. Le seul besoin de requête documenté à ce jour est l'exécution des cinq contrôles après chargement déclarés ci-dessous : ils s'exécutent en 4,1 s sur la base complète de 5 242 334 lignes, le plus coûteux — evenement_porteur_existe, 1 961 124 lignes — en 3,8 s. Les plans d'exécution montrent que les quatre sous-requêtes empruntent les index que SQLite crée automatiquement pour les clés primaires et les contraintes d'unicité : 17 index, 96,8 Mio, soit 14,6 % de la base. Ces index sont donc un effet des contraintes justifiées par artefact, non un choix de performance. Un index supplémentaire ne pourra être déclaré qu'après qu'un besoin de requête des couches supérieures aura été documenté puis mesuré comme insatisfait (étape F4, entrepot.executer_controles() sur la base complète 202607)

## Déclarations par table

### `entete` — 8 colonnes

Une ligne par fichier ingéré. L'identifiant de lot est déterministe : rejouer la même ingestion sur le même fichier produit le même identifiant.

- **Clé primaire** `(id_lot)` — [artefact] 2 lignes, 2 valeurs distinctes, aucune nulle sur entete.id_lot (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Non nulles** : `id_lot`, `source`, `millesime`, `schema_version`, `nom_fichier`, `empreinte`, `octets`

### `entite_juridique` — 17 colonnes

- **Clé primaire** `(num_finess_ej)` — [artefact] 98168 lignes, 98168 valeurs distinctes, aucune nulle sur entite_juridique.num_finess_ej (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Unicité** `(pm_smsse_id)` — [artefact] 98168 lignes, 98168 valeurs distinctes, aucune nulle sur entite_juridique.pm_smsse_id (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Non nulles** : `num_finess_ej`, `pm_smsse_id`, `denomination`, `denomination_longue`, `code_statut_juridique`, `code_type_personne_morale`, `date_creation`, `etat_objet`, `date_derniere_maj`, `id_lot`

### `etablissement` — 20 colonnes

- **Clé primaire** `(num_finess_et)` — [artefact] 174508 lignes, 174508 valeurs distinctes, aucune nulle sur etablissement.num_finess_et (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Unicité** `(ege_id)` — [artefact] 174508 lignes, 174508 valeurs distinctes, aucune nulle sur etablissement.ege_id (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Clé étrangère** `(num_finess_ej)` → `entite_juridique(num_finess_ej)` — [artefact] 174508 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Non nulles** : `num_finess_et`, `ege_id`, `num_finess_ej`, `pm_smsse_id`, `nom_court`, `nom_long`, `etat_objet`, `date_derniere_maj`, `id_lot`

### `adresse` — 27 colonnes

Cardinalité mesurée : une adresse par porteur en médiane, jusqu'à 150.

- **Clé primaire** `(type_porteur, id_porteur, rang)` — [artefact] 278615 lignes, 278615 valeurs distinctes, aucune nulle sur adresse.(type_porteur, id_porteur, rang) (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Non nulles** : `type_porteur`, `id_porteur`, `num_finess_porteur`, `rang`, `code_usage_adresse`, `code_postal`, `cog_commune`, `id_lot`
- **Contrôle après chargement** `adresse_porteur_existe` — Tout porteur d'adresse existe dans entite_juridique ou etablissement, selon la valeur de type_porteur.
    - *Non déclarable en SQL* : Rattachement polymorphe : id_porteur désigne tantôt une entité juridique, tantôt un établissement, selon type_porteur. Aucune clé étrangère SQL ne peut exprimer une cible variable. Scinder la table par type de porteur déformerait le modèle émis par la couche 1
    - [artefact] 278 615 adresses réparties sur 272 676 porteurs, 98 168 entités juridiques et 174 508 établissements (passe F1, profiler_colonnes.py, fichiers complets 202607)

### `contact` — 9 colonnes

Cardinalité mesurée : exactement un contact par porteur sur les 222 505 porteurs, sans exception.

- **Clé primaire** `(type_porteur, id_porteur, rang)` — [artefact] 222505 lignes, 222505 valeurs distinctes, aucune nulle sur contact.(type_porteur, id_porteur, rang) (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Non nulles** : `type_porteur`, `id_porteur`, `num_finess_porteur`, `rang`, `code_role_contact`, `id_lot`
- **Contrôle après chargement** `contact_porteur_existe` — Tout porteur de contact existe dans entite_juridique ou etablissement.
    - *Non déclarable en SQL* : Rattachement polymorphe, comme pour adresse
    - [artefact] 222 505 contacts, un par porteur (passe F1, profiler_colonnes.py, fichiers complets 202607)

### `engagement` — 16 colonnes

engagement_id n'est pas une clé naturelle : 50 identifiants apparaissent plusieurs fois, pour 144 lignes, un même arrêté étant rattaché à plusieurs porteurs. 37 de ces 50 identifiants portent en outre des nom_engagement et identifiant_engagement divergents selon l'occurrence. La table est donc une table de rattachements, et non d'entités ; aucune déduplication n'est opérée.

- **Clé primaire** `(engagement_id, type_porteur, id_porteur)` — [artefact] 77487 lignes, 77487 valeurs distinctes, aucune nulle sur engagement.(engagement_id, type_porteur, id_porteur) (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Non nulles** : `engagement_id`, `type_porteur`, `id_porteur`, `rang`, `id_lot`
- **Contrôle après chargement** `engagement_porteur_existe` — Tout porteur d'engagement existe dans sa table selon type_porteur : EJ, ET, GROUPEMENT ou ACTIVITE_EJ.
    - *Non déclarable en SQL* : Rattachement polymorphe à quatre cibles possibles
    - [artefact] 77 487 engagements : 77 268 issus du fichier structures, 219 du fichier activités (passe F1, profiler_colonnes.py, fichiers complets 202607)

### `engagement_autorite` — 4 colonnes

Table sans clé. 316 lignes pour 223 combinaisons distinctes, y compris en retenant les trois colonnes disponibles : 93 lignes sont des doublons exacts, produits par la réémission des autorités à chaque rattachement de l'engagement. La colonne de porteur qui les distinguerait n'existe pas dans le contrat gelé de la couche 1, et celui-ci n'est pas rouvert pour ce seul cas.

- **Aucune clé primaire** — [artefact] Aucune combinaison de colonnes n'est unique : 316 lignes, 223 distinctes sur (engagement_id, rang, code_autorite_regulation). Déclarer une clé exigerait d'ajouter les colonnes de porteur, donc de modifier le contrat gelé de la couche 1, ce qui a été écarté faute de nécessité démontrée (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Non nulles** : `engagement_id`, `rang`, `code_autorite_regulation`, `id_lot`
- **Contrôle après chargement** `autorite_engagement_existe` — Tout engagement_id référencé existe dans la table engagement.
    - *Non déclarable en SQL* : La clé primaire d'engagement est (engagement_id, type_porteur, id_porteur) ; engagement_id seul n'est pas unique, et SQL n'autorise pas une clé étrangère vers une colonne non unique
    - [artefact] 316 autorités rattachées à 221 engagements distincts, 1,2 autorité par engagement en moyenne, 9 au maximum (passe F1, profiler_colonnes.py, fichiers complets 202607)

### `evenement` — 14 colonnes

1 961 124 lignes : la table la plus volumineuse du pivot. evenement_id est unique sur les deux fichiers réunis.

- **Clé primaire** `(evenement_id)` — [artefact] 1961124 lignes, 1961124 valeurs distinctes, aucune nulle sur evenement.evenement_id (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Non nulles** : `evenement_id`, `type_porteur`, `id_porteur`, `rang`, `code_evenement`, `date_evenement`, `date_enregistrement`, `code_type_objet_1`, `identifiant_objet_1`, `code_systeme_maitre`, `id_lot`
- **Contrôle après chargement** `evenement_porteur_existe` — Tout porteur d'évènement existe dans sa table selon type_porteur : EJ, ET, GROUPEMENT, ACTIVITE_EJ ou ACTIVITE_ET.
    - *Non déclarable en SQL* : Rattachement polymorphe à cinq cibles possibles
    - [artefact] 1 961 124 évènements : 629 075 du fichier structures et 1 332 049 du fichier activités (passe F1, profiler_colonnes.py, fichiers complets 202607)

### `groupement` — 8 colonnes

GCO et GCC réunis. groupement_id reste unique même en confondant les deux natures.

- **Clé primaire** `(groupement_id)` — [artefact] 1991 lignes, 1991 valeurs distinctes, aucune nulle sur groupement.groupement_id (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Non nulles** : `nature_groupement`, `groupement_id`, `code_type_groupement`, `id_lot`

### `groupement_membre` — 7 colonnes

- **Clé primaire** `(groupement_id, rang)` — [artefact] 763 lignes, 763 valeurs distinctes, aucune nulle sur groupement_membre.(groupement_id, rang) (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Clé étrangère** `(groupement_id)` → `groupement(groupement_id)` — [artefact] 763 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Clé étrangère** `(id_membre)` → `entite_juridique(pm_smsse_id)` — [artefact] 763 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Non nulles** : `groupement_id`, `nature_groupement`, `type_membre`, `id_membre`, `code_role_membre`, `rang`, `id_lot`

### `relation_etablissement` — 6 colonnes

- **Clé primaire** `(ege_id, rang)` — [artefact] 47474 lignes, 47474 valeurs distinctes, aucune nulle sur relation_etablissement.(ege_id, rang) (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Clé étrangère** `(ege_id)` → `etablissement(ege_id)` — [artefact] 47474 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Clé étrangère** `(ege_id_porteuse)` → `etablissement(ege_id)` — [artefact] 47474 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Clé étrangère** `(ege_id_non_porteuse)` → `etablissement(ege_id)` — [artefact] 47474 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Non nulles** : `ege_id`, `rang`, `ege_id_porteuse`, `ege_id_non_porteuse`, `code_role_relation`, `id_lot`

### `activite` — 44 colonnes

Les deux niveaux, EJ et ET, coexistent dans une table unique, discriminés par la colonne niveau. Leurs identifiants sont entièrement disjoints : 292 873 au niveau EJ, 292 873 au niveau ET, 585 746 distincts au total. **Aucun lien n'existe dans les données entre une activité autorisée et l'activité exercée correspondante.** Le schéma n'en invente aucun : ce sont deux ensembles indépendants, propriété du millésime observé et non lacune du modèle.

- **Clé primaire** `(activite_ae_id)` — [artefact] 585746 lignes, 585746 valeurs distinctes, aucune nulle sur activite.activite_ae_id (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Clé étrangère** `(num_finess_ej)` → `entite_juridique(num_finess_ej)` — [artefact] 585746 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Clé étrangère** `(pm_smsse_id)` → `entite_juridique(pm_smsse_id)` — [artefact] 585746 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Clé étrangère** `(num_finess_et)` → `etablissement(num_finess_et)` — [artefact] 292873 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Clé étrangère** `(ege_id)` → `etablissement(ege_id)` — [artefact] 292873 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Non nulles** : `niveau`, `activite_ae_id`, `num_finess_ej`, `pm_smsse_id`, `rang`, `code_nature`, `code_type_activite_smsse`, `etat_objet`, `id_lot`

### `capacite` — 15 colonnes

Cardinalité mesurée : 1,9 capacité par activité en moyenne, 26 au maximum. 22 lignes portent un nombre nul.

- **Clé primaire** `(id_capacite)` — [artefact] 537233 lignes, 537233 valeurs distinctes, aucune nulle sur capacite.id_capacite (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Clé étrangère** `(activite_ae_id)` → `activite(activite_ae_id)` — [artefact] 537233 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Non nulles** : `id_capacite`, `niveau`, `activite_ae_id`, `rang`, `code_statut_capacite`, `code_unite_mesure`, `id_lot`

### `appareil` — 6 colonnes

Cardinalité mesurée : exactement 8 appareils sur chacune des 2 012 activités concernées, sans exception.

- **Clé primaire** `(activite_ae_id, rang)` — [artefact] 16096 lignes, 16096 valeurs distinctes, aucune nulle sur appareil.(activite_ae_id, rang) (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Clé étrangère** `(activite_ae_id)` → `activite(activite_ae_id)` — [artefact] 16096 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Non nulles** : `activite_ae_id`, `rang`, `code_type_appareil`, `nombre_appareil`, `code_statut_appareil`, `id_lot`

### `zone_intervention` — 4 colonnes

- **Clé primaire** `(zone_intervention_id)` — [artefact] 8336 lignes, 8336 valeurs distinctes, aucune nulle sur zone_intervention.zone_intervention_id (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Clé étrangère** `(activite_ae_id)` → `activite(activite_ae_id)` — [artefact] 8336 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Non nulles** : `zone_intervention_id`, `activite_ae_id`, `id_lot`

### `zone_intervention_commune` — 4 colonnes

Cardinalité mesurée : 41 communes par zone en médiane, 4 057 au maximum.

- **Clé primaire** `(zone_intervention_id, rang)` — [artefact] 1231970 lignes, 1231970 valeurs distinctes, aucune nulle sur zone_intervention_commune.(zone_intervention_id, rang) (passe F1, verifier_cles.py et verifier_composites.py, fichiers complets 202607)
- **Clé étrangère** `(zone_intervention_id)` → `zone_intervention(zone_intervention_id)` — [artefact] 1231970 rattachements vérifiés, aucune référence orpheline (étape E6, cli.py integrite, 13 relations, 3 687 802 rattachements)
- **Non nulles** : `zone_intervention_id`, `rang`, `cog_commune`, `id_lot`
