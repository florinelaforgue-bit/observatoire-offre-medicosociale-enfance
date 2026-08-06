"""
Module de taxonomie officielle des catégories FINESS.
Contient les règles de classement scientifiques (Handicap, Protection de l'enfance, Sanitaire).
Totalement indépendant des fichiers CSV et des données.
Compatible Python 3.13 et Termux Android.
"""

TAXONOMIE = {
    "Handicap": {
        "IME": {
            "Institut Médico-Educatif (I.M.E.)"
        },
        "ITEP": {
            "Institut Thérapeutique Éducatif et Pédagogique (I.T.E.P.)"
        },
        "SESSAD": {
            "Service d'Éducation Spéciale et de Soins à Domicile"
        },
        "CAMSP": {
            "Centre Action Médico-Sociale Précoce (C.A.M.S.P.)"
        },
        "CMPP": {
            "Centre Médico-Psycho-Pédagogique (C.M.P.P.)"
        },
        "IEM": {
            "Institut d'éducation motrice"
        },
        "EEAP": {
            "Etablissement pour Enfants ou Adolescents Polyhandicapés"
        },
        "DITEP": {
            # Inclus si présent ou variantes
        },
        "Autres structures handicap enfance": {
            "Institut d'Education Sensorielle Sourd/Aveugle",
            "Institut pour Déficients Auditifs",
            "Institut pour Déficients Visuels",
            "Jardin d'Enfants Spécialisé",
            "Foyer Hébergement Enfants et Adolescents Handicapés",
            "Etablissement d'Accueil Temporaire d'Enfants Handicapés",
            "Etablissement Expérimental pour Enfance Handicapée"
        }
    },

    "Protection de l'enfance": {
        "MECS": {
            "Maison d'Enfants à Caractère Social"
        },
        "Prévention spécialisée": {
            "Service de prévention spécialisée"
        },
        "Village d'enfants": {
            "Village d'Enfants"
        },
        "Placement familial": {
            "Service de placement familial",
            "Etablissement de Placement"
        },
        "Pouponnières": {
            "Pouponnière à Caractère Social"
        },
        "Foyer de l'enfance": {
            "Foyer de l'Enfance"
        },
        "Dispositifs ASE / Milieu ouvert": {
            "Service d'Intervention Educative en Milieu Ouvert",
            "Service d'Investigation Educative",
            "Services AEMO et AED",
            "Etablissement Expérimental Enfance Protégée",
            "Etab. de mise à l'abri pour les pers. se déclarant M.N.A.",
            "Serv. d'éval. minorité et isolement pers. se décl. mineures"
        }
    },

    "Sanitaire": {
        "CMP enfant": {
            "Centre Médico-Psychologique (C.M.P.)"
        },
        "CATTP enfant": {
            "Centre d'Accueil Thérapeutique à temps partiel (C.A.T.T.P.)"
        },
        "Hôpital de jour": {
            # Généralement rattaché aux structures de soins / psychiatrie infanto-juvénile
        },
        "Pédopsychiatrie": {
            "Centre Hospitalier Spécialisé lutte Maladies Mentales"
        }
    }
}


def famille(libelle: str) -> str | None:
    """
    Détermine la grande famille (Handicap, Protection de l'enfance, Sanitaire)
    à partir d'un libellé exact de catégorie FINESS.
    Retourne None si le libellé n'est pas répertorié dans la taxonomie.
    """
    if not libelle:
        return None
    lib_clean = libelle.strip()
    for fam, sous_fam_dict in TAXONOMIE.items():
        for sous_fam, libelles_set in sous_fam_dict.items():
            if lib_clean in libelles_set:
                return fam
    return None


def sous_famille(libelle: str) -> str | None:
    """
    Détermine la sous-famille (ex: IME, MECS, SESSAD) à partir d'un libellé 
    exact de catégorie FINESS.
    Retourne None si non trouvé.
    """
    if not libelle:
        return None
    lib_clean = libelle.strip()
    for fam, sous_fam_dict in TAXONOMIE.items():
        for sous_fam, libelles_set in sous_fam_dict.items():
            if lib_clean in libelles_set:
                return sous_fam
    return None


def est_reference(libelle: str) -> bool:
    """
    Vérifie si un libellé de catégorie FINESS fait partie des références 
    connues de la taxonomie.
    """
    return famille(libelle) is not None


def liste_familles() -> list[str]:
    """
    Retourne la liste des grandes familles de la taxonomie.
    """
    return list(TAXONOMIE.keys())


def liste_sous_familles(famille_nom: str = None) -> list[str]:
    """
    Retourne la liste des sous-familles. Si une famille est spécifiée,
    filtre les sous-familles correspondantes.
    """
    resultats = []
    for fam, sous_fam_dict in TAXONOMIE.items():
        if famille_nom is None or fam.lower() == famille_nom.lower():
            resultats.extend(list(sous_fam_dict.keys()))
    return resultats
