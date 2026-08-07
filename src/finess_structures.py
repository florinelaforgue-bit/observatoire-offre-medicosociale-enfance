"""
sources/finess_structures.py — Couche 1 (acquisition), étape E3.

Connecteur du fichier `finess-structures-mensuel`. Il traduit, et rien d'autre :
aucun filtrage de périmètre, aucun libellé résolu, aucun département déduit,
aucun agrégat. Les codes sont émis verbatim, les entités fermées sont chargées
comme les autres.

Un seul passage sur le fichier, à mémoire bornée : un enregistrement racine à
la fois, aucune collection accumulée. Le budget mémoire hérité d'E1 est la
contrainte d'architecture applicable ici.

Aucune dépendance tierce. Compatible Python 3.9+.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple

from contrat_source import BLOQUANT, AVERTISSEMENT, ContexteSource, Source
from flux_json import CLE_ENTETE, parcourir
import finess_commun as fc

__all__ = ["SourceFinessStructures"]

# --- jeux de clés propres à ce fichier, dérivés du recensement exhaustif ----

CLES_RACINE = frozenset({"schemaVersion", "generatedAt", "gco", "gcc", "pmej"})
CLES_ENTETE_SCALAIRES = frozenset({"schemaVersion", "generatedAt"})
CLES_TABLEAUX = ("gco", "gcc", "pmej")

CLES_PMEJ = frozenset({
    "informationsGeneralesPMEJ", "adresse", "contact", "engagement",
    "evenement", "ege", "etatObjet", "dateDerniereMaj",
})
CLES_INFOS_PMEJ = frozenset({
    "pmSmsseId", "numFinessPm", "denominationPm", "denominationLonguePmSmsse",
    "siren", "codeApe", "statutJuridique", "typePersonneMorale",
    "fonctionPublique", "typeGroupeGco", "dateCreation", "dateFermeture",
    "complementAdressePmSmsse", "categorieentiteGeographiqueExercice",
})
CLES_EGE = frozenset({
    "informationsGeneralesEGE", "categorieentiteGeographiqueExercice",
    "modefixationtarifaire", "typeBudget", "adresse", "contact", "engagement",
    "evenement", "roleEge", "etatObjet", "dateDerniereMaj",
})
CLES_INFOS_EGE = frozenset({
    "egeId", "numFinessEge", "nomEgeCourt", "nomEgeLong",
    "complementDenominationEg", "siret", "espic", "numeroEducationNationale",
    "numeroReferenceExterne", "dateOuverture", "datePremiereAutorisation",
    "dateFermeture",
})
CLES_ROLE_EGE = frozenset({"idEgePorteuse", "idEgeNonPorteuse", "roleRelationEge"})
CLES_GCO = frozenset({"pmSmsseId", "typeGco", "pmejDuGco", "egeDuGco"})
CLES_GCC = frozenset({
    "gccId", "nomGcc", "typeGcc", "numFinessGcc", "engagement", "evenement",
    "pmejDuGcc", "egeDuGcc", "etatObjet", "dateDerniereMaj",
})


class SourceFinessStructures(Source):
    """Connecteur du fichier structures mensuel FINESS."""

    nom = "finess_structures"

    def __init__(self, taille_bloc: int = 1 << 18) -> None:
        self.taille_bloc = taille_bloc

    def millesime(self, chemin: Path) -> str:
        return fc.extraire_millesime(Path(chemin).name)

    def types_enregistrements(self):
        return fc.TYPES_STRUCTURES

    # -- production ---------------------------------------------------------

    def produire(self, chemin: Path, contexte: ContexteSource
                 ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        lot = contexte.lot
        entete_emise = False

        for cle_racine, rang, valeur in parcourir(chemin, taille_bloc=self.taille_bloc):

            if cle_racine == CLE_ENTETE:
                nom, contenu = valeur
                if nom not in CLES_ENTETE_SCALAIRES:
                    contexte.signaler("cle_racine_non_declaree", BLOQUANT,
                                      type_enregistrement="racine", champ=nom)
                    continue
                if entete_emise:
                    contexte.signaler("entete_tardive", BLOQUANT,
                                      type_enregistrement="racine", champ=nom)
                    continue
                if nom == "schemaVersion":
                    lot.schema_version = contenu
                else:
                    lot.genere_le = contenu
                continue

            if not entete_emise:
                yield ("entete", lot.ligne_entete())
                entete_emise = True

            if cle_racine not in CLES_TABLEAUX:
                contexte.signaler("tableau_racine_non_declare", BLOQUANT,
                                  type_enregistrement="racine", champ=cle_racine)
                contexte.compter_ignore(cle_racine)
                continue

            contexte.compter_lu(cle_racine)

            if cle_racine == "gco":
                yield from self._groupement_gco(valeur, contexte)
            elif cle_racine == "gcc":
                yield from self._groupement_gcc(valeur, contexte)
            else:
                yield from self._entite_juridique(valeur, contexte)

    # -- entité juridique et ses dépendances --------------------------------

    def _entite_juridique(self, pmej: Dict[str, Any], contexte: ContexteSource
                          ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        lot = contexte.lot
        fc.controler_cles(contexte, "pmej", pmej, CLES_PMEJ)
        infos = pmej.get("informationsGeneralesPMEJ") or {}
        fc.controler_cles(contexte, "pmej.informationsGeneralesPMEJ", infos, CLES_INFOS_PMEJ)

        num_ej = infos.get("numFinessPm")
        pm_id = infos.get("pmSmsseId")

        yield ("entite_juridique", {
            "num_finess_ej": num_ej,
            "pm_smsse_id": pm_id,
            "denomination": infos.get("denominationPm"),
            "denomination_longue": infos.get("denominationLonguePmSmsse"),
            "siren": infos.get("siren"),
            "code_ape": infos.get("codeApe"),
            "code_statut_juridique": infos.get("statutJuridique"),
            "code_type_personne_morale": infos.get("typePersonneMorale"),
            "code_fonction_publique": infos.get("fonctionPublique"),
            "code_type_groupe_gco": infos.get("typeGroupeGco"),
            "complement_adresse": infos.get("complementAdressePmSmsse"),
            "code_categorie": infos.get("categorieentiteGeographiqueExercice"),
            "date_creation": infos.get("dateCreation"),
            "date_fermeture": infos.get("dateFermeture"),
            "etat_objet": pmej.get("etatObjet"),
            "date_derniere_maj": pmej.get("dateDerniereMaj"),
            "id_lot": lot.identifiant,
        })

        yield from self._adresses(pmej.get("adresse"), fc.PORTEUR_EJ, pm_id, num_ej, contexte)
        yield from self._contacts(pmej.get("contact"), fc.PORTEUR_EJ, pm_id, num_ej, contexte)
        yield from self._engagements(pmej.get("engagement"), fc.PORTEUR_EJ, pm_id, num_ej, contexte)
        yield from self._evenements(pmej.get("evenement"), fc.PORTEUR_EJ, pm_id, contexte)

        for ege in pmej.get("ege") or []:
            yield from self._etablissement(ege, num_ej, pm_id, contexte)

    def _etablissement(self, ege: Dict[str, Any], num_ej: Optional[str],
                       pm_id: Optional[str], contexte: ContexteSource
                       ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        lot = contexte.lot
        fc.controler_cles(contexte, "pmej.ege", ege, CLES_EGE)
        infos = ege.get("informationsGeneralesEGE") or {}
        fc.controler_cles(contexte, "pmej.ege.informationsGeneralesEGE", infos, CLES_INFOS_EGE)

        num_et = infos.get("numFinessEge")
        ege_id = infos.get("egeId")

        yield ("etablissement", {
            "num_finess_et": num_et,
            "ege_id": ege_id,
            "num_finess_ej": num_ej,
            "pm_smsse_id": pm_id,
            "nom_court": infos.get("nomEgeCourt"),
            "nom_long": infos.get("nomEgeLong"),
            "complement_denomination": infos.get("complementDenominationEg"),
            "code_categorie": ege.get("categorieentiteGeographiqueExercice"),
            "siret": infos.get("siret"),
            "code_espic": fc.valeur_unique(infos.get("espic"), contexte,
                                           "pmej.ege.informationsGeneralesEGE.espic"),
            "numero_uai": infos.get("numeroEducationNationale"),
            "numero_reference_externe": infos.get("numeroReferenceExterne"),
            "code_mode_fixation_tarifaire": ege.get("modefixationtarifaire"),
            "code_type_budget": fc.valeur_unique(ege.get("typeBudget"), contexte,
                                                  "pmej.ege.typeBudget"),
            "date_ouverture": infos.get("dateOuverture"),
            "date_premiere_autorisation": infos.get("datePremiereAutorisation"),
            "date_fermeture": infos.get("dateFermeture"),
            "etat_objet": ege.get("etatObjet"),
            "date_derniere_maj": ege.get("dateDerniereMaj"),
            "id_lot": lot.identifiant,
        })

        yield from self._adresses(ege.get("adresse"), fc.PORTEUR_ET, ege_id, num_et, contexte)
        yield from self._contacts(ege.get("contact"), fc.PORTEUR_ET, ege_id, num_et, contexte)
        yield from self._engagements(ege.get("engagement"), fc.PORTEUR_ET, ege_id, num_et, contexte)
        yield from self._evenements(ege.get("evenement"), fc.PORTEUR_ET, ege_id, contexte)

        for rang, role in enumerate(ege.get("roleEge") or []):
            fc.controler_cles(contexte, "pmej.ege.roleEge", role, CLES_ROLE_EGE)
            yield ("relation_etablissement", {
                "ege_id": ege_id,
                "rang": str(rang),
                "ege_id_porteuse": role.get("idEgePorteuse"),
                "ege_id_non_porteuse": role.get("idEgeNonPorteuse"),
                "code_role_relation": role.get("roleRelationEge"),
                "id_lot": lot.identifiant,
            })

    # -- blocs partagés entre niveaux ---------------------------------------

    def _adresses(self, adresses, type_porteur: str, id_porteur: Optional[str],
                  num_finess: Optional[str], contexte: ContexteSource
                  ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        lot = contexte.lot
        for rang, adresse in enumerate(adresses or []):
            fc.controler_cles(contexte, f"{type_porteur}.adresse", adresse, fc.CLES_ADRESSE)
            coord = adresse.get("coordonneesGeographique")
            if coord:
                fc.controler_cles(contexte, f"{type_porteur}.adresse.coordonneesGeographique",
                                  coord, fc.CLES_COORDONNEES)
            else:
                coord = {}
            yield ("adresse", {
                "type_porteur": type_porteur,
                "id_porteur": id_porteur,
                "num_finess_porteur": num_finess,
                "rang": str(rang),
                "code_usage_adresse": adresse.get("usageAdresse"),
                "numero_voie": adresse.get("numeroVoie"),
                "code_type_voie": adresse.get("typeVoie"),
                "libelle_voie": adresse.get("libelleVoie"),
                "complement_voie": adresse.get("complementVoie"),
                "complement_point_geographique": adresse.get("complementPointGeographique"),
                "lieu_dit": adresse.get("lieuDit"),
                "code_postal": adresse.get("codePostal"),
                "cog_commune": adresse.get("cogCommune"),
                "ligne_acheminement": adresse.get("ligneAcheminement"),
                "ligne_une": adresse.get("ligneUne"),
                "ligne_deux": adresse.get("ligneDeux"),
                "ligne_trois": adresse.get("ligneTrois"),
                "ligne_quatre": adresse.get("ligneQuatre"),
                "ligne_cinq": adresse.get("ligneCinq"),
                "ligne_six": adresse.get("ligneSix"),
                "coordonnee_x": coord.get("coordonneeX"),
                "coordonnee_y": coord.get("coordonneeY"),
                "direction_latitude": coord.get("directionLatitude"),
                "direction_longitude": coord.get("directionLongitude"),
                "cle_interop_ban": coord.get("cleInInteropBAN"),
                "score_ban": coord.get("scoreBAN"),
                "id_lot": lot.identifiant,
            })

    def _contacts(self, contacts, type_porteur: str, id_porteur: Optional[str],
                  num_finess: Optional[str], contexte: ContexteSource
                  ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        lot = contexte.lot
        for rang, contact in enumerate(contacts or []):
            fc.controler_cles(contexte, f"{type_porteur}.contact", contact, fc.CLES_CONTACT)
            type_contact = contact.get("typeContact") or {}
            telecom = contact.get("telecom") or {}
            fc.controler_cles(contexte, f"{type_porteur}.contact.typeContact",
                              type_contact, fc.CLES_TYPE_CONTACT)
            fc.controler_cles(contexte, f"{type_porteur}.contact.telecom",
                              telecom, fc.CLES_TELECOM)
            yield ("contact", {
                "type_porteur": type_porteur,
                "id_porteur": id_porteur,
                "num_finess_porteur": num_finess,
                "rang": str(rang),
                "code_role_contact": type_contact.get("roleContact"),
                "telephone": telecom.get("telephone"),
                "telecopie": telecom.get("telecopie"),
                "courriel": telecom.get("courriel"),
                "id_lot": lot.identifiant,
            })

    def _engagements(self, engagements, type_porteur: str, id_porteur: Optional[str],
                     num_finess: Optional[str], contexte: ContexteSource
                     ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        lot = contexte.lot
        for rang, engagement in enumerate(engagements or []):
            fc.controler_cles(contexte, f"{type_porteur}.engagement",
                              engagement, fc.CLES_ENGAGEMENT)
            engagement_id = engagement.get("engagementId")
            yield ("engagement", {
                "engagement_id": engagement_id,
                "type_porteur": type_porteur,
                "id_porteur": id_porteur,
                "num_finess_porteur": num_finess,
                "rang": str(rang),
                "code_type_engagement": engagement.get("typeEngagement"),
                "code_sous_type_engagement": engagement.get("sousTypeEngagement"),
                "nom_engagement": engagement.get("nomEngagement"),
                "identifiant_engagement": engagement.get("identifiantEngagement"),
                "code_motif_arrete": engagement.get("motifArrete"),
                "date_effet": engagement.get("dateEffetEngagement"),
                "date_signature": engagement.get("dateSignatureEngagement"),
                "date_fin": engagement.get("dateFinEngagement"),
                "date_notification": engagement.get("dateNotificationEngagement"),
                "date_caducite": engagement.get("dateCaduciteEngagement"),
                "id_lot": lot.identifiant,
            })
            for rang_autorite, autorite in enumerate(
                    engagement.get("autoriteRegulationEngagement") or []):
                fc.controler_cles(contexte, f"{type_porteur}.engagement.autoriteRegulation",
                                  autorite, fc.CLES_AUTORITE)
                yield ("engagement_autorite", {
                    "engagement_id": engagement_id,
                    "rang": str(rang_autorite),
                    "code_autorite_regulation": autorite.get("autoriteRegulationid"),
                    "id_lot": lot.identifiant,
                })

    def _evenements(self, evenements, type_porteur: str, id_porteur: Optional[str],
                    contexte: ContexteSource) -> Iterator[Tuple[str, Dict[str, Any]]]:
        lot = contexte.lot
        for rang, evenement in enumerate(evenements or []):
            fc.controler_cles(contexte, f"{type_porteur}.evenement",
                              evenement, fc.CLES_EVENEMENT)
            yield ("evenement", {
                "evenement_id": evenement.get("evenementId"),
                "type_porteur": type_porteur,
                "id_porteur": id_porteur,
                "rang": str(rang),
                "code_evenement": evenement.get("codeEvenement"),
                "date_evenement": evenement.get("dateEvenement"),
                "date_enregistrement": evenement.get("dateEnregistrement"),
                "code_etat_objet_1": evenement.get("etatObjet1"),
                "code_type_objet_1": evenement.get("typeObjet1"),
                "identifiant_objet_1": evenement.get("identifiantObjet1"),
                "code_type_objet_2": evenement.get("typeObjet2"),
                "identifiant_objet_2": evenement.get("identifiantObjet2"),
                "code_systeme_maitre": evenement.get("systemeMaitre"),
                "id_lot": lot.identifiant,
            })

    # -- groupements --------------------------------------------------------

    def _groupement_gco(self, gco: Dict[str, Any], contexte: ContexteSource
                        ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        lot = contexte.lot
        fc.controler_cles(contexte, "gco", gco, CLES_GCO)
        groupement_id = gco.get("pmSmsseId")
        yield ("groupement", {
            "nature_groupement": fc.GROUPEMENT_GCO,
            "groupement_id": groupement_id,
            "num_finess_groupement": None,
            "nom_groupement": None,
            "code_type_groupement": gco.get("typeGco"),
            "etat_objet": None,
            "date_derniere_maj": None,
            "id_lot": lot.identifiant,
        })
        yield from self._membres(gco.get("pmejDuGco"), groupement_id, fc.GROUPEMENT_GCO,
                                 fc.PORTEUR_EJ, contexte)
        self._membres_ege_non_supportes(gco.get("egeDuGco"), "gco.egeDuGco", contexte)

    def _groupement_gcc(self, gcc: Dict[str, Any], contexte: ContexteSource
                        ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        lot = contexte.lot
        fc.controler_cles(contexte, "gcc", gcc, CLES_GCC)
        groupement_id = gcc.get("gccId")
        yield ("groupement", {
            "nature_groupement": fc.GROUPEMENT_GCC,
            "groupement_id": groupement_id,
            "num_finess_groupement": gcc.get("numFinessGcc"),
            "nom_groupement": gcc.get("nomGcc"),
            "code_type_groupement": gcc.get("typeGcc"),
            "etat_objet": gcc.get("etatObjet"),
            "date_derniere_maj": gcc.get("dateDerniereMaj"),
            "id_lot": lot.identifiant,
        })
        yield from self._membres(gcc.get("pmejDuGcc"), groupement_id, fc.GROUPEMENT_GCC,
                                 fc.PORTEUR_EJ, contexte)
        self._membres_ege_non_supportes(gcc.get("egeDuGcc"), "gcc.egeDuGcc", contexte)
        yield from self._engagements(gcc.get("engagement"), fc.PORTEUR_GROUPEMENT,
                                     groupement_id, None, contexte)
        yield from self._evenements(gcc.get("evenement"), fc.PORTEUR_GROUPEMENT,
                                    groupement_id, contexte)

    def _membres(self, membres, groupement_id: Optional[str], nature: str,
                 type_membre: str, contexte: ContexteSource
                 ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        lot = contexte.lot
        for rang, membre in enumerate(membres or []):
            fc.controler_cles(contexte, f"{nature}.membre", membre,
                              fc.CLES_MEMBRE_GROUPEMENT)
            yield ("groupement_membre", {
                "groupement_id": groupement_id,
                "nature_groupement": nature,
                "type_membre": type_membre,
                "id_membre": membre.get("pmSmsseId"),
                "code_role_membre": membre.get("typeRoleEntiteGroupe"),
                "rang": str(rang),
                "id_lot": lot.identifiant,
            })

    @staticmethod
    def _membres_ege_non_supportes(membres, chemin: str, contexte: ContexteSource) -> None:
        """Les listes d'établissements membres sont vides sur 202607.

        Leur forme est donc inconnue et ne peut pas être devinée. Si un
        millésime ultérieur les renseigne, l'échec est bloquant et visible,
        plutôt qu'une perte silencieuse.
        """
        if membres:
            contexte.signaler("structure_inconnue", BLOQUANT,
                              type_enregistrement=chemin, detail=str(len(membres)))
            contexte.compter_ignore(chemin, len(membres))


# ---------------------------------------------------------------------------
# Inspection en ligne de commande
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import resource

    from contrat_source import (CONTROLE_ECHANTILLON, CONTROLE_MINIMAL, CONTROLE_STRICT,
                                InventaireCodes, Lot, RapportIngestion, RegistreAnomalies,
                                parcourir_source)

    analyseur = argparse.ArgumentParser(description="Ingestion du fichier FINESS structures.")
    analyseur.add_argument("fichier", type=Path)
    analyseur.add_argument("--controle", default=CONTROLE_ECHANTILLON,
                           choices=[CONTROLE_MINIMAL, CONTROLE_ECHANTILLON, CONTROLE_STRICT])
    analyseur.add_argument("--codes", action="store_true",
                           help="détailler les valeurs de chaque domaine")
    arguments = analyseur.parse_args()

    rapport = RapportIngestion(Lot("", "", "", "", 0), RegistreAnomalies(),
                               InventaireCodes(), arguments.controle)
    for _nom, _ligne in parcourir_source(SourceFinessStructures(), arguments.fichier,
                                         controle=arguments.controle, rapport=rapport):
        pass

    print(rapport.texte())
    print(f"RSS max    : {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.1f} Mio")
    if arguments.codes:
        for domaine in rapport.inventaire.domaines():
            valeurs = rapport.inventaire.valeurs(domaine)
            apercu = list(valeurs.items())[:10]
            print(f"\n{domaine} ({len(valeurs)} distincts) : {apercu}")
