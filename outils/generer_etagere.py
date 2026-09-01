#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Écrit le bloc « Sur l'étagère » de l'accueil et de la page cave.

Huit vraies références, deux rangs de quatre, avec leur photo. Chaque carte
renvoie vers la fiche correspondante du catalogue.

    python3 outils/generer_etagere.py

Pour changer la sélection : modifier CHOIX ci-dessous et relancer. Le bloc est
remplacé entre les balises <!-- étagère:début --> et <!-- étagère:fin -->.
"""
import html, json, re, sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).parent))
from generer_catalogue import titre_propre, court, LIBELLES, SINGULIER

# Deux rangs de quatre : d'abord les signatures, ensuite les régionales.
CHOIX = ["chateau-pichon-baron-2017", "chablis-2023-2023",
         "domaine-gueissard-bandol-rose-2024", "cremant-du-jura-blanc",
         "les-caselles-rouge-2024", "les-fumees-blanches-les-calcaires-2025",
         "madame-de-rayne-sauternes", "la-cuvee-des-fadas"]
PAGES = ["index.html", "cave-a-vin.html"]
DEBUT, FIN = "<!-- étagère:début -->", "<!-- étagère:fin -->"

def e(t): return html.escape(t or "", quote=True)

def region(p):
    """Une ligne courte : l'appellation, sinon l'origine, plus le cépage dominant."""
    lieu = court(p.get("appellation") or p.get("origine") or "")
    lieu = re.sub(r"^AOP\s+|^AOC\s+|^IGP\s+", "", lieu)
    # « France — Bordeaux — Sauternes AOC » : c'est le dernier segment qui parle
    bouts = [b.strip() for b in re.split(r"\s*[·—]\s*|\s+-\s+|,", lieu) if b.strip()]
    bouts = [b for b in bouts if b.lower() not in {"france", "occitanie", "bourgogne", "bordeaux"}] or bouts
    lieu = re.sub(r"\s+(AOC|AOP|IGP|DOC|DO)\b.*$", "", bouts[-1]).strip()
    cep = (p.get("cepages") or "").strip()
    cep = re.sub(r"\d+\s*%|\.|;", " ", cep)
    cep = re.split(r"[,/&]| et ", cep)[0].strip()
    bouts = [b for b in (lieu, cep) if b and len(b) < 30]
    return " · ".join(bouts[:2])

def carte(p, i):
    lien = "/nos-references?q=" + quote(p["nom"])
    img = p["images"][0]
    return f'''      <a class="bouteille-carte rv" href="{lien}" data-type="{p["type"]}" style="--d:{i * .07:.2f}s">
        <span class="b-photo"><img src="{e(img)}" alt="{e(p["nom"])}" loading="lazy" decoding="async" width="675" height="900"></span>
        <span class="b-type {p["type"]}">{SINGULIER[p["type"]]}</span>
        <h3 class="b-nom">{e(p["nom"])}</h3>
        <p class="b-region">{e(region(p))}</p>
        <p class="b-prix">Prix en boutique</p>
      </a>'''

def main():
    produits = {x["id"]: x for x in json.load(open("data/produits.json"))}
    choisis = []
    for cle in CHOIX:
        p = produits.get(cle)
        if not p:
            sys.exit(f"référence inconnue : {cle}")
        if not p.get("images"):
            sys.exit(f"référence sans photo : {cle}")
        p = dict(p)
        p["nom"] = titre_propre(court(p["nom"]))
        choisis.append(p)

    bloc = (DEBUT + "\n    <div class=\"etagere\" id=\"etagere\">\n"
            + "\n".join(carte(p, i) for i, p in enumerate(choisis))
            + "\n    </div>\n    " + FIN)

    for page in PAGES:
        s = Path(page).read_text(encoding="utf-8")
        if DEBUT not in s:
            sys.exit(f"{page} : balises d'étagère absentes")
        s = re.sub(re.escape(DEBUT) + r".*?" + re.escape(FIN), lambda _: bloc, s, flags=re.S)
        Path(page).write_text(s, encoding="utf-8")
        print(f"  {page} : étagère remplacée")
    print(f"{len(choisis)} références : " + ", ".join(p["nom"] for p in choisis))

if __name__ == "__main__":
    main()
