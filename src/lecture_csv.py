"""
Module de lecture et d'analyse des fichiers CSV FINESS.
Conçu pour Python 3.13 sous Termux Android.
Lecture optimisée (générateurs, pas de chargement mémoire complet) avec mapping par dictionnaire.
"""

import csv
from pathlib import Path
from collections import defaultdict

# Définition des colonnes attendues selon la nomenclature FINESS ETALAB (si le fichier n'a pas d'en-tête)
COLONNES_FINESS_ETALAB = [
    "type_ligne", "nofinesset", "nofinessej", "rs", "rslongue", "complrs", 
    "compldistrib", "numvoie", "typvoie", "voie", "compvoie", "lieuditbp", 
    "commune", "departement", "libdepartement", "ligneacheminement", 
    "telephone", "telecopie", "categetab", "libcategetab", "categagretab", 
    "libcategagretab", "siret", "codeape", "codemft", "libmft", "codesph", 
    "libsph", "dateouv", "dateautor", "datemaj", "numuai"
]

COLONNES_ETABLISSEMENTS = [
    "type_ligne", "nofinesset", "nofinessej"
]

def detecter_encodage_separateur(filepath: Path) -> tuple[str, str]:
    """
    Détecte automatiquement l'encodage et le séparateur d'un fichier CSV.
    """
    encodages = ['utf-8', 'iso-8859-1', 'cp1252']
    separateur_defaut = ';'
    
    for enc in encodages:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                echantillon = f.read(4096)
                if not echantillon:
                    continue
                try:
                    sniffer = csv.Sniffer()
                    separateur = sniffer.sniff(echantillon).delimiter
                    return enc, separateur
                except csv.Error:
                    # Fallback au comptage si le sniffer échoue
                    if echantillon.count(';') > echantillon.count(','):
                        return enc, ';'
                    if echantillon.count('\t') > echantillon.count(','):
                        return enc, '\t'
                    return enc, ','
        except UnicodeDecodeError:
            continue
            
    return 'utf-8', separateur_defaut

def iterer_lignes_csv_dict(filepath: Path, colonnes_fallback: list[str]) -> map:
    """
    Générateur lisant le fichier ligne par ligne.
    Tente de lire l'en-tête pour nommer les colonnes dynamiquement.
    Si le fichier est au format ETALAB (données directes sans en-tête), utilise le fallback fourni.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Fichier introuvable : {filepath}")
        
    encodage, sep = detecter_encodage_separateur(filepath)
    
    with open(filepath, 'r', encoding=encodage, newline='') as f:
        reader = csv.reader(f, delimiter=sep)
        entetes = None
        
        for ligne in reader:
            if not ligne:
                continue
                
            # Ignorer la ligne de commentaire spécifique à l'export FINESS (ex: finess;etalab;111;...)
            if ligne[0].startswith("finess") and "etalab" in ligne:
                continue
                
            # Détection de l'en-tête (s'il existe)
            if entetes is None:
                if ligne[0] == "structureet":
                    # Pas d'en-tête dans le fichier : les données commencent directement.
                    # On utilise les colonnes du cahier des charges (fallback)
                    entetes = colonnes_fallback
                    # Traiter cette ligne immédiatement car c'est une donnée valide
                    yield dict(zip(entetes, ligne))
                else:
                    # Ligne identifiée comme un en-tête CSV classique
                    entetes = [str(col).strip().lower() for col in ligne]
                continue
                
            # Construction du dictionnaire pour la ligne de données
            if entetes:
                yield dict(zip(entetes, ligne))

def formater_adresse(d: dict) -> str:
    """Reconstitue l'adresse postale complète à partir des différents champs."""
    champs = [
        d.get("numvoie", ""),
        d.get("typvoie", ""),
        d.get("voie", ""),
        d.get("compvoie", ""),
        d.get("lieuditbp", "")
    ]
    return " ".join(c.strip() for c in champs if c and c.strip())

def extraire_cp_ville(ligneacheminement: str) -> tuple[str, str]:
    """Sépare le Code Postal et la Ville depuis la ligne d'acheminement."""
    if not ligneacheminement:
        return "", ""
    parts = ligneacheminement.strip().split(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return ligneacheminement, ""

def construire_correspondances_finess(filepath_etablissements: Path) -> dict:
    """
    Lit le fichier annexe (ex: etablissements.csv) et construit 
    les dictionnaires de rattachement EJ (Entité Juridique) <-> ET (Établissements).
    """
    mapping_ej_vers_et = defaultdict(list)
    mapping_et_vers_ej = {}

    for row in iterer_lignes_csv_dict(filepath_etablissements, COLONNES_ETABLISSEMENTS):
        finess_et = row.get("nofinesset", "").strip()
        finess_ej = row.get("nofinessej", "").strip()
        
        if finess_et and finess_ej:
            mapping_ej_vers_et[finess_ej].append(finess_et)
            mapping_et_vers_ej[finess_et] = finess_ej

    return {
        "ej_vers_et": dict(mapping_ej_vers_et),
        "et_vers_ej": mapping_et_vers_ej
    }

def extraire_donnees_finess(filepath_finess: Path) -> dict:
    """
    Lit le fichier principal finess.csv et en extrait un dictionnaire 
    complet d'informations normalisées par établissement.
    """
    etablissements = {}
    
    for row in iterer_lignes_csv_dict(filepath_finess, COLONNES_FINESS_ETALAB):
        finess_et = row.get("nofinesset", "").strip()
        if not finess_et:
            continue
            
        cp, ville = extraire_cp_ville(row.get("ligneacheminement", ""))
        
        etablissements[finess_et] = {
            # Identifiants
            "finess_et": finess_et,
            "finess_ej": row.get("nofinessej", "").strip(),
            "siret": row.get("siret", "").strip(),
            "code_ape": row.get("codeape", "").strip(),
            
            # Identité / Gestionnaire
            "raison_sociale": row.get("rs", "").strip(),
            "raison_sociale_longue": row.get("rslongue", "").strip(),
            
            # Localisation
            "adresse_complete": formater_adresse(row),
            "code_postal": cp,
            "commune": ville,
            "code_commune_insee": row.get("commune", "").strip(),
            "departement": row.get("departement", "").strip(),
            "libelle_departement": row.get("libdepartement", "").strip(),
            # La région n'est pas nativement dans l'ETALAB, elle devra être déduite par ailleurs
            
            # Caractéristiques (Catégorie, Tarification, Secteur)
            "code_categorie": row.get("categetab", "").strip(),
            "libelle_categorie": row.get("libcategetab", "").strip(),
            "categorie_agregat": row.get("libcategagretab", "").strip(),
            "mode_fixation_tarif": row.get("libmft", "").strip(),
            "service_public_hospitalier": row.get("libsph", "").strip(),
            
            # Dates clés
            "date_ouverture": row.get("dateouv", "").strip(),
            "date_autorisation": row.get("dateautor", "").strip(),
            "date_maj": row.get("datemaj", "").strip(),
            
            # (Note : Les places installées/autorisées se trouvent typiquement dans les 
            # fichiers FINESS d'équipement ou d'autorisations, non présents dans la structure ETALAB ET de base)
        }
        
    return etablissements

def preparer_donnees_observatoire(chemin_finess: str | Path, chemin_etablissements: str | Path) -> dict:
    """
    Fonction principale orchestrant la lecture et la jointure des deux fichiers CSV.
    Fournit un ensemble de données prêt à être consommé par les modules statistiques.
    """
    path_finess = Path(chemin_finess)
    path_etab = Path(chemin_etablissements)
    
    # 1. Correspondances et arborescences (EJ -> ET)
    mappings = construire_correspondances_finess(path_etab)
    
    # 2. Données brutes par établissement
    etablissements = extraire_donnees_finess(path_finess)
    
    # 3. Consolidation et vérification des rattachements juridiques
    for finess_et, details in etablissements.items():
        ej_deduit = mappings["et_vers_ej"].get(finess_et)
        details["finess_ej_valide"] = ej_deduit if ej_deduit else details["finess_ej"]
            
    return {
        "etablissements": etablissements,
        "arborescence_ej": mappings["ej_vers_et"]
    }

if __name__ == "__main__":
    try:
        data = preparer_donnees_observatoire("finess.csv", "etablissements.csv")
        nb_et = len(data["etablissements"])
        nb_ej = len(data["arborescence_ej"])
        print(f"Extraction terminée : {nb_et} ET analysés, répartis sous {nb_ej} EJ.")
        
        # Test sur un élément si disponible
        if nb_et > 0:
            premier_et = next(iter(data["etablissements"].values()))
            print("\nExemple de données extraites :")
            for k, v in premier_et.items():
                print(f" - {k}: {v}")
                
    except Exception as e:
        print(f"Erreur d'exécution : {e}")
