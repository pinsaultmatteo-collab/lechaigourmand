#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Écrit le bloc « Sur l'étagère » de l'accueil et de la page cave.

Chaque pastille de filtre a sa propre vitrine de huit bouteilles : l'étagère
reste pleine quel que soit le filtre choisi, au lieu de se vider quand on
demande les rosés. Une même bouteille peut servir plusieurs vitrines — c'est
l'attribut data-vitrine qui dit lesquelles.

    python3 outils/generer_etagere.py

Pour changer la sélection de « Tout voir » : modifier CHOIX ci-dessous.
Le bloc est remplacé entre <!-- étagère:début --> et <!-- étagère:fin -->.
"""
import html, json, re, sys, unicodedata
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).parent))
from generer_catalogue import titre_propre, court, SINGULIER, silhouette, dedoublonner

# Deux rangs de quatre, d'abord les signatures puis les régionales : la vitrine
# « Tout voir ».
CHOIX = ["chateau-pichon-baron-2017", "chablis-2023-2023",
         "domaine-gueissard-bandol-rose-2024", "cremant-du-jura-blanc",
         "les-caselles-rouge-2024", "les-fumees-blanches-les-calcaires-2025",
         "madame-de-rayne-sauternes", "la-cuvee-des-fadas"]

VITRINES = ["rouge", "blanc", "rose", "bulles", "moelleux", "biere"]
PAR_VITRINE = 8
MEME_DOMAINE = 2        # pas plus de deux cuvées du même domaine dans une vitrine
MEME_REGION = 2         # ni deux fois la même appellation, tant qu'on a le choix
PAGES = ["index.html", "cave-a-vin.html"]
DEBUT, FIN = "<!-- étagère:début -->", "<!-- étagère:fin -->"

def e(t): return html.escape(t or "", quote=True)

def sans_accent(t):
    return unicodedata.normalize("NFKD", (t or "").lower()).encode("ascii", "ignore").decode()

def region(p):
    """Une ligne courte : le lieu le plus précis, puis le cépage dominant."""
    lieu = court(p.get("appellation") or p.get("origine") or "")
    lieu = re.sub(r"^AOP\s+|^AOC\s+|^IGP\s+", "", lieu)
    # « France — Bordeaux — Sauternes AOC » : c'est le dernier segment qui parle
    bouts = [b.strip() for b in re.split(r"\s*[·—]\s*|\s+-\s+|,", lieu) if b.strip()]
    precis = [b for b in bouts
              if b.lower() not in {"france", "occitanie", "bourgogne", "bordeaux"}]
    # le dernier segment est le plus précis ; si tout est générique, le premier
    # reste plus parlant (« Occitanie » vaut mieux que « France »)
    choisi = precis[-1] if precis else (bouts[0] if bouts else "")
    lieu = re.sub(r"\s+(AOC|AOP|IGP|DOC|DO)\b.*$", "", choisi).strip(" .")
    # « orge » et « raisin rouge » ne disent rien d'utile sous une bière
    if p["type"] in ("biere", "epicerie", "spiritueux"):
        return lieu
    cep = re.sub(r"\d+\s*%|\.|;", " ", p.get("cepages") or "").strip()
    cep = re.split(r"[,/&]| et |—", cep)[0].strip(" -")
    return " · ".join([b for b in (lieu, cep) if b and len(b) < 30][:2])

def choisir(produits, type_):
    """Huit références d'une couleur : les photographiées d'abord, et sans
    répéter le même domaine ni la même appellation tant qu'il reste du choix —
    sinon la vitrine des bières affiche huit fois la même brasserie, et celle
    des rouges huit bourgognes du même importateur."""
    lot = [x for x in produits.values() if x["type"] == type_]
    # photographiées d'abord, puis celles dont on sait dire l'origine
    lot.sort(key=lambda x: (0 if x.get("images") else 1,
                            0 if region(x) else 1, sans_accent(x["nom"])))
    pris, vus = [], set()
    domaines, regions = {}, {}
    for plafonds in ((MEME_DOMAINE, MEME_REGION), (MEME_DOMAINE, 99), (99, 99)):
        pd, pr = plafonds
        for x in lot:
            if len(pris) >= PAR_VITRINE:
                return pris
            if x["id"] in vus:
                continue
            d = sans_accent(x.get("producteur") or x["id"])
            r = sans_accent(region(x).split(" · ")[0] or x["id"])
            if domaines.get(d, 0) >= pd or regions.get(r, 0) >= pr:
                continue
            domaines[d] = domaines.get(d, 0) + 1
            regions[r] = regions.get(r, 0) + 1
            vus.add(x["id"]); pris.append(x)
    return pris

def carte(p, rang, vitrines):
    lien = "/nos-references?q=" + quote(p["nom"])
    if p.get("images"):
        visuel = (f'<img src="{e(p["images"][0])}" alt="{e(p["nom"])}" loading="lazy" '
                  f'decoding="async" width="675" height="900">')
    else:
        visuel = silhouette(p["type"])
    cachee = "" if "tous" in vitrines else " cache"
    return f'''      <a class="bouteille-carte rv{cachee}" href="{lien}" data-type="{p["type"]}" data-vitrine="{" ".join(vitrines)}" style="--d:{rang % 8 * .07:.2f}s">
        <span class="b-photo">{visuel}</span>
        <span class="b-type {p["type"]}">{SINGULIER[p["type"]]}</span>
        <h3 class="b-nom">{e(p["nom"])}</h3>
        <p class="b-region">{e(region(p))}</p>
        <p class="b-prix">Prix en boutique</p>
      </a>'''

def main():
    produits = {}
    for x in dedoublonner(json.load(open("data/produits.json"))):
        x["nom"] = titre_propre(court(x["nom"]))
        if x.get("producteur"):
            x["producteur"] = titre_propre(court(x["producteur"]))
        produits[x["id"]] = x

    # qui apparaît dans quelle vitrine
    appartenance, ordre = {}, []
    def inscrire(p, vitrine):
        if p["id"] not in appartenance:
            appartenance[p["id"]] = []
            ordre.append(p)
        appartenance[p["id"]].append(vitrine)

    for cle in CHOIX:
        p = produits.get(cle)
        if not p:
            sys.exit(f"référence inconnue : {cle}")
        inscrire(p, "tous")
    resume = []
    for v in VITRINES:
        lot = choisir(produits, v)
        for p in lot:
            inscrire(p, v)
        illustrees = sum(1 for p in lot if p.get("images"))
        resume.append(f"{v} {len(lot)} ({illustrees} en photo)")

    bloc = (DEBUT + "\n    <div class=\"etagere\" id=\"etagere\">\n"
            + "\n".join(carte(p, i, appartenance[p["id"]]) for i, p in enumerate(ordre))
            + "\n    </div>\n    " + FIN)

    for page in PAGES:
        s = Path(page).read_text(encoding="utf-8")
        if DEBUT not in s:
            sys.exit(f"{page} : balises d'étagère absentes")
        s = re.sub(re.escape(DEBUT) + r".*?" + re.escape(FIN), lambda _: bloc, s, flags=re.S)
        Path(page).write_text(s, encoding="utf-8")
        print(f"  {page} : étagère remplacée")
    print(f"{len(ordre)} cartes au total — " + ", ".join(resume))

if __name__ == "__main__":
    main()
