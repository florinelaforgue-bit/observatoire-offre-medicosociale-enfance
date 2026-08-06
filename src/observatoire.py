"""
observatoire.py

Script d'orchestration pour l'observatoire. Utilise exclusivement les fonctions publiques
des modules du dossier src/ : lecture_csv, categories, taxonomie, excel.

Compatible Python 3.13 et Termux. Ne crée aucune dépendance supplémentaire.

Ce fichier :
- charge les indices FINESS via lecture_csv
- convertit les namedtuple Etablissement/EquipementSocial en dicts compatibles
  avec categories.py
- calcule des statistiques par catégorie et par agrégat via categories.py
- génère un fichier Excel via src.excel

Contrainte : n'adapte que dans ce fichier les incompatibilités existantes (noms de
champs différents entre lecture_csv.Etablissement et les clés attendues par
categories.py).

"""
from __future__ import annotations

from pathlib import Path
import sys
import argparse
import traceback
from typing import Dict, List, Tuple, Iterable, Any

# Assurer l'import des modules situés dans src/ quel que soit le répertoire de
# lancement : ajouter le dossier src/ au sys.path si nécessaire.
REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Importer les modules publics fournis par le dépôt
import lecture_csv
import categories
import taxonomie
import excel

# ---------------------------------------------------------------------------
# Vérification automatique de l'API publique que nous utiliserons
# ---------------------------------------------------------------------------

_REQUIRED_LECTURE_CSV = [
    "Etablissement",
    "EquipementSocial",
    "detecter_encodage",
    "detecter_separateur",
    "lire_horodatage",
    "lire_etablissements_complets",
    "lire_equipements_sociaux",
    "lire_correspondances_et_ej",
    "construire_correspondance_ej_et",
    "regrouper_et_par_ej",
    "indexer_etablissements_par_nofinesset",
    "regrouper_equipements_par_etablissement",
]

_REQUIRED_CATEGORIES = [
    "extraire_categories",
    "compter_categories",
    "compter_agregats",
    "liste_categories_triees",
    "export_categories",
]

_REQUIRED_TAXONOMIE = [
    "famille",
    "sous_famille",
    "est_reference",
    "liste_familles",
    "liste_sous_familles",
]

_REQUIRED_EXCEL = [
    "creer_classeur",
    "ajouter_feuille",
    "ecrire_tableau",
    "ajuster_colonnes",
    "sauvegarder",
]


def verify_public_api() -> None:
    """Vérifie que les symboles que nous allons utiliser existent bien.

    Lève RuntimeError avec message clair si quelque chose manque.
    """
    missing = []

    for name in _REQUIRED_LECTURE_CSV:
        if not hasattr(lecture_csv, name):
            missing.append(f"lecture_csv.{name}")

    for name in _REQUIRED_CATEGORIES:
        if not hasattr(categories, name):
            missing.append(f"categories.{name}")

    for name in _REQUIRED_TAXONOMIE:
        if not hasattr(taxonomie, name):
            missing.append(f"taxonomie.{name}")

    for name in _REQUIRED_EXCEL:
        if not hasattr(excel, name):
            missing.append(f"excel.{name}")

    if missing:
        raise RuntimeError("API publique manquante dans le dépôt :\n" + "\n".join(missing))


# Appel de vérification immédiat pour échouer tôt si l'environnement est mal
# configuré.
verify_public_api()

# Vérifier que les namedtuple Etablissement et EquipementSocial exposent les
# attributs que nous utiliserons (sécurité contre un renommage accidentel).
ET_FIELDS_REQUIRED = {
    "nofinesset",
    "nofinessej",
    "raison_sociale",
    "libelle_departement",
    "libelle_categorie_etablissement",
    "libelle_categorie_agregat",
}

EQ_FIELDS_REQUIRED = {
    "nofinesset",
    "code_discipline",
    "libelle_discipline",
    "code_fonctionnement",
    "libelle_fonctionnement",
    "code_clientele",
    "libelle_clientele",
    "champs_complementaires",
}


def verify_namedtuple_fields() -> None:
    """Vérifie l'existence des champs utilisés sur les namedtuple.

    Lève RuntimeError si un champ attendu est absent.
    """
    Etab = getattr(lecture_csv, "Etablissement")
    Equip = getattr(lecture_csv, "EquipementSocial")

    et_fields = set(getattr(Etab, "_fields", []))
    eq_fields = set(getattr(Equip, "_fields", []))

    missing = []
    missing_et = ET_FIELDS_REQUIRED - et_fields
    missing_eq = EQ_FIELDS_REQUIRED - eq_fields
    if missing_et:
        missing.extend([f"Etablissement.{f}" for f in sorted(missing_et)])
    if missing_eq:
        missing.extend([f"EquipementSocial.{f}" for f in sorted(missing_eq)])

    if missing:
        raise RuntimeError("Champs attendus manquants dans les namedtuple :\n" + "\n".join(missing))


verify_namedtuple_fields()

# ---------------------------------------------------------------------------
# Conversion des structures nommées (namedtuple) en dict compatibles categories
# ---------------------------------------------------------------------------


def convertir_etablissement(et_raw: "lecture_csv.Etablissement") -> Dict[str, Any]:
    """Convertit un Etablissement (namedtuple) en dict compatible avec
    categories.py.

    Mapping explicite des clés :
    - 'nofinesset' <- et_raw.nofinesset
    - 'finess_ej' <- et_raw.nofinessej
    - 'raison_sociale' <- et_raw.raison_sociale
    - 'libelle_departement' <- et_raw.libelle_departement
    - 'libelle_categorie' <- et_raw.libelle_categorie_etablissement
    - 'categorie_agregat' <- et_raw.libelle_categorie_agregat

    Nous ne supposons rien d'autre ; si un champ est vide, la valeur (str)
    vide est conservée.
    """
    # Accès direct aux attributs du namedtuple (vérifiés plus haut)
    return {
        "nofinesset": et_raw.nofinesset,
        "finess_ej": et_raw.nofinessej,
        "raison_sociale": et_raw.raison_sociale,
        "libelle_departement": et_raw.libelle_departement,
        # alignement des noms de champs : categories attend 'libelle_categorie'
        "libelle_categorie": et_raw.libelle_categorie_etablissement,
        # categories attend 'categorie_agregat'
        "categorie_agregat": et_raw.libelle_categorie_agregat,
    }


def convertir_equipement(eq_raw: "lecture_csv.EquipementSocial") -> Dict[str, Any]:
    """Convertit un EquipementSocial (namedtuple) en dict plat prêt pour export.

    champs_complementaires (tuple[str]) est converti en chaîne joinée pour
    faciliter l'affichage dans Excel.
    """
    champs_comp = eq_raw.champs_complementaires
    if isinstance(champs_comp, tuple):
        champs_comp_str = ";".join(champs_comp)
    else:
        champs_comp_str = str(champs_comp)

    return {
        "nofinesset": eq_raw.nofinesset,
        "code_discipline": eq_raw.code_discipline,
        "libelle_discipline": eq_raw.libelle_discipline,
        "code_fonctionnement": eq_raw.code_fonctionnement,
        "libelle_fonctionnement": eq_raw.libelle_fonctionnement,
        "code_clientele": eq_raw.code_clientele,
        "libelle_clientele": eq_raw.libelle_clientele,
        "champs_complementaires": champs_comp_str,
    }


# ---------------------------------------------------------------------------
# Chargement et préparation des indices
# ---------------------------------------------------------------------------


def charger_indices(chemin_finess: Path, chemin_etablissements: Path) -> Tuple[
    Dict[str, "lecture_csv.Etablissement"], Dict[str, str], Dict[str, List["lecture_csv.EquipementSocial"]]
]:
    """Charge les indices principaux depuis les fichiers FINESS.

    Retourne (index_etablissements_raw, correspondance_et_to_ej, equipements_par_et_raw)
    - index_etablissements_raw: dict[nofinesset, Etablissement]
    - correspondance_et_to_ej: dict[nofinesset, nofinessej]
    - equipements_par_et_raw: dict[nofinesset, list[EquipementSocial]]
    """
    # indexer_etablissements_par_nofinesset lit finess.csv et renvoie un dict en mémoire
    index_etablissements_raw = lecture_csv.indexer_etablissements_par_nofinesset(chemin_finess)

    # construire_correspondance_ej_et prend un iterable de Path
    correspondance = lecture_csv.construire_correspondance_ej_et([chemin_etablissements, chemin_finess])

    # regrouper_equipements_par_etablissement lit etablissements.csv et groupe par nofinesset
    equipements_par_et_raw = lecture_csv.regrouper_equipements_par_etablissement(chemin_etablissements)

    return index_etablissements_raw, correspondance, equipements_par_et_raw


def construire_arborescence_ej(correspondance_et_to_ej: Dict[str, str]) -> Dict[str, List[str]]:
    """Inverse la correspondance (nofinesset->nofinessej) en nofinessej->list[nofinesset].

    Utilise la fonction publique du module lecture_csv.
    """
    return lecture_csv.regrouper_et_par_ej(correspondance_et_to_ej)


def construire_etablissements_normaux(
    index_etablissements_raw: Dict[str, "lecture_csv.Etablissement"],
    equipements_par_et_raw: Dict[str, List["lecture_csv.EquipementSocial"]] | None = None,
) -> Dict[str, Dict[str, Any]]:
    """Convertit tous les Etablissement namedtuple en dicts compatibles avec categories.

    Si equipements_par_et_raw est fourni, convertit et attache la liste d'équipements
    sous la clé 'equipements' pour chaque établissement.

    Retour : dict[nofinesset, details_dict]
    """
    index_normaux: Dict[str, Dict[str, Any]] = {}

    for nofinesset, et_raw in index_etablissements_raw.items():
        details = convertir_etablissement(et_raw)

        # Intégrer les équipements convertis si présents
        if equipements_par_et_raw:
            eq_list_raw = equipements_par_et_raw.get(nofinesset)
            if eq_list_raw:
                details["equipements"] = [convertir_equipement(eq) for eq in eq_list_raw]

        index_normaux[nofinesset] = details

    return index_normaux


# ---------------------------------------------------------------------------
# Calculs statistiques
# ---------------------------------------------------------------------------


def calculer_statistiques_categories(index_etablissements: Dict[str, Dict[str, Any]], arborescence_ej: Dict[str, List[str]] | None = None) -> Dict[str, Any]:
    """Calcule les statistiques par catégorie via categories.export_categories.

    Retourne le dict tel que renvoyé par categories.export_categories.
    """
    return categories.export_categories(index_etablissements, arborescence_ej)


def calculer_statistiques_agregats(index_etablissements: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    """Calcule la fréquence des agrégats via categories.compter_agregats.
    """
    return categories.compter_agregats(index_etablissements)


# ---------------------------------------------------------------------------
# Préparation des lignes pour Excel
# ---------------------------------------------------------------------------


def preparer_lignes_excel_etablissements(index_etablissements: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prépare une liste de dicts pour la feuille 'Etablissements'.

    Colonnes : ['nofinesset','finess_ej','raison_sociale','libelle_departement',
    'libelle_categorie','categorie_agregat','nombre_equipements']
    """
    rows: List[Dict[str, Any]] = []

    for nofinesset, details in index_etablissements.items():
        nombre_equipements = 0
        if "equipements" in details and isinstance(details["equipements"], list):
            nombre_equipements = len(details["equipements"])

        rows.append(
            {
                "nofinesset": nofinesset,
                "finess_ej": details.get("finess_ej", ""),
                "raison_sociale": details.get("raison_sociale", ""),
                "libelle_departement": details.get("libelle_departement", ""),
                "libelle_categorie": details.get("libelle_categorie", ""),
                "categorie_agregat": details.get("categorie_agregat", ""),
                "nombre_equipements": nombre_equipements,
            }
        )

    return rows


def preparer_lignes_excel_equipements(equipements_par_et_raw: Dict[str, List["lecture_csv.EquipementSocial"]]) -> List[Dict[str, Any]]:
    """Prépare une liste de dicts pour la feuille 'Equipements' à partir du raw.

    Chaque équipement devient une ligne.
    """
    rows: List[Dict[str, Any]] = []

    for nofinesset, eq_list in equipements_par_et_raw.items():
        for eq_raw in eq_list:
            eq = convertir_equipement(eq_raw)
            rows.append(eq)

    return rows


def preparer_lignes_excel_categories(categories_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Prépare une liste de dicts pour la feuille 'Categories' à partir du dict de stats.

    Chaque entrée : {'libelle_categorie': str, 'nombre': int, 'ej': int}
    """
    rows: List[Dict[str, Any]] = []
    for libelle, data in categories_stats.items():
        rows.append({"libelle_categorie": libelle, "nombre": data.get("nombre", 0), "ej": data.get("ej", 0)})
    return rows


def preparer_lignes_excel_agregats(agregats_stats: Dict[str, int]) -> List[Dict[str, Any]]:
    """Prépare une liste de dicts pour la feuille 'Agrégats'.

    Chaque entrée : {'categorie_agregat': str, 'nombre': int}
    """
    rows: List[Dict[str, Any]] = []
    for agregat, nombre in agregats_stats.items():
        rows.append({"categorie_agregat": agregat, "nombre": nombre})
    return rows


# ---------------------------------------------------------------------------
# Génération du fichier Excel
# ---------------------------------------------------------------------------


def generer_excel(
    chemin_sortie: Path,
    etablissements_rows: List[Dict[str, Any]],
    equipements_rows: List[Dict[str, Any]],
    categories_rows: List[Dict[str, Any]],
    agregats_rows: List[Dict[str, Any]],
    options: Dict[str, Any] | None = None,
) -> None:
    """Construit et sauvegarde le fichier Excel en utilisant src.excel.

    Utilise exclusivement les fonctions publiques du module excel.
    """
    # Créer le classeur
    wb = excel.creer_classeur()

    # Feuilles et colonnes (ordre explicite)
    feuille_etab = excel.ajouter_feuille(wb, options.get("feuille_etablissements", "Etablissements") if options else "Etablissements")
    feuille_equip = excel.ajouter_feuille(wb, options.get("feuille_equipements", "Equipements") if options else "Equipements")
    feuille_cat = excel.ajouter_feuille(wb, options.get("feuille_categories", "Categories") if options else "Categories")
    feuille_ag = excel.ajouter_feuille(wb, options.get("feuille_agregats", "Agregats") if options else "Agregats")

    # Écrire les tableaux avec colonnes ordonnées
    excel.ecrire_tableau(
        feuille_etab,
        etablissements_rows,
        colonnes=[
            "nofinesset",
            "finess_ej",
            "raison_sociale",
            "libelle_departement",
            "libelle_categorie",
            "categorie_agregat",
            "nombre_equipements",
        ],
    )

    excel.ecrire_tableau(
        feuille_equip,
        equipements_rows,
        colonnes=[
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

    excel.ecrire_tableau(
        feuille_cat,
        categories_rows,
        colonnes=["libelle_categorie", "nombre", "ej"],
    )

    excel.ecrire_tableau(
        feuille_ag,
        agregats_rows,
        colonnes=["categorie_agregat", "nombre"],
    )

    # Sauvegarder
    excel.sauvegarder(wb, chemin_sortie)


# ---------------------------------------------------------------------------
# Rapport console (synthèse)
# ---------------------------------------------------------------------------


def rapport_console(
    index_etablissements: Dict[str, Dict[str, Any]],
    equipements_par_et_raw: Dict[str, List["lecture_csv.EquipementSocial"]],
    categories_stats: Dict[str, Any],
    agregats_stats: Dict[str, int],
) -> None:
    """Affiche une synthèse succincte dans la console.
    """
    total_et = len(index_etablissements)
    total_equip = sum(len(v) for v in equipements_par_et_raw.values()) if equipements_par_et_raw else 0

    print("\n=== Synthèse observatoire ===")
    print(f"Établissements indexés : {total_et}")
    print(f"Lignes équipements total : {total_equip}")
    print(f"Catégories identifiées : {len(categories_stats)}")
    print("Top 10 des catégories (par nombre d'établissement) :")

    # Trier categories_stats par nombre décroissant
    sorted_cats = sorted(categories_stats.items(), key=lambda item: item[1].get("nombre", 0), reverse=True)
    for libelle, data in sorted_cats[:10]:
        print(f" - {libelle}: {data.get('nombre', 0)} établissements, {data.get('ej', 0)} EJ")


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Génère des statistiques et un export Excel pour l'observatoire FINESS.")
    parser.add_argument("--finess", type=Path, default=REPO_ROOT / "data" / "finess.csv", help="Chemin vers finess.csv (par défaut: data/finess.csv)")
    parser.add_argument("--etablissements", type=Path, default=REPO_ROOT / "data" / "etablissements.csv", help="Chemin vers etablissements.csv (par défaut: data/etablissements.csv)")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "outputs" / "observatoire.xlsx", help="Chemin de sortie pour l'Excel (par défaut: outputs/observatoire.xlsx)")
    parser.add_argument("--no-excel", action="store_true", help="Ne pas générer le fichier Excel, afficher uniquement la synthèse")

    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        # Vérifier l'existence des fichiers en amont
        if not args.finess.exists():
            print(f"Fichier introuvable : {args.finess}")
            return 2
        if not args.etablissements.exists():
            print(f"Fichier introuvable : {args.etablissements}")
            return 2

        # 1. Charger indices bruts
        index_etablissements_raw, correspondance_et_to_ej, equipements_par_et_raw = charger_indices(args.finess, args.etablissements)

        # 2. Construire l'arborescence EJ -> [ET]
        arborescence_ej = construire_arborescence_ej(correspondance_et_to_ej)

        # 3. Convertir Etablissement namedtuple -> dict compatible categories
        index_etablissements = construire_etablissements_normaux(index_etablissements_raw, equipements_par_et_raw)

        # Optionnel : libérer l'index raw pour alléger la mémoire
        try:
            del index_etablissements_raw
        except Exception:
            pass

        # 4. Calculer statistiques
        categories_stats = calculer_statistiques_categories(index_etablissements, arborescence_ej)
        agregats_stats = calculer_statistiques_agregats(index_etablissements)

        # 5. Préparer lignes Excel
        etablissements_rows = preparer_lignes_excel_etablissements(index_etablissements)
        equipements_rows = preparer_lignes_excel_equipements(equipements_par_et_raw)
        categories_rows = preparer_lignes_excel_categories(categories_stats)
        agregats_rows = preparer_lignes_excel_agregats(agregats_stats)

        # 6. Générer Excel si demandé
        if not args.no_excel:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            generer_excel(args.output, etablissements_rows, equipements_rows, categories_rows, agregats_rows)
            print(f"Fichier Excel généré : {args.output}")

        # 7. Rapport console
        rapport_console(index_etablissements, equipements_par_et_raw, categories_stats, agregats_stats)

        return 0

    except Exception as e:
        print("Une erreur s'est produite lors de l'exécution :")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
