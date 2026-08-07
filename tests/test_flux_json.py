"""Tests du prototype flux_json sur cas limites."""
import gzip, json, sys
from pathlib import Path
from flux_json import parcourir, Compteurs, ErreurFluxJson, CLE_ENTETE

BASE = Path("/tmp/tests_flux"); BASE.mkdir(exist_ok=True)

def ecrire(nom, contenu, compresse=False):
    p = BASE / nom
    if compresse:
        with gzip.open(p, "wt", encoding="utf-8") as f: f.write(contenu)
    else:
        p.write_text(contenu, encoding="utf-8")
    return p

def lire(p, **kw):
    c = Compteurs()
    return [(k, r, v) for k, r, v in parcourir(p, compteurs=c, **kw)], c

ok = 0; ko = 0
def verifier(intitule, condition, detail=""):
    global ok, ko
    if condition: ok += 1; print(f"  OK   {intitule}")
    else: ko += 1; print(f"  ECHEC {intitule} {detail}")

doc = {"schemaVersion": "v1.0.0", "generatedAt": "2026-08-01T00:00:00Z",
       "gco": [{"id": "1"}, {"id": "2"}],
       "pmej": [{"nom": 'Guill"emet et \\ antislash', "ege": [{"n": "A"}]},
                {"nom": "Accentué éèàç", "ege": []}]}

print("1. JSON indenté")
r, c = lire(ecrire("indent.json", json.dumps(doc, indent=2, ensure_ascii=False)))
verifier("2 entêtes + 2 gco + 2 pmej", [x[0] for x in r] == [CLE_ENTETE]*2 + ["gco"]*2 + ["pmej"]*2, r)
verifier("échappements restitués", r[4][2]["nom"] == 'Guill"emet et \\ antislash', r[4][2]["nom"])
verifier("accents restitués", r[5][2]["nom"] == "Accentué éèàç")
verifier("rangs par tableau", [x[1] for x in r] == [0,1,0,1,0,1], [x[1] for x in r])
verifier("compteurs", c.objets_par_cle == {"gco": 2, "pmej": 2} and c.termine)

print("2. JSON minifié (une seule ligne, sans espaces)")
r2, _ = lire(ecrire("minifie.json", json.dumps(doc, separators=(",", ":"), ensure_ascii=False)))
verifier("sortie identique à l'indenté", [x[2] for x in r2] == [x[2] for x in r], "")

print("3. JSON gzip")
r3, _ = lire(ecrire("compresse.json.gz", json.dumps(doc, indent=2, ensure_ascii=False), compresse=True))
verifier("détection gzip par nombre magique", [x[2] for x in r3] == [x[2] for x in r])

print("4. Très petits blocs (mémoire contrainte à l'extrême)")
r4, c4 = lire(ecrire("indent2.json", json.dumps(doc, indent=2, ensure_ascii=False)), taille_bloc=7, seuil_compactage=11)
verifier("sortie inchangée avec bloc de 7 caractères", [x[2] for x in r4] == [x[2] for x in r])

print("5. Tableaux vides et objet racine sans tableau")
r5, c5 = lire(ecrire("vide.json", '{"schemaVersion":"v1","gco":[],"pmej":[]}'))
verifier("aucun objet émis, compteurs à zéro", c5.objets_par_cle == {"gco": 0, "pmej": 0} and len(r5) == 1)

print("6. Détection des documents invalides")
for nom, contenu, motif in [
    ("tronque.json", json.dumps(doc, indent=2)[: int(len(json.dumps(doc, indent=2)) * 0.6)], "tronqué en plein enregistrement"),
    ("tronque_entete.json", '{"schemaVersion":"v1","pmej":[{"a":1},{"b', "tronqué dans une clé"),
    ("vide_total.json", "", "document vide"),
    ("racine_tableau.json", "[1,2,3]", "racine non objet"),
    ("apres.json", '{"pmej":[]} PARASITE', "contenu après la racine"),
    ("non_referme.json", '{"pmej":[{"a":"b"}', "tableau non refermé"),
]:
    p = ecrire(nom, contenu)
    try:
        lire(p); verifier(motif, False, "aucune exception levée")
    except ErreurFluxJson as e:
        verifier(motif, True)
    except Exception as e:
        verifier(motif, False, f"exception inattendue {type(e).__name__}: {e}")

print(f"\n{ok} tests réussis, {ko} échecs")
sys.exit(1 if ko else 0)
