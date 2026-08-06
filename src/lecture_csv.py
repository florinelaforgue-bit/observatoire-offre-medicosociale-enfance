"""
lecture_csv.py

Module de lecture et de préparation des extractions FINESS (Fichier
National des Établissements Sanitaires et Sociaux) pour l'observatoire
national de l'offre médico-sociale et sanitaire destinée aux enfants et
aux adolescents.

Deux structures FINESS réelles sont gérées, telles qu'observées dans les
fichiers fournis :

- "structureet" (32 champs) : fiche complète d'un établissement (ET),
  conforme à la documentation officielle FINESS "etalab_cs1100502"
  (raison sociale, adresse, catégorie, SIRET...). Présente en totalité
  dans finess.csv, et sous forme réduite (3 champs : préfixe, numéro
  FINESS ET, numéro FINESS EJ) dans etablissements.csv, où elle sert de
  table de correspondance entre numéro FINESS géographique (ET) et
  numéro FINESS juridique (EJ).

- "equipementsocial" (28 champs) : activités et capacités sociales ou
  médico-sociales autorisées/installées par établissement, sous forme
  du triplet FINESS classique discipline / mode de fonctionnement /
  clientèle. Présente dans etablissements.csv. La documentation
  officielle de cette structure n'était pas jointe (seule celle de
  "structureet" l'était) : seuls le numéro FINESS et le triplet
  discipline/fonctionnement/clientèle sont donc exposés sous forme de
  champs nommés, les champs suivants (capacités, dates, indicateurs de
  suppression...) étant conservés bruts et dans l'ordre d'origine dans
  `champs_complementaires`, plutôt que renommés sans certitude.

Contraintes de conception :
- Python 3.13, compatible Termux Android.
- Lecture strictement ligne par ligne (générateurs), aucun fichier n'est
  jamais chargé intégralement en mémoire, y compris sur des volumes
  dépassant le million de lignes.
- Seules les fonctions qui construisent explicitement un index de
  correspondance (nécessaire pour permettre des recherches rapides aux
  modules suivants) conservent des données en mémoire ; elles sont
  clairement identifiées comme telles.
- Aucune dépendance tierce : uniquement csv, pathlib et collections
  (bibliothèque standard).
"""

from __future__ import annotations

import csv
from collections import defaultdict, namedtuple
from collections.abc import Iterable, Iterator
from pathlib import Path

__all__ = [
    "Etablissement",
    "EquipementSocial",
    "detecter_encodage",
    "detecter_separateur",
    "lire_lignes_finess",
    "lire_horodatage",
    "lire_etablissements_complets",
    "lire_equipements_sociaux",
    "lire_correspondances_et_ej",
    "construire_correspondance_ej_et",
    "regrouper_et_par_ej",
    "indexer_etablissements_par_nofinesset",
    "regrouper_equipements_par_etablissement",
]


# ---------------------------------------------------------------------------
# Structures de données
# ---------------------------------------------------------------------------

# Fiche établissement complète ("structureet", 32 champs), champs nommés
# d'après la documentation officielle FINESS etalab_cs1100502 (colonne
# "Balise XML").
Etablissement = namedtuple(
    "Etablissement",
    [
        "nofinesset",
        "nofinessej",
        "raison_sociale",
        "raison_sociale_longue",
        "complement_raison_sociale",
        "complement_distribution",
        "numero_voie",
        "type_voie",
        "libelle_voie",
        "complement_voie",
        "lieudit_bp",
        "code_commune",
        "departement",
        "libelle_departement",
        "ligne_acheminement",
        "telephone",
        "telecopie",
        "code_categorie_etablissement",
        "libelle_categorie_etablissement",
        "code_categorie_agregat",
        "libelle_categorie_agregat",
        "siret",
        "code_ape",
        "code_mft",
        "libelle_mft",
        "code_sph",
        "libelle_sph",
        "date_ouverture",
        "date_autorisation",
        "date_maj",
        "numero_uai",
    ],
)

# Ligne d'équipement social/médico-social ("equipementsocial", 28 champs) :
# triplet discipline/fonctionnement/clientèle nommé, reste brut (cf.
# docstring du module).
EquipementSocial = namedtuple(
    "EquipementSocial",
    [
        "nofinesset",
        "code_discipline",
        "libelle_discipline",
        "code_fonctionnement",
        "libelle_fonctionnement",
        "code_clientele",
        "libelle_clientele",
        "champs_complementaires",
    ],
)


# ---------------------------------------------------------------------------
# Utilitaires internes
# ---------------------------------------------------------------------------

def _signaler_erreur(message: str) -> None:
    """Signale une anomalie de lecture sans interrompre le traitement."""
    print(f"[lecture_csv] ATTENTION : {message}")


# ---------------------------------------------------------------------------
# Détection de l'encodage et du séparateur
# ---------------------------------------------------------------------------

_ENCODAGES_A_TESTER = ("utf-8", "cp1252")


def detecter_encodage(chemin: Path) -> str:
    """
    Détecte l'encodage probable d'un fichier texte à partir d'un
    échantillon de ses premiers octets.

    Vérifie d'abord la présence d'un BOM UTF-8, puis tente un décodage
    strict avec chaque encodage candidat. Retourne "latin-1" en dernier
    recours : cet encodage ne lève jamais d'erreur de décodage, quelle
    que soit la suite d'octets rencontrée.
    """
    try:
        with open(chemin, "rb") as fichier_brut:
            echantillon = fichier_brut.read(65536)
    except OSError as erreur:
        raise OSError(f"Impossible de lire {chemin} : {erreur}") from erreur

    if echantillon.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"

    for encodage in _ENCODAGES_A_TESTER:
        try:
            echantillon.decode(encodage)
            return encodage
        except UnicodeDecodeError:
            continue

    return "latin-1"


def detecter_separateur(chemin: Path, encodage: str) -> str:
    """
    Détecte le séparateur de champs utilisé par un fichier FINESS.

    La ligne 1 d'un fichier FINESS est une ligne de commentaire
    (horodatage du flux) et non une ligne de données : la détection se
    fait donc sur la ligne 2. Utilise csv.Sniffer avec un repli sur un
    comptage manuel des séparateurs candidats en cas d'échec (fichier
    trop court, ligne atypique...).
    """
    candidats = [";", ",", "\t", "|"]
    try:
        with open(chemin, "r", encoding=encodage, newline="") as fichier:
            fichier.readline()  # ligne 1 : commentaire, ignorée
            ligne_test = fichier.readline()
    except OSError as erreur:
        raise OSError(f"Impossible de lire {chemin} : {erreur}") from erreur

    try:
        dialecte = csv.Sniffer().sniff(ligne_test, delimiters="".join(candidats))
        return dialecte.delimiter
    except csv.Error:
        pass

    comptes = {candidat: ligne_test.count(candidat) for candidat in candidats}
    meilleur_candidat = max(comptes, key=comptes.get)
    return meilleur_candidat if comptes[meilleur_candidat] > 0 else ";"


# ---------------------------------------------------------------------------
# Lecture bas niveau, ligne par ligne
# ---------------------------------------------------------------------------

def lire_lignes_finess(chemin: Path) -> Iterator[list[str]]:
    """
    Générateur bas niveau : ouvre un fichier d'extraction FINESS, détecte
    automatiquement son encodage et son séparateur, puis produit ses
    lignes de données déjà découpées en champs, une par une.

    La ligne 1 (horodatage du flux, ex. "finess;etalab;113;2026-05-12")
    est ignorée : ce n'est pas une ligne de donnée exploitable. Le
    fichier n'est jamais chargé entièrement en mémoire, quelle que soit
    sa taille.
    """
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")

    encodage = detecter_encodage(chemin)
    separateur = detecter_separateur(chemin, encodage)

    try:
        with open(chemin, "r", encoding=encodage, newline="") as fichier:
            lecteur = csv.reader(fichier, delimiter=separateur)
            try:
                next(lecteur)  # ligne 1 : commentaire d'horodatage
            except StopIteration:
                return
            for ligne in lecteur:
                if ligne:
                    yield ligne
    except OSError as erreur:
        raise OSError(f"Erreur de lecture de {chemin} : {erreur}") from erreur


def lire_horodatage(chemin: Path) -> dict[str, str]:
    """
    Lit la ligne 1 (commentaire d'horodatage) d'un fichier FINESS, par
    exemple "finess;etalab;113;2026-05-12", et la restitue sous forme de
    dictionnaire. Utile aux autres modules pour connaître la fraîcheur
    des données sans avoir à relire tout le fichier.
    """
    encodage = detecter_encodage(chemin)
    separateur = detecter_separateur(chemin, encodage)
    cles = ("emetteur", "destinataire", "version", "date_maj_flux")

    try:
        with open(chemin, "r", encoding=encodage, newline="") as fichier:
            premiere_ligne = fichier.readline()
    except OSError as erreur:
        raise OSError(f"Impossible de lire {chemin} : {erreur}") from erreur

    champs = next(csv.reader([premiere_ligne], delimiter=separateur), [])
    return dict(zip(cles, champs))


# ---------------------------------------------------------------------------
# Lecture des établissements complets ("structureet", 32 champs)
# ---------------------------------------------------------------------------

def lire_etablissements_complets(chemin: Path) -> Iterator[Etablissement]:
    """
    Lit les lignes "structureet" complètes (32 champs) d'un fichier
    FINESS, telles que présentes dans finess.csv, et produit un
    Etablissement par ligne valide. Les lignes au nombre de champs
    inattendu sont ignorées et signalées, sans interrompre la lecture.
    """
    for numero_ligne, champs in enumerate(lire_lignes_finess(chemin), start=2):
        if champs[0] != "structureet" or len(champs) < 32:
            if champs[0] == "structureet":
                _signaler_erreur(
                    f"{chemin.name} ligne {numero_ligne} ignorée "
                    f"({len(champs)} champs au lieu de 32 attendus)"
                )
            continue
        yield Etablissement(
            nofinesset=champs[1],
            nofinessej=champs[2],
            raison_sociale=champs[3],
            raison_sociale_longue=champs[4],
            complement_raison_sociale=champs[5],
            complement_distribution=champs[6],
            numero_voie=champs[7],
            type_voie=champs[8],
            libelle_voie=champs[9],
            complement_voie=champs[10],
            lieudit_bp=champs[11],
            code_commune=champs[12],
            departement=champs[13],
            libelle_departement=champs[14],
            ligne_acheminement=champs[15],
            telephone=champs[16],
            telecopie=champs[17],
            code_categorie_etablissement=champs[18],
            libelle_categorie_etablissement=champs[19],
            code_categorie_agregat=champs[20],
            libelle_categorie_agregat=champs[21],
            siret=champs[22],
            code_ape=champs[23],
            code_mft=champs[24],
            libelle_mft=champs[25],
            code_sph=champs[26],
            libelle_sph=champs[27],
            date_ouverture=champs[28],
            date_autorisation=champs[29],
            date_maj=champs[30],
            numero_uai=champs[31],
        )


# ---------------------------------------------------------------------------
# Lecture des équipements sociaux ("equipementsocial", 28 champs)
# ---------------------------------------------------------------------------

def lire_equipements_sociaux(chemin: Path) -> Iterator[EquipementSocial]:
    """
    Lit les lignes "equipementsocial" d'un fichier FINESS (activités et
    capacités sociales/médico-sociales par établissement, triplet
    discipline / mode de fonctionnement / clientèle), telles que
    présentes dans etablissements.csv, et produit un EquipementSocial par
    ligne valide.
    """
    for numero_ligne, champs in enumerate(lire_lignes_finess(chemin), start=2):
        if champs[0] != "equipementsocial":
            continue
        if len(champs) < 8:
            _signaler_erreur(
                f"{chemin.name} ligne {numero_ligne} ignorée "
                f"({len(champs)} champs, 8 minimum attendus)"
            )
            continue
        yield EquipementSocial(
            nofinesset=champs[1],
            code_discipline=champs[2],
            libelle_discipline=champs[3],
            code_fonctionnement=champs[4],
            libelle_fonctionnement=champs[5],
            code_clientele=champs[6],
            libelle_clientele=champs[7],
            champs_complementaires=tuple(champs[8:]),
        )


# ---------------------------------------------------------------------------
# Correspondance FINESS juridique (EJ) <-> FINESS géographique (ET)
# ---------------------------------------------------------------------------

def lire_correspondances_et_ej(chemin: Path) -> Iterator[tuple[str, str]]:
    """
    Produit les couples (nofinesset, nofinessej) portés par les lignes
    "structureet" d'un fichier FINESS. Fonctionne aussi bien sur les
    lignes réduites à 3 champs (etablissements.csv) que sur les lignes
    complètes à 32 champs (finess.csv), les deux identifiants occupant
    toujours les mêmes positions (champs 2 et 3).
    """
    for numero_ligne, champs in enumerate(lire_lignes_finess(chemin), start=2):
        if champs[0] != "structureet":
            continue
        if len(champs) < 3:
            _signaler_erreur(
                f"{chemin.name} ligne {numero_ligne} ignorée "
                f"({len(champs)} champs, 3 minimum attendus)"
            )
            continue
        yield champs[1], champs[2]


def construire_correspondance_ej_et(chemins: Iterable[Path]) -> dict[str, str]:
    """
    Construit un index nofinesset -> nofinessej à partir d'un ou
    plusieurs fichiers FINESS. Les fichiers sont lus l'un après l'autre
    en flux ; seuls les deux identifiants de chaque ligne sont conservés
    en mémoire (pas les lignes complètes), afin de limiter l'empreinte
    mémoire même sur de gros volumes. En cas de désaccord entre fichiers
    pour un même nofinesset, la dernière valeur lue l'emporte.
    """
    correspondance: dict[str, str] = {}
    for chemin in chemins:
        for nofinesset, nofinessej in lire_correspondances_et_ej(chemin):
            correspondance[nofinesset] = nofinessej
    return correspondance


def regrouper_et_par_ej(correspondance: dict[str, str]) -> dict[str, list[str]]:
    """
    Inverse un index nofinesset -> nofinessej en index
    nofinessej -> liste de nofinesset, une entité juridique (EJ) pouvant
    regrouper plusieurs établissements géographiques (ET).
    """
    par_ej: dict[str, list[str]] = defaultdict(list)
    for nofinesset, nofinessej in correspondance.items():
        par_ej[nofinessej].append(nofinesset)
    return dict(par_ej)


# ---------------------------------------------------------------------------
# Index en mémoire pour les modules suivants
# ---------------------------------------------------------------------------
# Les deux fonctions ci-dessous construisent volontairement des structures
# en mémoire (contrairement aux générateurs précédents) : c'est leur objet,
# afin de permettre des recherches rapides par nofinesset aux modules qui
# utiliseront ce module.

def indexer_etablissements_par_nofinesset(chemin_finess: Path) -> dict[str, Etablissement]:
    """
    Construit un index nofinesset -> Etablissement à partir d'un fichier
    FINESS complet (finess.csv).
    """
    return {etablissement.nofinesset: etablissement for etablissement in lire_etablissements_complets(chemin_finess)}


def regrouper_equipements_par_etablissement(
    chemin_etablissements: Path,
) -> dict[str, list[EquipementSocial]]:
    """
    Regroupe les lignes d'équipements sociaux par numéro FINESS
    d'établissement (nofinesset) à partir de etablissements.csv.
    """
    par_etablissement: dict[str, list[EquipementSocial]] = defaultdict(list)
    for equipement in lire_equipements_sociaux(chemin_etablissements):
        par_etablissement[equipement.nofinesset].append(equipement)
    return dict(par_etablissement)


# ---------------------------------------------------------------------------
# Démonstration (exécution directe du module)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    racine_projet = Path(__file__).resolve().parent.parent
    chemin_etablissements = racine_projet / "data" / "etablissements.csv"
    chemin_finess = racine_projet / "data" / "finess.csv"

    fichiers_manquants = [c for c in (chemin_etablissements, chemin_finess) if not c.exists()]
    if fichiers_manquants:
        for chemin in fichiers_manquants:
            print(f"[lecture_csv] Fichier introuvable : {chemin}")
        print("[lecture_csv] Placez etablissements.csv et finess.csv dans un dossier "
              "data/ à la racine du projet, ou modifiez les chemins en tête de ce bloc.")
        raise SystemExit(1)

    print("=== Démonstration du module lecture_csv ===\n")

    encodage_finess = detecter_encodage(chemin_finess)
    print(f"Encodage détecté ({chemin_finess.name}) : {encodage_finess}")
    print(f"Séparateur détecté ({chemin_finess.name}) : {detecter_separateur(chemin_finess, encodage_finess)!r}")
    print(f"Horodatage du flux ({chemin_finess.name}) : {lire_horodatage(chemin_finess)}")

    print("\nConstruction de la correspondance FINESS juridique <-> géographique...")
    correspondance = construire_correspondance_ej_et([chemin_etablissements, chemin_finess])
    print(f"  {len(correspondance)} correspondances nofinesset -> nofinessej.")

    print("\nIndexation des établissements complets (finess.csv)...")
    index_etablissements = indexer_etablissements_par_nofinesset(chemin_finess)
    print(f"  {len(index_etablissements)} établissements indexés.")
    premier_nofinesset = next(iter(index_etablissements))
    print(f"  Exemple ({premier_nofinesset}) : {index_etablissements[premier_nofinesset]}")

    print("\nRegroupement des équipements sociaux par établissement (etablissements.csv)...")
    equipements_par_etablissement = regrouper_equipements_par_etablissement(chemin_etablissements)
    print(f"  {len(equipements_par_etablissement)} établissements disposent d'au moins un équipement social.")
    for nofinesset, equipements in equipements_par_etablissement.items():
        if len(equipements) > 1:
            print(f"  Exemple multi-équipements ({nofinesset}, {len(equipements)} lignes) :")
            for equipement in equipements[:3]:
                print(
                    f"    - {equipement.libelle_discipline} / "
                    f"{equipement.libelle_fonctionnement} / {equipement.libelle_clientele}"
                )
            break
