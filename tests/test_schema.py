"""test_schema.py — Déclarations du schéma, garde-fous et couverture (F1, F5)."""
from __future__ import annotations
import sqlite3, sys

import finess_commun as fc
import schema as s

ok = ko = 0
def verifier(intitule, condition, detail=""):
    global ok, ko
    if condition: ok += 1; print(f"  OK    {intitule}")
    else: ko += 1; print(f"  ECHEC {intitule} — {detail}")

print("1. Construction et dérivation depuis la couche 1")
verifier("16 tables, exactement celles de la couche 1",
         {t.nom for t in s.SCHEMA.tables} == {t.nom for t in fc.TOUS_LES_TYPES})
verifier("les colonnes ne sont pas recopiées mais dérivées",
         all(t.colonnes == t.type_enregistrement.noms for t in s.SCHEMA.tables))
verifier("15 clés primaires, 1 absence justifiée",
         sum(1 for t in s.SCHEMA.tables if t.cle_primaire()) == 15
         and sum(1 for t in s.SCHEMA.tables if t.absence_cle_primaire) == 1)
verifier("engagement_autorite est la table sans clé",
         s.SCHEMA["engagement_autorite"].cle_primaire() is None)
verifier("aucun index de performance déclaré",
         "CREATE INDEX" not in s.SCHEMA.ddl().upper())

print("2. Garde-fous des déclarations")
essais = [
    ("nature de justification inventée",
     lambda: s.Justification("intuition", "t", "src")),
    ("justification vide", lambda: s.Justification(s.ARTEFACT, "  ", "src")),
    ("justification sans source", lambda: s.Justification(s.ARTEFACT, "t", "")),
    ("genre de contrainte inconnu",
     lambda: s.Contrainte("bidule", ("a",), s.REGLE_TYPE_DEFAUT)),
    ("contrainte sans colonne",
     lambda: s.Contrainte(s.UNICITE, (), s.REGLE_TYPE_DEFAUT)),
    ("clé étrangère sans cible",
     lambda: s.Contrainte(s.CLE_ETRANGERE, ("a",), s.REGLE_TYPE_DEFAUT)),
    ("contrôle sans motif de non-déclarabilité",
     lambda: s.ControlePostChargement("n", "d", "SELECT 1", "", s.REGLE_TYPE_DEFAUT)),
]
for intitule, action in essais:
    try:
        action(); verifier(intitule + " refusé", False, "accepté à tort")
    except s.ErreurSchema: verifier(intitule + " refusé", True)

def schema_modifie(**remplacements):
    tables = []
    for t in s.SCHEMA.tables:
        if t.nom in remplacements:
            tables.append(remplacements[t.nom])
        else:
            tables.append(t)
    return s.Schema(tables, s.REGLE_TYPE_DEFAUT, s.JUSTIFICATION_NON_NUL,
                    s.JUSTIFICATION_ABSENCE_INDEX)

print("3. Cohérence globale vérifiée à la construction")
try:
    s.Schema([s.SCHEMA["entete"]], s.REGLE_TYPE_DEFAUT, s.JUSTIFICATION_NON_NUL,
             s.JUSTIFICATION_ABSENCE_INDEX)
    verifier("schéma incomplet refusé", False)
except s.ErreurSchema: verifier("schéma incomplet refusé", True)

try:
    schema_modifie(groupement=s.Table(fc.TYPE_GROUPEMENT))
    verifier("table sans clé ni justification d'absence refusée", False)
except s.ErreurSchema: verifier("table sans clé ni justification d'absence refusée", True)

try:
    schema_modifie(appareil=s.Table(
        fc.TYPE_APPAREIL,
        contraintes=[s.Contrainte(s.CLE_PRIMAIRE, ("colonne_absente",),
                                  s.REGLE_TYPE_DEFAUT)]))
    verifier("colonne inconnue dans une contrainte refusée", False)
except s.ErreurSchema: verifier("colonne inconnue dans une contrainte refusée", True)

try:
    schema_modifie(appareil=s.Table(
        fc.TYPE_APPAREIL,
        contraintes=[
            s.Contrainte(s.CLE_PRIMAIRE, ("activite_ae_id", "rang"), s.REGLE_TYPE_DEFAUT),
            # La relation de la couche 1 reste couverte : c'est bien la cible non
            # unique de la seconde clé qui doit provoquer le refus.
            s.Contrainte(s.CLE_ETRANGERE, ("activite_ae_id",), s.REGLE_TYPE_DEFAUT,
                         "activite", ("activite_ae_id",)),
            s.Contrainte(s.CLE_ETRANGERE, ("code_type_appareil",), s.REGLE_TYPE_DEFAUT,
                         "capacite", ("code_statut_capacite",))]))
    verifier("clé étrangère vers une colonne non unique refusée", False)
except s.ErreurSchema as erreur:
    verifier("clé étrangère vers une colonne non unique refusée",
             "unicité" in str(erreur))

print("4. Couverture des relations déclarées par la couche 1")
couverture = s.SCHEMA.couverture_relations()
verifier("les 13 relations de la couche 1 sont couvertes",
         len(couverture) == 13 and all(couverture.values()), couverture)
verifier("12 par clé étrangère, 1 par contrôle",
         sum(1 for v in couverture.values() if v == "clé étrangère") == 12
         and sum(1 for v in couverture.values() if v.startswith("contrôle")) == 1,
         couverture)
verifier("la relation non déclarable est bien celle des autorités",
         couverture["engagement_autorite.engagement_id -> engagement.engagement_id"]
         .startswith("contrôle"))

sans_fk = s.Table(
    fc.TYPE_CAPACITE,
    contraintes=[s.Contrainte(s.CLE_PRIMAIRE, ("id_capacite",), s.REGLE_TYPE_DEFAUT)])
try:
    schema_modifie(capacite=sans_fk)
    verifier("relation de couche 1 laissée sans couverture → refus", False)
except s.ErreurSchema as erreur:
    verifier("relation de couche 1 laissée sans couverture → refus",
             "n'est couverte" in str(erreur), str(erreur))

print("5. DDL et registre")
connexion = sqlite3.connect(":memory:")
connexion.execute("PRAGMA foreign_keys=ON")
connexion.executescript(s.SCHEMA.ddl())
tables = [r[0] for r in connexion.execute(
    "SELECT name FROM sqlite_master WHERE type='table'")]
verifier("le DDL est accepté par SQLite", len(tables) == 16, tables)
verifier("aucune violation de clé étrangère à vide",
         not list(connexion.execute("PRAGMA foreign_key_check")))
fk = sum(len(list(connexion.execute(f"PRAGMA foreign_key_list({t})"))) for t in tables)
verifier("14 clés étrangères actives", fk == 14, fk)
connexion.close()

registre = s.SCHEMA.registre_markdown()
verifier("le registre cite chaque table",
         all(f"`{t.nom}`" in registre for t in s.SCHEMA.tables))
naturees = [n for n in (s.ARTEFACT, s.MESURE, s.BESOIN) if f"[{n}]" in registre]
verifier("toute justification du registre relève d'une nature déclarée",
         set(naturees) <= {s.ARTEFACT, s.MESURE, s.BESOIN} and len(naturees) >= 2,
         naturees)
verifier("aucune déclaration ne repose sur un besoin fonctionnel à ce jour : "
         "tout procède d'artefacts et de mesures",
         s.BESOIN not in naturees, naturees)
verifier("le registre cite les cinq contrôles et leur motif",
         registre.count("Non déclarable en SQL") == 5,
         registre.count("Non déclarable en SQL"))

print(f"\n{ok} tests réussis, {ko} échecs")
sys.exit(1 if ko else 0)
