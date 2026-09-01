#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérifie — et corrige — l'association entre les fiches et les photos.

Les références « IMG_xxxx » inscrites dans les PDF du client se sont révélées
fausses par endroits (tout un lot inversé, quelques décalages ailleurs). Plutôt
que de leur faire confiance, on lit l'étiquette de chaque photo (reconnaissance
de texte macOS, voir outils/ocr.swift) et on réattribue les photos par
ressemblance avec le nom, le producteur et l'appellation de la fiche.

    python3 outils/verifier_photos.py --lire      # relit les étiquettes
    python3 outils/verifier_photos.py             # réattribue et écrit le JSON
    python3 outils/verifier_photos.py --simuler   # montre sans rien écrire
"""
import json, re, subprocess, sys, unicodedata
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

ETIQUETTES = Path("data/etiquettes-ocr.tsv")
OCR = Path("outils/ocr")
IMAGES = Path("images/cave")
SEUIL = 1.2          # preuve minimale exigée de l'étiquette elle-même
FIDELITE = 1.0       # prime à la référence du PDF, à preuve égale

def net(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t)

VIDES = {"chateau", "domaine", "grand", "cru", "vin", "wine", "de", "du", "des", "la", "le",
         "les", "et", "aop", "aoc", "igp", "mis", "en", "bouteille", "au", "france", "product",
         "of", "appellation", "protegee", "controlee", "origine", "cl", "vol", "alc", "contient",
         "sulfites", "bio", "organic", "red", "blanc", "rouge", "rose", "millesime", "par"}

def mots(t):
    return {m for m in net(t).split() if len(m) > 3 and m not in VIDES}

def lire_etiquettes():
    fichiers = sorted(str(f) for f in IMAGES.glob("*.webp"))
    sortie = subprocess.run([str(OCR)] + fichiers, capture_output=True, text=True)
    ETIQUETTES.write_text(sortie.stdout, encoding="utf-8")
    print(f"{len(sortie.stdout.splitlines())} étiquettes lues → {ETIQUETTES}")

def etiquettes():
    d = {}
    for ligne in ETIQUETTES.read_text(encoding="utf-8").splitlines():
        chemin, _, texte = ligne.partition("\t")
        d[Path(chemin).stem] = texte
    return d

# Mentions légales et code-barres : ils trahissent une contre-étiquette. Le
# recto porte le nom du vin, c'est lui qu'on veut voir en premier.
DOS = re.compile(r"mis en bouteille|sulfit|contient|product of|produit de|"
                 r"consommer avec mod|www\.|\d{8,}|nutri|ingredient|conserver|"
                 r"abus d.alcool|femme enceinte|bouteille au ch", re.I)
CODEBARRE = re.compile(r"\d[\d\s-]{9,}")

def face(texte):
    """recto (l'étiquette), verso (la contre-étiquette) ou muet (rien de lu)."""
    marques = len(DOS.findall(texte)) + len(CODEBARRE.findall(texte))
    mots = len([m for m in re.split(r"[^A-Za-zÀ-ÿ]+", texte) if len(m) > 2])
    if marques >= 2 or (marques == 1 and mots > 8):
        return "verso"
    return "muet" if mots == 0 else "recto"

def poids_des_mots(fiches):
    """« Fumées Blanches » revient sur six cuvées du même lot : ce mot ne
    distingue rien. « Calcaires » n'apparaît qu'une fois : il vaut de l'or.
    On pondère donc chaque mot par sa rareté dans le lot."""
    freq = {}
    for p in fiches:
        for m in mots(" ".join(str(p.get(k) or "") for k in
                               ("nom", "producteur", "appellation", "origine"))):
            freq[m] = freq.get(m, 0) + 1
    return {m: 1.0 / n for m, n in freq.items()}

def score(produit, texte, poids=None):
    """Somme des mots partagés, pondérés par leur rareté ; le nom compte double."""
    lus = mots(texte)
    if not lus:
        return 0.0
    nom = mots(produit.get("nom"))
    reste = mots(" ".join(str(produit.get(k) or "") for k in
                          ("producteur", "appellation", "origine"))) - nom
    def w(m):
        return (poids or {}).get(m, 1.0)
    s = sum(2.0 * w(m) for m in nom & lus) + sum(1.0 * w(m) for m in reste & lus)
    millesime = str(produit.get("millesime") or "")
    if millesime and millesime in texte:
        s += 0.5
    if face(texte) == "verso":
        s *= 0.75                      # une contre-étiquette fait une piètre vignette
    return s

def main():
    if "--lire" in sys.argv:
        lire_etiquettes()
    if not ETIQUETTES.exists():
        sys.exit("étiquettes absentes : lancer d'abord --lire")

    lus = etiquettes()
    produits = json.load(open("data/produits.json"))

    # on raisonne lot par lot : les photos d'un lot ne servent qu'à ses fiches
    lots = {}
    for p in produits:
        lots.setdefault(p.get("lot") or "", []).append(p)

    # --- passe 1 : appariement optimal à l'intérieur de chaque lot -----------
    candidats, contexte = [], {}
    for lot, fiches in lots.items():
        vues = sorted({v for p in fiches for v in p["photos"] if v in lus})
        if not vues:
            continue
        poids = poids_des_mots(fiches)
        brut = np.zeros((len(fiches), len(vues)))
        M = np.zeros((len(fiches), len(vues)))
        for i, p in enumerate(fiches):
            for j, v in enumerate(vues):
                brut[i, j] = score(p, lus[v], poids)
                M[i, j] = brut[i, j] + (FIDELITE if v in p["photos"][:1] else 0)
        for i, j in zip(*linear_sum_assignment(-M)):
            if brut[i, j] >= SEUIL:
                candidats.append((brut[i, j], fiches[i]["id"], vues[j]))
        # qui revendique quoi : sert à savoir si une voisine est libre de droits
        revendique = {}
        for v in vues:
            notes = sorted(((score(p, lus[v], poids), p["id"]) for p in fiches), reverse=True)
            revendique[v] = notes[0] if notes else (0.0, None)
        contexte[lot] = revendique

    # --- passe 2 : arbitrage entre lots, la meilleure preuve l'emporte -------
    # les plages se chevauchent (…3160-3179 puis 3180-3199) : deux lots peuvent
    # réclamer la même photo, on tranche au score et non à l'ordre de lecture
    attribue, pris_v = {}, set()
    for note, pid, v in sorted(candidats, key=lambda c: -c[0]):
        if pid in attribue or v in pris_v:
            continue
        attribue[pid] = (v, note); pris_v.add(v)

    # --- passe 3 : recto devant, verso en seconde vue ------------------------
    def voisines(v):
        n = int(v.split("_")[1])
        return [f"IMG_{n + 1}", f"IMG_{n - 1}"]

    confirmes = corriges = orphelins = 0
    rapport, a_verifier = [], []
    for p in produits:
        if not p["photos"]:
            continue
        revendique = contexte.get(p.get("lot") or "", {})
        trouve = attribue.get(p["id"])

        if not trouve:
            # étiquette illisible : on garde la référence du PDF si personne
            # d'autre ne l'a réclamée, sinon la fiche part sans photo
            reste = [v for v in p["photos"][:1] if v in lus and v not in pris_v]
            pris_v.update(reste)
            if any(v in lus for v in p["photos"]):   # la photo existe, le doute aussi
                orphelins += 1
                a_verifier.append((p["nom"][:40], p["id"], reste[0] if reste else "aucune"))
            p["photos"] = reste
            continue

        v, note = trouve
        # tombé sur une contre-étiquette ? le recto de la même bouteille dort
        # peut-être juste à côté, la prise de vue va par paires
        if face(lus[v]) == "verso":
            mieux = next((x for x in voisines(v) if x in lus and x not in pris_v
                          and face(lus[x]) == "recto"), None)
            if mieux:
                pris_v.discard(v); pris_v.add(mieux); v = mieux

        # seconde vue : la voisine libre. Le verso porte souvent le nom du vin
        # lui aussi — c'est la même bouteille, pas la fiche du voisin.
        def sans_proprietaire(x):
            n, qui = revendique.get(x, (0.0, None))
            return x in lus and x not in pris_v and (n < SEUIL or qui == p["id"])
        vues = [v]
        autre = next((x for x in voisines(v) if sans_proprietaire(x)), None)
        if autre:
            pris_v.add(autre); vues.append(autre)

        if vues[0] != p["photos"][0]:
            corriges += 1
            rapport.append((p["nom"][:40], p["photos"][:2], vues, round(note, 1)))
        else:
            confirmes += 1
        p["photos"] = vues

    deux = sum(1 for p in produits if len(p["photos"]) > 1)
    print(f"confirmées : {confirmes}   corrigées : {corriges}   "
          f"sans étiquette lisible : {orphelins}   fiches à deux vues : {deux}")
    for nom, avant, apres, sc in rapport[:30]:
        print(f"  {nom:42s} {str(avant):26s} → {str(apres):26s} (score {sc})")
    if len(rapport) > 30:
        print(f"  … et {len(rapport) - 30} autres")

    if "--simuler" in sys.argv:
        print("\n(simulation : data/produits.json inchangé)")
        return

    with open("data/photos-a-verifier.csv", "w", encoding="utf-8") as f:
        f.write("produit;identifiant;photo retenue;remarque\n")
        for nom, pid, v in a_verifier:
            f.write(f"{nom};{pid};{v};étiquette illisible, référence du PDF conservée\n")
        for nom, avant, apres, sc in rapport:
            f.write(f"{nom};;{apres[0]};le PDF indiquait {avant[0] if avant else '?'}, "
                    f"l'étiquette lue dit {apres[0]}\n")
    print(f"détail dans data/photos-a-verifier.csv ({len(a_verifier) + len(rapport)} lignes)")

    json.dump(produits, open("data/produits.json", "w"), ensure_ascii=False, indent=1)
    print("data/produits.json mis à jour — relancer convertir_photos.py puis generer_catalogue.py")

if __name__ == "__main__":
    main()
