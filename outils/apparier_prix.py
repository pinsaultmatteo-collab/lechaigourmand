#!/usr/bin/env python3
"""Rapproche les fiches du catalogue des lignes du tarif fournisseur.

Les deux sources ne se ressemblent pas : la fiche dit « La Grenouille » chez
« Domaine de la Grenaudière », le tarif dit « Domaine De La Grenaudiere -
Blanc - Muscadet "La Grenouille" 75Cl ». On compare donc des sacs de mots
pondérés par leur rareté (IDF) : « grenaudiere » vaut cher, « rouge » ne vaut
rien.

Trois garde-fous, appris des erreurs du premier jet :

· la couleur est éliminatoire — un blanc ne prend pas le prix d'un rouge, et
  « CEZ White Blend » était parti chercher « Ernst Gouws Cez Rouge » ;
· le format aussi — une magnum coûte le double d'une 75 cl ;
· l'affectation est globale (Hungarian) : deux fiches ne peuvent pas se
  partager la même ligne de tarif, ce qui donnait le même prix aux quatre
  bières blondes de La Gorge Fraîche ;
· le mot-pivot — le terme le plus rare du nom de la fiche — doit figurer dans
  la désignation. Sans lui, « Château La Dominique » se contentait de
  « Château Franc Baudron » : deux châteaux, un saint-émilion, et 130 € d'écart.

La mesure est un rappel : quelle part du nom de la fiche se retrouve dans la
désignation. Un cosinus punissait les désignations bavardes du fournisseur —
« Chateau Soutard 2022 AOC St Emilion Grand Cru Rouge - Rouge - France » —
et faisait tomber des évidences sous le seuil.

Un prix faux est pire que pas de prix : ce qui n'est pas net part dans
data/prix-a-verifier.csv et reste « prix en boutique » sur le site.
"""
import csv
import json
import math
import os
import re
import sys
from collections import Counter

import numpy as np
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lire_tarifs import lire, normaliser                                   # noqa: E402

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

SEUIL_SUR = 0.72          # au-dessus, et sans rival proche : on prend
SEUIL_DOUTE = 0.45        # entre les deux : à relire à la main
ECART = 1.15              # le retenu doit devancer le suivant de 15 %

VIDES = {"cl", "ml", "l", "bio", "vin", "vins", "de", "du", "des", "la", "le", "les",
         "et", "aoc", "aop", "igp", "doc", "docg", "dop", "d", "s", "eur", "np", "c6",
         "alcool", "alcools", "spi", "vis", "non", "millesim", "grand", "cru", "france"}

GROS = re.compile(r"magnum|150\s*cl|1[.,]5\s*l|jeroboam|mathusalem|300\s*cl|600\s*cl|"
                  r"\b3\s*l\b|\b30\s*l\b|\b10\s*l\b|\b5\s*l\b|\bfut\b|\bbib\b")

# ---------- familles ----------
# Ce qui, dans une désignation, trahit la couleur ou la famille du produit.
FAMILLES = {
    "rouge":  r"\brouge\b|\brosso\b|\btinto\b|\bred\b|\bnoir\b",
    "blanc":  r"\bblanc\b|\bbianco\b|\bblanco\b|\bbranco\b|\bwhite\b|\bblc\b",
    "rose":   r"\brose\b|\brosato\b|\brosado\b",
    "bulles": r"\bpetillant\b|\bprosecco\b|\bcrement\b|\bcremant\b|\bspumante\b|"
              r"\bchampagne\b|\bperlant\b|\bblanquette\b|\bmoscato\b|\bbulle",
    "biere":  r"\bbiere\b|\bblonde\b|\bblanche\b|\bipa\b|\bneipa\b|\bstout\b|\btriple\b|"
              r"\blager\b|\bambre\b|\bambree\b|\bsour\b|\bale\b",
    "spiritueux": r"\bwhisky\b|\bgin\b|\brhum\b|\brum\b|\bvodka\b|\bliqueur\b|\barmagnac\b|"
                  r"\bcognac\b|\btequila\b|\bvermouth\b|\bcachaca\b|\bporto\b|\bmezcal\b|"
                  r"\bcalvados\b|\baperitivo\b|\bspritz\b|\bmacvin\b",
    "epicerie": r"\bconserverie\b|\bchocolat\b|\bpate\b|\bterrine\b|\bfoie\b|\bmiel\b|"
                r"\bjus\b|\brillette\b|\bcassoulet\b|\bgarbure\b|\bconfit\b|\bboudin\b|"
                r"\bjambonneau\b|\bguinguet\b|\btablette\b|\bballotin",
    "moelleux": r"\bsauterne|\bmoelleux\b|\bdoux\b|\bliquoreux\b",
}
# Ce qu'une fiche d'un type donné a le droit de rencontrer dans le tarif.
COMPATIBLE = {
    "rouge": {"rouge"}, "blanc": {"blanc"}, "rose": {"rose"},
    "bulles": {"bulles", "blanc", "rose"},          # « Petillant Blanc », « Crement Brut »
    "biere": {"biere"},
    "spiritueux": {"spiritueux"},
    "moelleux": {"moelleux", "blanc"},              # un sauternes est un blanc
    "epicerie": {"epicerie"},
}


def familles(texte):
    n = normaliser(texte)
    return {f for f, motif in FAMILLES.items() if re.search(motif, n)}


def mots(t):
    sortie = []
    for m in normaliser(t).split():
        if m in VIDES or len(m) < 2:
            continue
        # « fontanilles » et « fontanille » désignent le même vin.
        if len(m) > 4 and m.endswith("s"):
            m = m[:-1]
        sortie.append(m)
    return sortie


def annee(t):
    a = re.findall(r"\b(19[5-9]\d|20[0-3]\d)\b", str(t or ""))
    return a[-1] if a else None


def dedoublonner(tarifs):
    """Le fournisseur répète certaines références. On garde la moins chère,
    pour ne jamais annoncer un prix supérieur à celui de la boutique."""
    par_cle, ordre = {}, []
    for t in tarifs:
        cle = t["cle"]
        if cle not in par_cle:
            par_cle[cle] = t
            ordre.append(cle)
        elif t["prix"] < par_cle[cle]["prix"]:
            par_cle[cle] = t
    return [par_cle[c] for c in ordre]


def apparier():
    tarifs, sans_prix = lire()
    tarifs = dedoublonner(tarifs)
    fiches = json.load(open(os.path.join(RACINE, "data/produits.json"), encoding="utf-8"))

    presence = Counter()
    for t in tarifs:
        presence.update(set(mots(t["designation"])))
    n = len(tarifs)
    idf = {m: math.log(n / (1 + c)) + 0.35 for m, c in presence.items()}
    inconnu = math.log(n) + 0.35
    poids = lambda m: idf.get(m, inconnu)

    for t in tarifs:
        t["mots"] = set(mots(t["designation"]))
        t["annee"] = annee(t["designation"])
        t["gros"] = bool(GROS.search(normaliser(t["designation"])))
        t["fam"] = familles(t["designation"])
        t["norme"] = math.sqrt(sum(poids(m) ** 2 for m in t["mots"])) or 1

    vus = set(idf)                       # les mots que le tarif emploie

    # Deux traitements pour les mots que le tarif ignore, selon d'où ils viennent.
    #
    # Venant du producteur ou des cépages, c'est de la prose que le fournisseur
    # n'écrit jamais — « Domaine du Château Philippe le Hardi », « 63 % Merlot ».
    # Les compter au dénominateur pénaliserait la fiche pour rien : on les jette.
    #
    # Venant du NOM, c'est l'inverse : si le tarif n'emploie nulle part le mot
    # « pilet », c'est que le Château Pilet n'est pas chez ce fournisseur. On les
    # garde donc, et leur absence fait chuter le score. Sans cette asymétrie,
    # « Château Pilet — Bordeaux » se voyait offrir à 0,87 le prix du Château La
    # Guillaumette : deux bordeaux rouges, aucun rapport.
    #
    # Le nom pèse plein, le producteur un peu moins : « Château Soutard »
    # s'appelle comme son domaine, « La Grenouille » non.
    POIDS_NOM, POIDS_PROD = 1.0, 0.6

    profils = []
    for f in fiches:
        noyau = {}
        for m in mots(f.get("nom") or ""):
            noyau[m] = POIDS_NOM
        for m in mots(f.get("producteur") or ""):
            if m in vus:
                noyau[m] = max(noyau.get(m, 0), POIDS_PROD)
        # Appellation et cépages ne servent qu'à départager : trouvés ils
        # rapportent, absents ils ne coûtent rien.
        appui = {m for c in ("appellation", "cepages", "style", "millesime")
                 for m in mots(f.get(c) or "") if m in vus} - set(noyau)
        connus = [m for m in mots(f.get("nom") or "") if m in vus]
        profils.append({
            "noyau": noyau,
            "appui": appui,
            "pivot": max(connus, key=poids) if connus else None,
            "masse": sum(w * poids(m) ** 2 for m, w in noyau.items()) or 1,
            "annee": f.get("millesime") or annee(f.get("nom")),
            "gros": bool(GROS.search(normaliser((f.get("contenance") or "") + " " + (f.get("nom") or "")))),
            "type": f.get("type"),
        })

    # ---------- matrice des scores ----------
    M = np.zeros((len(fiches), len(tarifs)))
    for i, p in enumerate(profils):
        if not p["noyau"] or not p["pivot"]:
            continue
        permis = COMPATIBLE.get(p["type"], set())
        for j, t in enumerate(tarifs):
            # Sans le mot-pivot, on ne regarde même pas le reste.
            if p["pivot"] not in t["mots"]:
                continue
            # La couleur tranche : si le tarif l'annonce et qu'elle diffère, non.
            if t["fam"] and permis and not (t["fam"] & permis):
                continue
            trouves = {m: w for m, w in p["noyau"].items() if m in t["mots"]}
            s = sum(w * poids(m) ** 2 for m, w in trouves.items()) / p["masse"]
            s += min(0.16, 0.055 * len(p["appui"] & t["mots"]))
            if p["gros"] != t["gros"]:
                s *= 0.40
            if p["annee"] and t["annee"] and p["annee"] != t["annee"]:
                s *= 0.88
            M[i, j] = min(s, 1.0)

    # ---------- affectation globale ----------
    # Une ligne de tarif ne peut servir qu'une fois. Les colonnes fictives
    # laissent les fiches sans bon candidat repartir les mains vides.
    fictives = np.full((len(fiches), len(fiches)), SEUIL_DOUTE * 0.999)
    lignes, colonnes = linear_sum_assignment(np.hstack([M, fictives]), maximize=True)

    resultats = []
    for i, j in zip(lignes, colonnes):
        f = fiches[i]
        candidats = sorted(((M[i, k], tarifs[k]) for k in np.argsort(-M[i])[:3] if M[i, k] > 0),
                           key=lambda x: -x[0])
        if j >= len(tarifs) or M[i, j] < SEUIL_DOUTE:
            resultats.append({"fiche": f, "tarif": None, "score": 0.0,
                              "candidats": candidats, "net": False})
            continue
        score = M[i, j]
        rival = max((M[i, k] for k in range(len(tarifs)) if k != j), default=0.0)
        net = score >= SEUIL_SUR and (rival == 0 or score >= rival * ECART)
        # Une fiche de spiritueux réduite à sa marque — « Two Stacks », « Silvio
        # Carta », rien de plus que le producteur — ne désigne pas un produit.
        # Two Stacks fait du whiskey et une crème irlandaise ; le tarif n'en
        # liste qu'un. On ne devine pas lequel est en rayon.
        if net and f.get("type") == "spiritueux":
            marque = set(mots(f.get("nom") or "")) <= set(mots(f.get("producteur") or ""))
            if marque:
                net = False
        resultats.append({"fiche": f, "tarif": tarifs[j], "score": score,
                          "candidats": candidats, "net": net})
    resultats.sort(key=lambda r: fiches.index(r["fiche"]))
    return resultats, tarifs, sans_prix


def main():
    resultats, tarifs, sans_prix = apparier()
    surs = [r for r in resultats if r["net"]]
    doutes = [r for r in resultats if not r["net"] and r["tarif"]]
    rien = [r for r in resultats if not r["tarif"]]

    print(f"  {len(surs):>3} fiches appariées sans ambiguïté")
    print(f"  {len(doutes):>3} à relire")
    print(f"  {len(rien):>3} sans correspondance → « prix en boutique »")
    print(f"  ({len(resultats)} fiches, {len(tarifs)} lignes de tarif après dédoublonnage)\n")

    print("  ── douze appariements sûrs ──")
    for r in surs[::max(1, len(surs) // 12)][:12]:
        print(f"    {r['score']:.2f}  {r['fiche']['nom'][:33]:33} → "
              f"{r['tarif']['designation'][:50]:50} {r['tarif']['prix']:>7.2f} €")

    print("\n  ── les doutes ──")
    for r in doutes[:22]:
        print(f"    {r['score']:.2f}  {r['fiche']['nom'][:33]:33} → "
              f"{r['tarif']['designation'][:50]:50} {r['tarif']['prix']:>7.2f} €")

    chemin = os.path.join(RACINE, "data/prix-a-verifier.csv")
    with open(chemin, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["etat", "score", "fiche", "type", "producteur", "millesime",
                    "tarif retenu", "prix", "autre candidat", "prix autre"])
        for r in resultats:
            f, t = r["fiche"], r["tarif"]
            autres = [c for c in r["candidats"] if not t or c[1] is not t]
            a = autres[0] if autres else None
            w.writerow(["sur" if r["net"] else ("doute" if t else "aucun"),
                        f"{r['score']:.2f}", f["nom"], f.get("type") or "",
                        f.get("producteur") or "", f.get("millesime") or "",
                        t["designation"] if t else "", f"{t['prix']:.2f}" if t else "",
                        a[1]["designation"] if a else "", f"{a[1]['prix']:.2f}" if a else ""])
    print(f"\n  → data/prix-a-verifier.csv")


if __name__ == "__main__":
    main()
