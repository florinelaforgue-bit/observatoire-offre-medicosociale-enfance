"""Preuve d'exhaustivité du parcours de flux_json.

Deux recensements indépendants des occurrences de clés JSON sont comparés :
  A. par le lecteur : toute clé rencontrée dans les objets émis, à toute profondeur ;
  B. par balayage textuel du flux décompressé, sans aucun parseur.
Si les deux recensements coïncident clé par clé, aucun fragment du document
n'a été sauté par le lecteur.
"""
import gzip, re, sys
from collections import Counter
from pathlib import Path
from flux_json import parcourir, Compteurs, CLE_ENTETE

MOTIF_CLE = re.compile(r'^\s*"([A-Za-z0-9_]+)"\s*:')


def recensement_lecteur(chemin):
    """Méthode A : via flux_json."""
    compte = Counter()

    def visiter(noeud):
        if isinstance(noeud, dict):
            for cle, valeur in noeud.items():
                compte[cle] += 1
                visiter(valeur)
        elif isinstance(noeud, list):
            for valeur in noeud:
                visiter(valeur)

    cpt = Compteurs()
    for cle_racine, _rang, valeur in parcourir(chemin, compteurs=cpt):
        if cle_racine == CLE_ENTETE:
            compte[valeur[0]] += 1        # clé scalaire de l'objet racine
        else:
            visiter(valeur)
    for cle_racine in cpt.objets_par_cle:
        compte[cle_racine] += 1           # la clé du tableau racine elle-même
    return compte, cpt


def recensement_textuel(chemin):
    """Méthode B : balayage ligne à ligne du flux décompressé, sans parseur."""
    compte = Counter()
    with gzip.open(chemin, "rt", encoding="utf-8") as f:
        for ligne in f:
            m = MOTIF_CLE.match(ligne)
            if m:
                compte[m.group(1)] += 1
    return compte


def comparer(chemin):
    chemin = Path(chemin)
    print(f"\n=== {chemin.name} ===")
    a, cpt = recensement_lecteur(chemin)
    b = recensement_textuel(chemin)
    ecarts = {c: (a.get(c, 0), b.get(c, 0)) for c in set(a) | set(b) if a.get(c, 0) != b.get(c, 0)}
    print(f"  Parcours          : {cpt.resume()}")
    print(f"  Clés distinctes   : lecteur {len(a)} | balayage textuel {len(b)}")
    print(f"  Occurrences total : lecteur {sum(a.values()):,} | balayage textuel {sum(b.values()):,}"
          .replace(",", " "))
    if ecarts:
        print(f"  ECHEC : {len(ecarts)} clés discordantes")
        for c, (x, y) in sorted(ecarts.items())[:20]:
            print(f"      {c:<40} lecteur={x:<10} textuel={y}")
        return False
    print("  OK : recensements strictement identiques, clé par clé")
    return True


if __name__ == "__main__":
    resultats = [comparer(c) for c in sys.argv[1:]]
    print()
    sys.exit(0 if all(resultats) else 1)
