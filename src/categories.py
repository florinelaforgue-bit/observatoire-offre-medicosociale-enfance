"""
Module d'analyse objective et de recensement des catégories FINESS.
Ne réalise aucun classement ni filtrage thématique.
Compatible Python 3.13 et Termux Android.
"""

from collections import defaultdict


def extraire_categories(etablissements: dict) -> set:
    """
    Extrait l'ensemble des libellés de catégories d'établissements uniques présents
    dans le dictionnaire des établissements.
    """
    categories = set()
    for details in etablissements.values():
        libelle = details.get("libelle_categorie")
        if libelle:
            categories.add(libelle.strip())
    return categories


def compter_categories(etablissements: dict, arborescence_ej: dict = None) -> dict:
    """
    Compte pour chaque catégorie d'établissement le nombre d'établissements (ET)
    et le nombre d'entités juridiques (EJ) distinctes associées.
    """
    # Construction inversée ET -> EJ si l'arborescence est fournie
    et_vers_ej = {}
    if arborescence_ej:
        for ej, liste_et in arborescence_ej.items():
            for et in liste_et:
                et_vers_ej[et] = ej

    stats = defaultdict(lambda: {"nombre": 0, "ej_set": set()})

    for finess_et, details in etablissements.items():
        libelle = details.get("libelle_categorie")
        if not libelle:
            continue
        libelle = libelle.strip()

        stats[libelle]["nombre"] += 1

        # Récupération de l'EJ associée (via le dictionnaire ou les détails)
        ej = details.get("finess_ej_valide") or details.get("finess_ej") or et_vers_ej.get(finess_et)
        if ej:
            stats[libelle]["ej_set"].add(ej)

    # Transformation du set d'EJ en comptage numérique pour le format de sortie
    resultat = {}
    for cat, data in stats.items():
        resultat[cat] = {
            "nombre": data["nombre"],
            "ej": len(data["ej_set"])
        }

    return resultat


def compter_agregats(etablissements: dict) -> dict:
    """
    Recense et compte la fréquence de chaque agrégat de catégories d'établissements
    présent dans la base.
    """
    frequences = defaultdict(int)
    for details in etablissements.values():
        agregat = details.get("categorie_agregat")
        if agregat:
            agregat_clean = agregat.strip()
            frequences[agregat_clean] += 1
            
    return dict(sorted(frequences.items(), key=lambda item: item[1], reverse=True))


def liste_categories_triees(etablissements: dict) -> list:
    """
    Retourne la liste alphabétique de toutes les catégories présentes dans la base.
    """
    return sorted(list(extraire_categories(etablissements)))


def export_categories(etablissements: dict, arborescence_ej: dict = None) -> dict:
    """
    Exporte une photographie structurée contenant les statistiques par catégorie,
    prête à être consommée par les modules d'export (ex: Excel).
    """
    return compter_categories(etablissements, arborescence_ej)
