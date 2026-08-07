# BILAN_COUCHE_2.md

**Gel de la couche 2 — entrepôt. Étape F7.**

| | |
|---|---|
| Périmètre gelé | `schema`, `entrepot`, `chargement` |
| Millésime de référence | FINESS 202607 |
| Tests | 101 pour la couche 2, 305 sur le dépôt, aucun échec |
| Dépendances tierces | aucune |
| Code | 1 456 lignes de production, 580 de tests, 328 d'outils de mesure |

---

## 1. Empreintes de gel

| Fichier | SHA-256 (24 premiers caractères) |
|---|---|
| `schema.py` | `9cf9af2a2c13ae3e9cc6ddb2…` |
| `entrepot.py` | `fec354c6054c0edc2f5ae465…` |
| `chargement.py` | `46fcb49c7a489a314bee823f…` |
| `schema.sql` | `adc1b94d2f314a93f3662d66…` |
| `DECISIONS_SCHEMA.md` | `c06184992baa6c82fce325cb…` |
| `test_schema.py` | `dedd8ce39c08149ee1e1b253…` |
| `test_entrepot.py` | `050b23c383ff0548cf19b39e…` |
| `test_chargement.py` | `7ae98383a98c1298d5b64281…` |
| `mesurer_entrepot.py` | `e337dead1f1a529b4d281eae…` |
| `mesurer_chargement.py` | `df7e7142ea85ceb876d20138…` |
| `mesurer_rowid.py` | `7d6cf25dd9a4dc766279f584…` |
| `mesurer_integrite_sql.py` | `c771bb55086c0f539417b43f…` |

---

## 2. Métriques de référence — millésime 202607

Machine de développement. **Aucune mesure sur Termux.**

**Chargement**

| Fichier | Lignes | Durée | RSS max | Base après |
|---|---|---|---|---|
| structures | 1 530 465 | 25,7 s | 72,1 Mio | 236,8 Mio |
| activités | 3 711 869 | 59,3 s | 93,9 Mio | 663,8 Mio |
| **Total** | **5 242 334** | **85,0 s** | **93,9 Mio** | **663,8 Mio** |

Durées mesurées vérification comprise : `foreign_key_check` et les cinq
contrôles déclarés s'exécutent à l'issue de chaque fichier.

**Vérification**

| Opération | Durée | Portée |
|---|---|---|
| `foreign_key_check` | 1,0 s | les 12 relations couvertes par clé étrangère |
| Cinq contrôles déclarés | 1,4 s | la 13ᵉ relation et les rattachements polymorphes |
| `integrity_check` | 4,3 s à chaud | corruption de la base, sans rapport avec les relations |

À froid, la première lecture des 663,8 Mio a été mesurée à environ 31 s pour
`integrity_check`. C'est le chiffre à retenir pour un appareil au stockage lent.

**Structure**

17 index, 96,8 Mio, 14,6 % de la base. Aucun n'est déclaré : SQLite les crée
pour les clés primaires et les contraintes d'unicité. « Aucun index de
performance » ne signifie donc pas « aucune structure d'accès ».

---

## 3. Le schéma

16 tables, dérivées des types d'enregistrements de la couche 1 sans recopie.
15 clés primaires, 1 absence justifiée, 2 contraintes d'unicité, 14 clés
étrangères, 106 colonnes `NOT NULL`, 5 contrôles après chargement, 0 index
déclaré. Toutes les colonnes sont en `TEXT`.

Chaque déclaration porte une justification de nature `artefact`, `mesure` ou
`besoin` ; une déclaration sans justification fait échouer la construction du
schéma. `DECISIONS_SCHEMA.md` est engendré depuis ces déclarations.

---

## 4. Propriétés démontrées

| Propriété | Preuve |
|---|---|
| Le schéma dérive de la couche 1 | Les colonnes proviennent de `TOUS_LES_TYPES` ; un test vérifie l'égalité |
| Aucune déclaration injustifiée | 7 garde-fous éprouvés sur des déclarations fautives fabriquées |
| Une clé étrangère ne peut viser une colonne non unique | Contrôlé à la construction, éprouvé par un test |
| Les 13 relations de la couche 1 sont couvertes | Vérifié à la construction ; retirer une clé étrangère fait échouer le module |
| Chargement complet et exact | 5 242 334 lignes, conformes à la volumétrie de référence |
| Aucune référence orpheline | `foreign_key_check` et les 5 contrôles, tous à zéro sur la base complète |
| Équivalence avec les contrôles Python d'E6 | Même verdict sur données intactes et sur une référence délibérément cassée |
| Mémoire bornée au chargement | 100,1 Mio au pire, mesurée par taille de lot dans des processus distincts |
| Atomicité | Une panne en cours de flux ne laisse aucune ligne en base |
| Idempotence | Rechargement du même fichier refusé ; remplacement sans duplication |
| Cohérence du millésime | Un second millésime est refusé avant toute écriture |
| Les contrôles déclarés détectent ce que SQL ne voit pas | Un rattachement polymorphe orphelin, invisible pour `foreign_key_check`, est détecté |
| Les contrôles déclarés sont exécutés par le chemin nominal | `charger()` les exécute et met l'ingestion en échec sur anomalie ; éprouvé sur un orphelin fabriqué |

---

## 5. Décisions justifiées par la mesure

| Décision | Mesure |
|---|---|
| Réglages SQLite par défaut | 0,73 s à 0,91 s entre toutes les combinaisons de journalisation et de synchronisation, le défaut parmi les plus rapides |
| Taille des lots à 2 000 | 65,6 Mio à 616,7 Mio de mémoire selon le lot, vitesse insensible |
| `WITHOUT ROWID` écarté | 4,0 % de taille gagnée pour 20,2 % de durée perdue sur le chargement complet |
| Aucun index de performance | Le seul besoin de requête documenté s'exécute en 2,4 s sans index supplémentaire |
| Chargement contraintes désactivées | L'ordre du document de la couche 1 n'est pas un ordre d'insertion valide |

Deux campagnes de mesure ont dû être refaites : la première comparaison des
modes de journalisation, faussée par un cache froid, désignait WAL comme
meilleur choix alors que la répétition l'infirme ; la première mesure du coût
de vérification agrégeait `integrity_check` avec les contrôles de relations, ce
qui la rendait ininterprétable.

---

## 6. Limites connues

**Aucune mesure sur Termux.** Toutes les durées viennent d'une machine de
développement. C'est la vérification la plus urgente.

**663,8 Mio pour un millésime.** Volume significatif sur un appareil mobile,
auquel s'ajoute le fichier source de 108 Mio.

**Entrepôt mono-millésime.** Une base ne porte qu'un millésime ; la comparaison
entre millésimes relève des couches supérieures.

**Certaines relations ne sont pas exprimables en SQL** — quatre rattachements
polymorphes et une clé étrangère visant une colonne non unique. Elles sont
couvertes par les cinq contrôles déclarés, que `charger()` exécute sur le
chemin nominal ; une anomalie place l'ingestion en échec.

**`engagement_autorite` n'a pas de clé primaire.** 316 lignes pour 223
combinaisons distinctes sur les trois colonnes disponibles.

**Aucun besoin de requête des couches supérieures n'est documenté.** Le schéma
est donc dimensionné par les seuls artefacts et les contrôles d'intégrité.

**Un seul millésime a été observé.** Rien n'a pu être vérifié sur la stabilité
du schéma d'un mois sur l'autre.

---

## 7. Points explicitement reportés

Aucun ne bloque la V1 ; chacun attend un besoin démontré.

| Point | Motif du report |
|---|---|
| Multi-millésime, `id_lot` dans les clés primaires | Rouvrirait le gel de F1 ; aucun besoin démontré |
| Clé étrangère `id_lot → entete` | Identifiée après le gel de F1 ; amélioration de conception, non un besoin |
| Conversion des colonnes `ENTIER_TEXTE` en entier | Propriété d'absence de perte démontrée sur 4 767 700 valeurs, mais la conversion est une interprétation, que la couche 2 s'interdit |
| `WITHOUT ROWID` | Mesuré, écarté ; à réexaminer si la taille devenait contraignante |
| Index de performance | Aucun tant qu'un besoin de requête n'est pas documenté puis mesuré comme insatisfait |
| Dérogation aux réglages SQLite | Aucune tant que la mesure n'est pas refaite sur Termux |

---
