PLAN DE MIGRATION DU MODULE D'ACQUISITION

==================================================
0. PÉRIMÈTRE
==================================================

Cette mission couvre uniquement la couche Acquisition de l'architecture cible :

- flux_json
- contrat_source
- sources/finess_structures
- sources/finess_activites

Le module ne fait que produire des enregistrements plats en mémoire.

Il :

- n'écrit aucune base
- n'utilise pas sqlite3
- ne fait aucun calcul métier
- ne filtre aucune donnée

Il prépare simplement la couche Entrepôt.

==================================================
1. MIGRATION DE lecture_csv.py
==================================================

detecter_encodage
→ supprimé
(JSON est UTF-8)

detecter_separateur
→ supprimé

lire_lignes_finess
→ remplacé par flux_json

lire_horodatage
→ lecture de schemaVersion et generatedAt

lire_etablissements_complets
→ sources/finess_structures

lire_equipements_sociaux
→ sources/finess_activites

lire_correspondances_et_ej
→ supprimé
(le lien ET/EJ est porté par l'imbrication)

construire_correspondance_ej_et
→ supprimé

regrouper_et_par_ej
→ supprimé
(relève désormais de SQL)

indexer_etablissements_par_nofinesset
→ supprimé

regrouper_equipements_par_etablissement
→ supprimé

Etablissement
EquipementSocial

→ remplacés par des enregistrements plats

_signaler_erreur()

→ remplacé par journal + compteurs

Bloc __main__

→ remplacé par une commande CLI.

Décision importante :

Aucune fonction du nouveau module ne construit d'index mémoire.

Toutes les jointures seront réalisées plus tard dans SQLite.

==================================================
2. STREAMING JSON
==================================================

Trois solutions ont été étudiées.

Option A

ijson

Rejetée

Motifs :

- dépendance externe
- installation compliquée sous Termux

Option B

Découpage par indentation

Rejetée

Motifs :

- dépend de la mise en forme
- fragile face aux chaînes JSON

Option C

json.JSONDecoder.raw_decode()

Retenue.

Avantages :

- bibliothèque standard
- robuste
- compatible JSON indenté ou minifié
- mémoire bornée
- aucune dépendance externe

Mesures obtenues :

structures
748 Mio

8 s

127 Mio RSS

activités
1,44 Gio

10,8 s

88 Mio RSS

Avec tampon 256 Kio :

55,6 Mio RSS

Objectif mémoire :

100 Mio maximum sous Termux.

==================================================
3. CONTRAT DE SORTIE
==================================================

Les sorties sont :

- plates
- scalaires
- autoportantes

Jamais :

- objets imbriqués
- arbres JSON
- agrégations

Chaque ligne contient :

- identifiants
- lot d'ingestion
- références parentales

Depuis structures :

- entete
- entite_juridique
- etablissement
- adresse
- contact
- engagement
- engagement_autorite
- evenement
- groupement
- groupement_membre
- relation_etablissement

Depuis activités :

- activite
- capacite
- activite_specificite
- appareil
- zone_intervention
- zone_intervention_commune
- evenement
- engagement
- activite_autorisee_ej
- capacite_autorisee_ej

Décisions importantes :

Le triplet

activité
mode de fonctionnement
public

est aplati dans trois colonnes communes.

Les activités niveau EJ sont conservées malgré leur redondance afin de garantir l'absence de perte d'information.

==================================================
4. CONTRAT PUBLIC
==================================================

Chaque source devra exposer :

- identité
- millésime
- empreinte
- schemaVersion

Inventaire des types produits.

Production :

un générateur unique
un seul passage

Comptage :

- lus
- émis
- ignorés

Registre d'anomalies.

Inventaire des codes rencontrés.

Aucune fonction ne renvoie une collection complète.

==================================================
5. GARANTIES
==================================================

Mémoire bornée.

Lecture en un seul passage.

Aucune perte.

Détection automatique des nouveaux champs.

Aucun échec silencieux.

Résultat déterministe.

==================================================
6. SÉQUENCEMENT
==================================================

E1

flux_json

Validation :

- deux fichiers parcourus
- mémoire <100 Mio
- JSON minifié
- JSON tronqué

E2

contrat_source

Validation :

- compteurs
- anomalies
- source factice

E3

sources/finess_structures

Validation :

- volumétrie conforme
- aucune clé oubliée

E4

sources/finess_activites

Validation :

- volumétrie conforme
- contrôle EJ/ET

E5

Inventaire exhaustif des codes.

E6

Commande CLI d'inspection.

E7

Jeu d'essai figé.

==================================================
7. JEU DE VALIDATION
==================================================

Le jeu de test devra contenir :

- pire cas mémoire
- chaînes échappées
- établissement avec 150 adresses
- EJ sans ET
- ET actif sans activité
- DITEP avec engagement DISP/DIT
- activité EML
- activité avec deux statuts de capacité

Valeurs de référence :

EJ :
98168

ET :
174508

ET actifs :
104699

ET inactifs :
69809

Activités :
292873

Capacités ET :
398537

Capacités EJ :
138696

Evénements structures :
629075

Evénements activités :
1332049

Groupements GCO :
1856

Groupements GCC :
135

Catégories :
301

ET sans activité :
34833

==================================================
8. RISQUES
==================================================

Changement de schéma.

Le détecteur de clés inconnues rend le changement visible.

JSON minifié.

Sans impact.

Temps d'exécution sous Termux.

Quelques minutes par mois.

Enregistrement exceptionnellement volumineux.

Suivi de la taille maximale à chaque exécution.

==================================================
9. HORS PÉRIMÈTRE
==================================================

Pas de SQLite.

Pas de schéma SQL.

Pas de taxonomie.

Pas de nomenclatures.

Pas de calcul métier.

Pas de filtrage.

Pas de jointures.

Le module produit uniquement des données brutes prêtes à être insérées dans l'entrepôt.
