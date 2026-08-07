"""Coût du contrat sur un enregistrement large, aux dimensions réelles du pivot."""
import resource, time
from pathlib import Path
from contrat_source import (Champ, Source, TypeEnregistrement, TYPE_ENTETE, TEXTE, DATE,
                            ENTIER_TEXTE, parcourir_source, RapportIngestion, Lot,
                            RegistreAnomalies, InventaireCodes,
                            CONTROLE_MINIMAL, CONTROLE_ECHANTILLON, CONTROLE_STRICT)

FICHIER = Path("/tmp/tests_contrat/source_factice.txt")

# 47 champs, dont 8 codifiés et 5 datés : dimensions du type `activite` du pivot
CHAMPS = [Champ("activite_ae_id", TEXTE, obligatoire=True), Champ("niveau", TEXTE, obligatoire=True)]
CHAMPS += [Champ(f"code_{i}", TEXTE, domaine=f"domaine_{i}") for i in range(8)]
CHAMPS += [Champ(f"date_{i}", DATE) for i in range(5)]
CHAMPS += [Champ(f"nombre_{i}", ENTIER_TEXTE) for i in range(3)]
CHAMPS += [Champ(f"texte_{i}", TEXTE) for i in range(28)]
CHAMPS += [Champ("id_lot", TEXTE, obligatoire=True)]
TYPE_LARGE = TypeEnregistrement("activite", CHAMPS)
print(f"Type de mesure : {len(TYPE_LARGE.noms)} champs, "
      f"{len(TYPE_LARGE.champs_codifies())} codifiés")

N = 1_000_000

class SourceLarge(Source):
    nom = "mesure"
    def millesime(self, chemin): return "202607"
    def types_enregistrements(self): return (TYPE_ENTETE, TYPE_LARGE)
    def produire(self, chemin, contexte):
        lot = contexte.lot
        lot.schema_version = "v1.0.0"; lot.genere_le = "2026-08-01T02:06:22Z"
        yield ("entete", lot.ligne_entete())
        modele = {c.nom: "valeur" for c in CHAMPS}
        for i in range(len(CHAMPS)):
            if CHAMPS[i].type_valeur == DATE: modele[CHAMPS[i].nom] = "1990-01-01"
            if CHAMPS[i].type_valeur == ENTIER_TEXTE: modele[CHAMPS[i].nom] = "24"
        for i in range(N):
            ligne = dict(modele)
            ligne["activite_ae_id"] = str(i)
            for j in range(8):
                ligne[f"code_{j}"] = str((i + j) % 300)
            yield ("activite", ligne)

# coût de référence : la source seule, sans le contrat
t0 = time.time(); n = 0
src = SourceLarge()
from contrat_source import ContexteSource
ctx = ContexteSource(Lot("m","202607","f","0"*64,0), RegistreAnomalies(), InventaireCodes())
for _ in src.produire(FICHIER, ctx): n += 1
reference = time.time() - t0
print(f"\nSource seule (sans contrat)           : {reference:5.1f} s pour {n} lignes")

for mode, inv in (("minimal", True), ("echantillon", True), ("strict", True), ("echantillon", False)):
    rap = RapportIngestion(Lot("x","x","x","x"*8,0), RegistreAnomalies(), InventaireCodes(), mode)
    avant = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    t0 = time.time()
    for _ in parcourir_source(SourceLarge(), FICHIER, controle=mode, rapport=rap,
                              inventorier_codes=inv):
        pass
    d = time.time() - t0
    pic = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    etiquette = f"{mode}{'' if inv else ' sans inventaire'}"
    print(f"Contrôle « {etiquette:<24} » : {d:5.1f} s "
          f"(surcoût {d - reference:+5.1f} s, {(d/reference - 1)*100:+4.0f} %) | "
          f"RSS {pic:5.1f} Mio | contrôlées {rap.lignes_controlees}")
