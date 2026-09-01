#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère nos-references.html à partir de data/produits.json.

    python3 outils/generer_catalogue.py

Les fiches sont écrites en dur dans la page (et non chargées en JavaScript)
pour que les moteurs de recherche les indexent. Le JavaScript ne fait que
filtrer, chercher et ouvrir le détail.
"""
import html, json, re, unicodedata
from pathlib import Path

SOURCE_GABARIT = "cave-a-vin.html"     # d'où l'on reprend la nav et le pied de page
SORTIE = "nos-references.html"

LIBELLES = {"rouge": "Rouges", "blanc": "Blancs", "rose": "Rosés", "bulles": "Bulles",
            "moelleux": "Moelleux", "biere": "Bières", "spiritueux": "Spiritueux",
            "epicerie": "Épicerie fine", "autre": "Autres"}
SINGULIER = {"rouge": "Rouge", "blanc": "Blanc", "rose": "Rosé", "bulles": "Bulles",
             "moelleux": "Moelleux", "biere": "Bière", "spiritueux": "Spiritueux",
             "epicerie": "Épicerie", "autre": "Autre"}
ORDRE = ["rouge", "blanc", "rose", "bulles", "moelleux", "biere", "spiritueux", "epicerie", "autre"]
VERRE = {"rouge": "#7c2140", "blanc": "#d8c48a", "rose": "#d9a6a0", "bulles": "#2f4a33",
         "moelleux": "#c08a3e", "biere": "#6b3f1d", "spiritueux": "#5a3a24",
         "epicerie": "#8a6c3e", "autre": "#7a6355"}

def e(t):
    return html.escape(t or "", quote=True)

def sans_accent(t):
    return unicodedata.normalize("NFKD", (t or "").lower()).encode("ascii", "ignore").decode()

def silhouette(type_):
    """Bouteille dessinée, pour les références dont la photo manque encore."""
    c = VERRE.get(type_, VERRE["autre"])
    if type_ == "epicerie":                      # pot plutôt que bouteille
        corps = (f'<rect x="30" y="52" width="60" height="78" rx="8" fill="{c}"/>'
                 f'<rect x="26" y="40" width="68" height="16" rx="5" fill="{c}" opacity=".75"/>')
    elif type_ == "biere":
        corps = (f'<path d="M48 18h24v22c0 16 14 18 14 40v46a9 9 0 0 1-9 9H43a9 9 0 0 1-9-9V80'
                 f'c0-22 14-24 14-40z" fill="{c}"/>')
    else:
        corps = (f'<path d="M50 16h20v34c0 14 15 18 15 38v40a9 9 0 0 1-9 9H44a9 9 0 0 1-9-9V88'
                 f'c0-20 15-24 15-38z" fill="{c}"/>')
    return ('<svg class="ref-silhouette" viewBox="0 0 120 160" aria-hidden="true">'
            f'{corps}'
            '<rect x="34" y="92" width="52" height="36" rx="3" fill="#fdf9f0" opacity=".92"/>'
            '<rect x="42" y="102" width="36" height="3" rx="1.5" fill="#7a6355" opacity=".55"/>'
            '<rect x="46" y="110" width="28" height="2.5" rx="1.2" fill="#7a6355" opacity=".4"/>'
            '<rect x="44" y="117" width="32" height="2.5" rx="1.2" fill="#7a6355" opacity=".3"/>'
            '</svg>')

PETITS_MOTS = {"de", "du", "des", "et", "à", "au", "aux", "en", "sur", "sous", "chez"}
ACRONYMES = {"AOP", "AOC", "IGP", "IGT", "DOC", "DOCG", "DO", "VDP", "XO", "VS", "VSOP",
             "IPA", "NEIPA", "APA", "VDN", "BIB", "SO", "MC"}
_MOT = r"[^\W\d_]+"

def titre_propre(t):
    """Les fiches PDF crient parfois en capitales : « LA CUVÉE DES FADAS » → « La Cuvée des Fadas ».
    On ne touche qu'aux titres écrits majoritairement en majuscules."""
    t = (t or "").strip()
    lettres = [c for c in t if c.isalpha()]
    if not lettres or sum(1 for c in lettres if c.isupper()) < len(lettres) * .8:
        return t

    def cap(m):
        mot = m.group(0)
        return mot.upper() if mot.upper() in ACRONYMES else mot[:1].upper() + mot[1:].lower()

    t = re.sub(_MOT, cap, t)
    # « les Brunettes » garde sa majuscule : on ne rabaisse pas ce qui suit une ouverture
    t = re.sub(r"(?<![«(\"\u201c])(\s)(" + _MOT + r")",
               lambda m: m.group(1) + (m.group(2).lower()
                                       if m.group(2).lower() in PETITS_MOTS else m.group(2)), t)
    t = re.sub(r"(?<=\s)([DdLl])(['\u2019])", lambda m: m.group(1).lower() + m.group(2), t)
    t = re.sub(r"(\d)(Er|Ere|E|Eme|Ers)\b", lambda m: m.group(1) + m.group(2).lower(), t)
    return t

def court(t):
    """Enlève le point final des valeurs courtes (« La Gorge Fraîche. » → « La Gorge Fraîche »)."""
    t = (t or "").strip()
    return t[:-1].strip() if t.endswith(".") and t.count(".") == 1 else t

def ligne_meta(p):
    bouts = [court(p.get("appellation") or p.get("origine")), court(p.get("millesime"))]
    if p.get("alcool"): bouts.append(f"{p['alcool']} %")
    if p.get("contenance"): bouts.append(court(p["contenance"]))
    return " · ".join(b for b in bouts if b)

def bloc_detail(p):
    """Le détail complet, présent dans la page (donc indexable) et ouvert au clic."""
    d = []
    fiche = [("Producteur", court(p.get("producteur"))), ("Origine", p.get("origine")),
             ("Appellation", court(p.get("appellation"))), ("Cépages", p.get("cepages")),
             ("Style", p.get("style")), ("Millésime", p.get("millesime")),
             ("Vieillissement", p.get("vieillissement")),
             ("Degré", f"{p['alcool']} % vol." if p.get("alcool") else None),
             ("Contenance", p.get("contenance"))]
    lignes = "".join(f'<div class="fd-ligne"><dt>{k}</dt><dd>{e(v)}</dd></div>'
                     for k, v in fiche if v)
    if lignes:
        d.append(f'<dl class="fd-fiche">{lignes}</dl>')

    degust = [("À l’œil", p.get("visuel")), ("Au nez", p.get("nez")), ("En bouche", p.get("bouche"))]
    notes = "".join(f'<div class="fd-note"><h4>{k}</h4><p>{e(v)}</p></div>'
                    for k, v in degust if v)
    if notes:
        d.append(f'<div class="fd-degustation">{notes}</div>')
    if p.get("accords"):
        d.append(f'<div class="fd-accords"><h4>Accords mets &amp; vins</h4><p>{e(p["accords"])}</p></div>')
    if p.get("sources"):
        def domaine_de(u):
            return e(re.sub(r"^https?://(www\.)?", "", u).split("/")[0])
        liens = "".join('<li><a href="%s" target="_blank" rel="noopener nofollow">%s</a></li>'
                        % (e(u), domaine_de(u)) for u in p["sources"][:4])
        d.append(f'<div class="fd-sources"><h4>Sources</h4><ul>{liens}</ul></div>')
    return "".join(d)

def carte(p):
    t = p["type"]
    recherche = sans_accent(" ".join(str(p.get(k) or "") for k in
                ("nom", "producteur", "origine", "appellation", "cepages", "millesime", "style")))
    if p.get("images"):
        img = p["images"][0]
        alt = f'{p["nom"]}' + (f' — {p["producteur"]}' if p.get("producteur") else "")
        visuel = (f'<img src="{e(img)}" alt="{e(alt)}" loading="lazy" decoding="async" '
                  f'width="675" height="900">')
    else:
        visuel = silhouette(t)
    # les vues du volet ne sont chargées qu'à son ouverture : un attribut suffit,
    # pas la peine d'alourdir la grille de trois cents images
    vues = f' data-vues="{e(" ".join(p["images"]))}"' if p.get("images") else ""
    phrase = p.get("phrase") or p.get("bouche") or ""
    return f'''  <article class="ref-carte" data-type="{t}" data-cherche="{e(recherche)}"{vues}>
    <div class="ref-visuel">{visuel}</div>
    <div class="ref-corps">
      <span class="b-type {t}">{SINGULIER[t]}</span>
      <h3 class="ref-nom">{e(p["nom"])}</h3>
      {f'<p class="ref-domaine">{e(court(p["producteur"]))}</p>' if p.get("producteur") else ''}
      {f'<p class="ref-meta">{e(ligne_meta(p))}</p>' if ligne_meta(p) else ''}
      {f'<p class="ref-phrase">{e(phrase)}</p>' if phrase else ''}
      <p class="ref-prix">Prix en boutique</p>
      <button class="ref-ouvrir" type="button" aria-expanded="false">La fiche complète <span aria-hidden="true">→</span></button>
    </div>
    <div class="ref-detail" hidden>{bloc_detail(p)}</div>
  </article>'''

def carte_cachee(p):
    """La même fiche, sans sa vignette : le volet reconstruit la photo depuis
    data-vues. Sert à l'étagère de l'accueil et de la page cave, pour ouvrir un
    produit sans quitter la page ni recharger le catalogue entier."""
    t = p["type"]
    vues = f' data-vues="{e(" ".join(p["images"]))}"' if p.get("images") else ""
    visuel = "" if p.get("images") else f'<div class="ref-visuel">{silhouette(t)}</div>'
    return f'''<article class="ref-carte" id="fiche-{e(p["id"])}" data-type="{t}"{vues}>{visuel}
      <div class="ref-corps">
        <span class="b-type {t}">{SINGULIER[t]}</span>
        <h3 class="ref-nom">{e(p["nom"])}</h3>
        {f'<p class="ref-domaine">{e(court(p["producteur"]))}</p>' if p.get("producteur") else ''}
        <p class="ref-prix">Prix en boutique</p>
      </div>
      <div class="ref-detail" hidden>{bloc_detail(p)}</div>
    </article>'''

VOLET = '''<div class="ref-volet" id="refVolet" hidden>
  <div class="ref-volet-fond" data-fermer></div>
  <aside class="ref-volet-corps" role="dialog" aria-modal="true" aria-labelledby="refVoletTitre">
    <button class="ref-volet-fermer" type="button" data-fermer aria-label="Fermer la fiche">×</button>
    <div class="ref-volet-contenu" id="refVoletContenu"></div>
  </aside>
</div>'''

def dedoublonner(produits, bavard=True):
    """Le même vin décrit dans deux lots : on garde la fiche la mieux remplie."""
    garde = {}
    for x in produits:
        cle = (sans_accent(x["nom"]), sans_accent(x.get("producteur") or ""))
        note = (sum(1 for v in x.values() if v), 1 if x.get("images") else 0,
                1 if "REPRIS" in x.get("lot", "") else 0)
        if cle not in garde or note > garde[cle][0]:
            garde[cle] = (note, x)
    if bavard and len(garde) < len(produits):
        print(f"  {len(produits) - len(garde)} doublon(s) écarté(s)")
    return [v[1] for v in garde.values()]

def extraire(source, debut, fin):
    i = source.index(debut); j = source.index(fin, i) + len(fin)
    return source[i:j]

def main():
    produits = json.load(open("data/produits.json"))
    for x in produits:                       # les capitales des PDF, une bonne fois pour toutes
        x["nom"] = titre_propre(court(x.get("nom")))
        if x.get("producteur"):
            x["producteur"] = titre_propre(court(x["producteur"]))
    gabarit = open(SOURCE_GABARIT).read()
    nav = extraire(gabarit, '<!-- ==================== NAVIGATION', '</header>')
    pied = extraire(gabarit, '<!-- ==================== CONTACT / FOOTER', '</section>\n\n</body>')
    pied = pied.replace('</section>\n\n</body>', '</section>')
    nav = nav.replace(' aria-current="page"', '').replace(
        '<li><a href="/cave-a-vin">La cave</a></li>',
        '<li><a href="/cave-a-vin">La cave</a></li>')

    produits = dedoublonner(produits)

    compte = {t: sum(1 for p in produits if p["type"] == t) for t in ORDRE}
    presents = [t for t in ORDRE if compte[t]]
    pastilles = "".join(
        f'<button class="filtre" type="button" data-ref="{t}">{LIBELLES[t]} '
        f'<span class="filtre-nb">{compte[t]}</span></button>' for t in presents)
    rang = {t: i for i, t in enumerate(ORDRE)}
    produits.sort(key=lambda p: (rang.get(p["type"], 99), 0 if p.get("images") else 1,
                                 sans_accent(p.get("nom", ""))))
    # ItemList : les moteurs et les modèles de langage lisent le catalogue sans exécuter le JS
    elements = json.dumps([
        {"@type": "ListItem", "position": i + 1,
         "item": {k: v for k, v in {
             "@type": "Product",
             "name": x["nom"],
             "brand": {"@type": "Brand", "name": x["producteur"]} if x.get("producteur") else None,
             "category": LIBELLES.get(x["type"], ""),
             "description": (x.get("phrase") or x.get("bouche") or "")[:200] or None,
         }.items() if v}}
        for i, x in enumerate(produits)], ensure_ascii=False)

    cartes = "\n".join(carte(p) for p in produits)
    illustres = sum(1 for p in produits if p.get("images"))

    page = f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nos références — {len(produits)} vins, bières et spiritueux | Le Chai Gourmand, Cugnaux</title>
<meta name="description" content="Les {len(produits)} références de la cave du Chai Gourmand à Cugnaux, près de Toulouse : vins de vignerons indépendants, bières artisanales, spiritueux et épicerie fine, avec notes de dégustation et accords mets &amp; vins.">
<link rel="canonical" href="https://lechaigourmand.vercel.app/nos-references">
<meta name="theme-color" content="#1a0f14">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Le Chai Gourmand">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="Nos références — la cave du Chai Gourmand, Cugnaux">
<meta property="og:description" content="{len(produits)} vins, bières et spiritueux choisis un par un, avec leurs notes de dégustation.">
<meta property="og:url" content="https://lechaigourmand.vercel.app/nos-references">
<meta property="og:image" content="https://lechaigourmand.vercel.app/images/og-le-chai-gourmand.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='44' r='40' stroke='%23c9a876' stroke-width='5' fill='none' stroke-dasharray='30 11 8 11 42 10 14 11'/%3E%3Cpath d='M31 34 Q41 24 50 32 T69 32 C68 47 61 55 50 56 C39 55 32 47 31 34 Z' fill='%239d2c50'/%3E%3Cpath d='M30 14 C26 34 32 54 50 56 C68 54 74 34 70 14 Z' stroke='%237c2140' stroke-width='5' fill='none'/%3E%3Cpath d='M50 56 L50 76 M35 82 Q50 74 65 82' stroke='%237c2140' stroke-width='5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600&family=Pinyon+Script&family=Jost:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">
<script src="/site.js" defer></script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Accueil", "item": "https://lechaigourmand.vercel.app/"}},
        {{"@type": "ListItem", "position": 2, "name": "La cave", "item": "https://lechaigourmand.vercel.app/cave-a-vin"}},
        {{"@type": "ListItem", "position": 3, "name": "Nos références", "item": "https://lechaigourmand.vercel.app/nos-references"}}
      ]
    }},
    {{
      "@type": "CollectionPage",
      "name": "Nos références — Le Chai Gourmand",
      "description": "Catalogue de la cave du Chai Gourmand à Cugnaux : {len(produits)} références.",
      "url": "https://lechaigourmand.vercel.app/nos-references",
      "isPartOf": {{"@id": "https://lechaigourmand.vercel.app/#website"}},
      "about": {{"@id": "https://lechaigourmand.vercel.app/#chai-francazal"}},
      "mainEntity": {{
        "@type": "ItemList",
        "name": "Les références de la cave du Chai Gourmand",
        "numberOfItems": {len(produits)},
        "itemListElement": {elements}
      }}
    }}
  ]
}}
</script>
</head>
<body>

<div class="grain" aria-hidden="true"></div>
<div class="jauge" aria-hidden="true"></div>

{nav}

<!-- ==================== HERO DE PAGE ==================== -->
<section class="hero-page">
  <div class="contenu hero-page-grille">
    <div class="hero-page-texte">
      <nav aria-label="Fil d'ariane">
        <ol class="fil">
          <li><a href="/">Accueil</a></li>
          <li><a href="/cave-a-vin">La cave</a></li>
          <li><span aria-current="page">Nos références</span></li>
        </ol>
      </nav>
      <p class="sur-titre entree">La cave, référence par référence</p>
      <h1 class="entree e2">Chaque bouteille,<br><span class="accent-script">et son histoire.</span></h1>
      <p class="chapeau entree e3">
        Vins de vignerons indépendants, bières artisanales, spiritueux et épicerie fine —
        avec les notes de dégustation et les accords conseillés par Adrien.
        Cherchez un domaine, une appellation, un cépage.
      </p>
      <div class="hero-chips entree e4" aria-label="En bref">
        <span class="hero-chip">{compte['rouge']} rouges</span>
        <span class="hero-chip">{compte['blanc']} blancs</span>
        <span class="hero-chip">{compte['biere']} bières</span>
        <span class="hero-chip">{compte['spiritueux']} spiritueux</span>
      </div>
    </div>

    <div class="hero-page-embleme entree e3" aria-hidden="true">
      <span class="poussiere" style="width:3px;height:3px;left:12%;top:18%;animation-delay:.8s"></span>
      <span class="poussiere" style="width:2px;height:2px;left:82%;top:30%;animation-delay:2.4s"></span>
      <svg class="embleme" viewBox="0 0 340 340" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs><radialGradient id="lueurRefs" cx="50%" cy="50%" r="55%">
          <stop offset="0" stop-color="#9d2c50" stop-opacity=".4"/>
          <stop offset="1" stop-color="#9d2c50" stop-opacity="0"/>
        </radialGradient></defs>
        <circle cx="170" cy="170" r="168" fill="url(#lueurRefs)"/>
        <g class="anneau" opacity=".5">
          <circle cx="170" cy="170" r="148" stroke="#c9a876" stroke-width="5"
                  stroke-dasharray="40 14 9 14 64 12 24 16" stroke-linecap="round"/>
        </g>
        <g stroke="#e6d3ae" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M96 96h32v34c0 18 18 22 18 46v92a9 9 0 0 1-9 9h-50a9 9 0 0 1-9-9v-92c0-24 18-28 18-46z"/>
          <path d="M196 96h32v34c0 18 18 22 18 46v92a9 9 0 0 1-9 9h-50a9 9 0 0 1-9-9v-92c0-24 18-28 18-46z"/>
          <path d="M78 268h184"/>
        </g>
      </svg>
      <span class="embleme-script">la cave</span>
    </div>
  </div>
  <div class="hero-filet" aria-hidden="true"><span>✦</span></div>
</section>

<svg class="transition-vague" viewBox="0 0 1440 90" preserveAspectRatio="none" aria-hidden="true" style="background:var(--noir)">
  <path d="M0 50 C240 6 480 88 720 44 C960 4 1200 84 1440 40 L1440 90 L0 90 Z" fill="#f6efe2"/>
</svg>

<!-- ==================== CATALOGUE ==================== -->
<section class="section s-creme" id="references">
  <div class="contenu">

    <div class="ref-barre" id="refBarre">
      <div class="ref-recherche">
        <label for="refCherche" class="visuellement-cache">Chercher une référence</label>
        <input type="search" id="refCherche" placeholder="Domaine, appellation, cépage…" autocomplete="off">
      </div>
      <div class="filtres-cave ref-filtres" role="group" aria-label="Filtrer par catégorie">
        <button class="filtre actif" type="button" data-ref="tous">Tout <span class="filtre-nb">{len(produits)}</span></button>
        {pastilles}
      </div>
      <p class="ref-compte" id="refCompte" aria-live="polite">{len(produits)} références</p>
    </div>

    <div class="ref-grille" id="refGrille">
{cartes}
    </div>

    <p class="ref-vide" id="refVide" hidden>
      Aucune référence ne correspond — essayez un autre domaine, ou demandez à Adrien,
      la cave en compte bien davantage en boutique.
    </p>

    <p class="etagere-note rv" style="margin-top:clamp(2rem,4vw,3rem)">
      Toute la cave et l’épicerie fine, sélectionnées une à une par Adrien.
      Les prix sont donnés en boutique, où il vous conseillera avec plaisir.
    </p>

    <div class="centre-cta rv">
      <a class="btn btn-plein" href="tel:+33685362265">Un conseil ? 06 85 36 22 65</a>
    </div>
  </div>
</section>

<!-- volet de détail -->
<div class="ref-volet" id="refVolet" hidden>
  <div class="ref-volet-fond" data-fermer></div>
  <aside class="ref-volet-corps" role="dialog" aria-modal="true" aria-labelledby="refVoletTitre">
    <button class="ref-volet-fermer" type="button" data-fermer aria-label="Fermer la fiche">×</button>
    <div class="ref-volet-contenu" id="refVoletContenu"></div>
  </aside>
</div>

<svg class="transition-vague" viewBox="0 0 1440 90" preserveAspectRatio="none" aria-hidden="true" style="background:var(--creme)">
  <path d="M0 46 C240 92 480 4 720 42 C960 80 1200 8 1440 50 L1440 90 L0 90 Z" fill="#1a0f14"/>
</svg>

{pied}

</body>
</html>
'''
    Path(SORTIE).write_text(page)
    print(f"{SORTIE} généré : {len(produits)} références, {illustres} illustrées")
    print("Répartition :", ", ".join(f"{LIBELLES[t]} {compte[t]}" for t in presents))
    print(f"Poids de la page : {len(page)/1000:.0f} Ko")

if __name__ == "__main__":
    main()
