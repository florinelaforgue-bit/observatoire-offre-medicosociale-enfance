"""
test_controles.py — Couche 0, étape E6.

Éprouve l'index d'identifiants et l'évaluateur de relations sans aucun fichier
FINESS : le module est générique, ses tests doivent l'être aussi.
"""
from __future__ import annotations

import sys

from contrat_source import BLOQUANT, RegistreAnomalies
from controles import (DIFFEREE, LOCALE, ErreurControle, IndexIdentifiants,
                       Relation, VerificateurRelations)

ok = ko = 0


def verifier(intitule, condition, detail=""):
    global ok, ko
    if condition:
        ok += 1
        print(f"  OK    {intitule}")
    else:
        ko += 1
        print(f"  ECHEC {intitule} — {detail}")


print("1. Index d'identifiants : exactitude de l'encodage")
index = IndexIdentifiants("essai")
for v in ("010000024", "10000024", "0", "00", "000", "1", "2A0002638", "2B0003768", "98187"):
    index.ajouter(v)
index.figer()
verifier("zéros de tête préservés",
         "010000024" in index and "10000024" in index and "0010000024" not in index)
verifier("chaînes de zéros distinguées",
         all(v in index for v in ("0", "00", "000")) and "0000" not in index)
verifier("identifiants non numériques conservés littéralement",
         "2A0002638" in index and "2B0003768" in index and "2C0000001" not in index)
verifier("valeur absente correctement rejetée", "999999999" not in index)
verifier("comptage exact", len(index) == 9, len(index))
verifier("part non numérique relevée", index.part_non_numerique() == 2)

collisions = IndexIdentifiants()
for i in range(20000):
    collisions.ajouter(f"{i:09d}")
    collisions.ajouter(str(i))
collisions.figer()
verifier("aucune collision entre formes courtes et formes complétées",
         len(collisions) == 40000, len(collisions))
verifier("appartenance exacte sur 40 000 identifiants",
         all(f"{i:09d}" in collisions and str(i) in collisions for i in range(0, 20000, 997)))
verifier("valeurs absentes rejetées",
         not any(f"9{i:09d}" in collisions for i in range(0, 20000, 997)))

grand = IndexIdentifiants()
for i in range(200000):
    grand.ajouter(f"{i:09d}")
grand.figer()
octets_par_identifiant = grand.octets() / len(grand)
verifier(f"empreinte de {octets_par_identifiant:.1f} octets par identifiant numérique",
         octets_par_identifiant < 12, f"{octets_par_identifiant:.1f}")
verifier("None ignoré", (lambda i: (i.ajouter(None), i.figer(), len(i) == 0)[2])(
    IndexIdentifiants()))

print("2. Index : garde-fous")
try:
    IndexIdentifiants().__contains__("x")
    verifier("interrogation avant figement refusée", False)
except ErreurControle:
    verifier("interrogation avant figement refusée", True)
try:
    fige = IndexIdentifiants()
    fige.figer()
    fige.ajouter("1")
    verifier("ajout après figement refusé", False)
except ErreurControle:
    verifier("ajout après figement refusé", True)
try:
    Relation("a", "b", "c", "d", portee="fantaisie")
    verifier("portée inconnue refusée", False)
except ErreurControle:
    verifier("portée inconnue refusée", True)

print("3. Relations locales")
positions = {"parent": {"cle": 0}, "enfant": {"ref": 0},
             "zone": {"zid": 0}, "commune": {"zid": 0}}
relations = (Relation("enfant", "ref", "parent", "cle", LOCALE),)
registre = RegistreAnomalies()
v = VerificateurRelations(relations, positions, registre)
for nom, ligne in (("parent", ("P1",)), ("enfant", ("P1",)), ("enfant", ("P1",)),
                   ("parent", ("P2",)), ("enfant", ("P2",))):
    v.controler(nom, ligne)
verifier("aucune orpheline sur un flux cohérent",
         v.orphelines["enfant.ref -> parent.cle"] == 0 and registre.bloquantes == 0)
verifier("trois références vérifiées", v.verifiees["enfant.ref -> parent.cle"] == 3)

registre = RegistreAnomalies()
v = VerificateurRelations(relations, positions, registre)
for nom, ligne in (("parent", ("P1",)), ("enfant", ("AUTRE",))):
    v.controler(nom, ligne)
verifier("enfant rattaché à un parent qui n'est pas le sien → bloquant",
         v.orphelines["enfant.ref -> parent.cle"] == 1 and registre.bloquantes == 1)

registre = RegistreAnomalies()
v = VerificateurRelations(relations, positions, registre)
v.controler("enfant", (None,))
verifier("référence nulle comptée à part, jamais orpheline",
         v.ignorees["enfant.ref -> parent.cle"] == 1
         and v.verifiees["enfant.ref -> parent.cle"] == 0 and registre.bloquantes == 0)

print("4. Relations différées")
relations = (Relation("enfant", "ref", "parent", "cle", DIFFEREE),)
registre = RegistreAnomalies()
v = VerificateurRelations(relations, positions, registre)
for cle in ("P1", "P2", "010000024"):
    v.indexer("parent", (cle,))
try:
    v.controler("enfant", ("P1",))
    verifier("contrôle différé avant figement refusé", False)
except ErreurControle:
    verifier("contrôle différé avant figement refusé", True)
v.figer()
for reference in ("P1", "P2", "010000024"):
    v.controler("enfant", (reference,))
verifier("références présentes acceptées", v.orphelines["enfant.ref -> parent.cle"] == 0)
v.controler("enfant", ("INCONNU",))
verifier("référence absente → bloquant",
         v.orphelines["enfant.ref -> parent.cle"] == 1 and registre.bloquantes == 1)
verifier("index dimensionné et mesuré", len(v.index[("parent", "cle")]) == 3
         and v.octets_index() > 0)

print("5. Gravité paramétrable et restitution")
registre = RegistreAnomalies()
v = VerificateurRelations((Relation("enfant", "ref", "parent", "cle", LOCALE,
                                    gravite="avertissement"),), positions, registre)
v.controler("parent", ("P1",))
v.controler("enfant", ("AUTRE",))
verifier("relation déclarée en avertissement ne bloque pas",
         registre.bloquantes == 0 and registre.total() == 1)
verifier("résumé complet", len(v.resume()) == 1 and "PORTÉE" in v.texte())

print("6. Substituabilité de l'index : l'interface est stable, l'algorithme non")


class IndexNaif:
    """Implémentation de référence, volontairement sans optimisation.

    Elle n'offre que le contrat minimal du module. Si le vérificateur se
    comporte identiquement avec elle, c'est que l'encodage entier de
    IndexIdentifiants est bien une optimisation interne, et non une règle
    dont dépendraient les autres modules.
    """

    def __init__(self, nom=""):
        self.nom = nom
        self._valeurs = set()
        self._fige = False

    def ajouter(self, valeur):
        if valeur is None:
            return
        if self._fige:
            raise ErreurControle("index figé")
        self._valeurs.add(valeur)

    def figer(self):
        self._fige = True
        return self

    def __contains__(self, valeur):
        if not self._fige:
            raise ErreurControle("index non figé")
        return valeur in self._valeurs

    def __len__(self):
        return len(self._valeurs)


relations = (Relation("enfant", "ref", "parent", "cle", DIFFEREE),)
identifiants = ["P1", "010000024", "10000024", "2A0002638", "0", "00"]
resultats = {}
for nom_fabrique, fabrique in (("optimisée", IndexIdentifiants), ("naïve", IndexNaif)):
    registre = RegistreAnomalies()
    v = VerificateurRelations(relations, positions, registre, fabrique_index=fabrique)
    for cle in identifiants:
        v.indexer("parent", (cle,))
    v.figer()
    for reference in identifiants + ["INCONNU", "0000", "2C0000001", None]:
        v.controler("enfant", (reference,))
    resultats[nom_fabrique] = (v.resume(), registre.bloquantes, registre.par_code(),
                               len(v.index[("parent", "cle")]))

verifier("comportement observable strictement identique",
         resultats["optimisée"] == resultats["naïve"],
         (resultats["optimisée"], resultats["naïve"]))
verifier("trois références inconnues détectées de part et d'autre",
         resultats["optimisée"][0][0][3] == 3, resultats["optimisée"][0])
verifier("aucune modification requise dans les autres modules",
         VerificateurRelations(relations, positions, RegistreAnomalies()).fabrique_index
         is IndexIdentifiants)

registre = RegistreAnomalies()
v = VerificateurRelations(relations, positions, registre, fabrique_index=IndexNaif)
v.indexer("parent", ("P1",))
v.figer()
verifier("index sans méthode octets() toléré par le rapport",
         v.octets_index() == 0 and "identifiants" in v.texte())

print(f"\n{ok} tests réussis, {ko} échecs")
sys.exit(1 if ko else 0)
