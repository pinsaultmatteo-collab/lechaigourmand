#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère /journal et ses articles à partir de contenu/journal/*.md.

    python3 outils/generer_journal.py

Ajouter un article : déposer un .md dans contenu/journal/ (en-tête titre,
description, resume, categorie, date, lecture, image, alt — puis --- et le
corps en Markdown) et relancer. Le sommaire, les liens croisés, le plan du
site et les données structurées suivent tout seuls.
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from journal_texte import lire, rendre, e
from generer_catalogue import extraire

SOURCE = Path("contenu/journal")
DOSSIER = Path("journal")
GABARIT = "cave-a-vin.html"
SITE = "https://lechaigourmand.vercel.app"

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]

def en_lettres(iso):
    a, m, j = iso.split("-")
    return f"{int(j)} {MOIS[int(m) - 1]} {a}"

ICONE = ""      # rempli au démarrage depuis le gabarit

def entete(titre, description, url, image, ld, categorie=None):
    og = f"{SITE}{image}" if image else f"{SITE}/images/og-le-chai-gourmand.jpg"
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(titre)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#1a0f14">
<meta property="og:type" content="{'article' if categorie else 'website'}">
<meta property="og:site_name" content="Le Chai Gourmand">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{e(titre)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
{ICONE}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600&family=Pinyon+Script&family=Jost:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">
<script src="/site.js" defer></script>
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body>
<div class="grain" aria-hidden="true"></div>
'''

def fil(pieces):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u}
        for i, (n, u) in enumerate(pieces)]}

def carte(a):
    visuel = (f'<div class="art-vignette"><img src="{e(a["image"])}" alt="{e(a.get("alt", ""))}" '
              f'loading="lazy" decoding="async" width="1200" height="800"></div>'
              if a.get("image") else "")
    return f'''      <article class="art-carte rv">
        <a href="/journal/{a["slug"]}">
          {visuel}
          <div class="art-carte-corps">
            <span class="art-cat">{e(a["categorie"])}</span>
            <h2>{e(a["titre"])}</h2>
            <p class="art-resume">{e(a["resume"])}</p>
            <p class="art-meta"><time datetime="{a["date"]}">{en_lettres(a["date"])}</time>
              <span class="puce" aria-hidden="true"></span>{e(a["lecture"])} min de lecture</p>
          </div>
        </a>
      </article>'''

def page_article(a, autres, nav, pied):
    url = f"{SITE}/journal/{a['slug']}"
    ld = {"@context": "https://schema.org", "@graph": [
        fil([("Accueil", "/"), ("Journal", "/journal"), (a["titre"], f"/journal/{a['slug']}")]),
        {"@type": "BlogPosting", "headline": a["titre"], "description": a["description"],
         "datePublished": a["date"], "dateModified": a["date"],
         "inLanguage": "fr-FR", "articleSection": a["categorie"],
         "mainEntityOfPage": {"@type": "WebPage", "@id": url},
         "image": SITE + a["image"] if a.get("image") else None,
         "author": {"@type": "Organization", "name": "Le Chai Gourmand", "url": SITE + "/"},
         "publisher": {"@id": SITE + "/#chai-francazal"}}]}
    ld["@graph"][1] = {k: v for k, v in ld["@graph"][1].items() if v is not None}

    visuel = (f'''
  <figure class="art-photo rv">
    <img src="{e(a["image"])}" alt="{e(a.get("alt", ""))}" width="1200" height="800" decoding="async">
  </figure>''' if a.get("image") else "")

    lire_aussi = "\n".join(f'''        <a class="art-lien rv" href="/journal/{x["slug"]}">
          <span class="art-cat">{e(x["categorie"])}</span>
          <span class="art-lien-titre">{e(x["titre"])}</span>
        </a>''' for x in autres)

    return entete(f'{a["titre"]} | Le Chai Gourmand', a["description"], url,
                  a.get("image"), ld, a["categorie"]) + f'''{nav}

<section class="hero-page hero-article">
  <div class="hero-page-fond" aria-hidden="true"></div>
  <div class="contenu hero-page-grille hero-article-grille">
    <div class="hero-page-texte">
      <nav class="fil" aria-label="Fil d'Ariane">
        <ol>
          <li><a href="/">Accueil</a></li>
          <li><a href="/journal">Journal</a></li>
          <li><span aria-current="page">{e(a["categorie"])}</span></li>
        </ol>
      </nav>
      <p class="sur-titre entree">{e(a["categorie"])}</p>
      <h1 class="entree e2">{e(a["titre"])}</h1>
      <p class="chapeau entree e3">{e(a["resume"])}</p>
      <p class="art-meta entree e4"><time datetime="{a["date"]}">{en_lettres(a["date"])}</time>
        <span class="puce" aria-hidden="true"></span>{e(a["lecture"])} min de lecture</p>
    </div>
  </div>
  <div class="hero-filet" aria-hidden="true"><span>✦</span></div>
</section>

<section class="section s-creme">
  <div class="contenu contenu-article">{visuel}
    <div class="art-corps rv">
{rendre(a["corps"])}
    </div>

    <div class="art-signature rv">
      <p>Écrit au comptoir du Chai Gourmand, à Cugnaux.<br>
        Une question sur une bouteille ? Passez, ou appelez le
        <a href="tel:+33685362265">06 85 36 22 65</a>.</p>
      <div class="art-signature-ctas">
        <a class="btn btn-plein" href="/nos-references">Voir toutes les références</a>
        <a class="btn ref-plus" href="/nos-adresses">Nos deux adresses</a>
      </div>
    </div>

    <aside class="art-suite rv" aria-label="À lire aussi">
      <h2 class="sous-titre-cave">À lire aussi</h2>
      <div class="art-liens">
{lire_aussi}
      </div>
    </aside>
  </div>
</section>

<svg class="transition-vague" viewBox="0 0 1440 90" preserveAspectRatio="none" aria-hidden="true" style="background:var(--creme)">
  <path d="M0 46 C240 92 480 4 720 42 C960 80 1200 8 1440 50 L1440 90 L0 90 Z" fill="#1a0f14"/>
</svg>

{pied}

</body>
</html>
'''

def page_index(articles, nav, pied):
    url = f"{SITE}/journal"
    ld = {"@context": "https://schema.org", "@graph": [
        fil([("Accueil", "/"), ("Journal", "/journal")]),
        {"@type": "Blog", "name": "Le journal du Chai Gourmand", "url": url,
         "inLanguage": "fr-FR",
         "description": "Accords mets et vins, conseils de conservation, terroirs et vie de la maison, "
                        "par la cave du Chai Gourmand à Cugnaux près de Toulouse.",
         "publisher": {"@id": SITE + "/#chai-francazal"},
         "blogPost": [{"@type": "BlogPosting", "headline": a["titre"],
                       "description": a["description"], "datePublished": a["date"],
                       "url": f"{SITE}/journal/{a['slug']}"} for a in articles]}]}
    return entete("Le journal du Chai Gourmand — accords, conseils et terroirs",
                  "Accords mets et vins, conservation des bouteilles, terroirs et coffrets cadeaux : "
                  "les conseils du caviste du Chai Gourmand, à Cugnaux près de Toulouse.",
                  url, "/images/planche-tapas-comptoir-le-chai-gourmand.webp", ld) + f'''{nav}

<section class="hero-page">
  <div class="hero-page-fond" aria-hidden="true"></div>
  <div class="contenu hero-page-grille">
    <div class="hero-page-texte">
      <nav class="fil" aria-label="Fil d'Ariane">
        <ol>
          <li><a href="/">Accueil</a></li>
          <li><span aria-current="page">Journal</span></li>
        </ol>
      </nav>
      <p class="sur-titre entree">Le journal de la maison</p>
      <h1 class="entree e2">Ce qu'on raconte<br><span class="accent-script">au comptoir.</span></h1>
      <p class="chapeau entree e3">
        Les questions qui reviennent, les réponses qu'on donne : accords mets et vins, conservation,
        terroirs, coffrets. De quoi choisir mieux, chez nous comme ailleurs.
      </p>
    </div>

    <div class="hero-page-embleme entree e3" aria-hidden="true">
      <span class="poussiere" style="width:3px;height:3px;left:14%;top:20%;animation-delay:.6s"></span>
      <span class="poussiere" style="width:2px;height:2px;left:80%;top:34%;animation-delay:2.6s"></span>
      <svg class="embleme" viewBox="0 0 340 340" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="lueurJournal" cx="50%" cy="50%" r="55%">
            <stop offset="0" stop-color="#9d2c50" stop-opacity=".4"/>
            <stop offset="1" stop-color="#9d2c50" stop-opacity="0"/>
          </radialGradient>
        </defs>
        <circle cx="170" cy="170" r="168" fill="url(#lueurJournal)"/>
        <g class="anneau" opacity=".5">
          <circle cx="170" cy="170" r="148" stroke="#c9a876" stroke-width="5"
                  stroke-dasharray="40 14 9 14 64 12 24 16" stroke-linecap="round"/>
        </g>
        <g stroke="#e6d3ae" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M104 96 h96 a10 10 0 0 1 10 10 v128 a10 10 0 0 1 -10 10 h-96 a10 10 0 0 1 -10 -10 v-128 a10 10 0 0 1 10 -10 z"/>
          <path d="M152 96 v148" opacity=".7"/>
          <path d="M118 128 h22 M118 150 h22 M118 172 h16"/>
          <path d="M166 128 h22 M166 150 h22 M166 172 h16"/>
          <path d="M210 116 c16 6 22 18 22 34 v104" opacity=".65"/>
        </g>
      </svg>
      <span class="embleme-script">le journal</span>
    </div>
  </div>
  <div class="hero-filet" aria-hidden="true"><span>✦</span></div>
</section>

<section class="section s-creme">
  <div class="contenu">
    <div class="art-grille">
{chr(10).join(carte(a) for a in articles)}
    </div>

    <div class="centre-cta rv">
      <a class="btn btn-plein" href="/nos-references">Voir toutes les références</a>
    </div>
  </div>
</section>

<svg class="transition-vague" viewBox="0 0 1440 90" preserveAspectRatio="none" aria-hidden="true" style="background:var(--creme)">
  <path d="M0 46 C240 92 480 4 720 42 C960 80 1200 8 1440 50 L1440 90 L0 90 Z" fill="#1a0f14"/>
</svg>

{pied}

</body>
</html>
'''

def inscrire_au_plan(articles):
    """Plan du site et llms.txt suivent les articles : un .md de plus suffit."""
    urls = "".join(f"""  <url>
    <loc>{SITE}/journal/{a['slug']}</loc>
    <lastmod>{a['date']}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>0.6</priority>
  </url>
""" for a in articles)
    plan = Path("sitemap.xml"); s = plan.read_text(encoding="utf-8")
    bloc = f"""  <!-- journal:début -->
  <url>
    <loc>{SITE}/journal</loc>
    <lastmod>{articles[0]['date']}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
{urls}  <!-- journal:fin -->"""
    plan.write_text(re.sub(r"  <!-- journal:début -->.*?  <!-- journal:fin -->",
                           lambda _: bloc, s, flags=re.S), encoding="utf-8")

    lignes = "\n".join(f"  - [{a['titre']}]({SITE}/journal/{a['slug']}) — {a['resume']}"
                        for a in articles)
    txt = Path("llms.txt"); t = txt.read_text(encoding="utf-8")
    bloc = (f"[//]: # (journal:début)\n"
            f"- [Journal]({SITE}/journal) : les conseils du caviste, {len(articles)} articles\n"
            f"{lignes}\n[//]: # (journal:fin)")
    txt.write_text(re.sub(r"\[//\]: # \(journal:début\).*?\[//\]: # \(journal:fin\)",
                          lambda _: bloc, t, flags=re.S), encoding="utf-8")

def main():
    global ICONE
    gabarit = open(GABARIT).read()
    ICONE = re.search(r'<link rel="icon"[^>]*>', gabarit).group(0)
    nav = extraire(gabarit, "<!-- ==================== NAVIGATION", "</header>")
    nav = nav.replace(' aria-current="page"', '')
    nav_index = nav.replace('<li><a href="/journal">Journal</a></li>',
                            '<li><a href="/journal" aria-current="page">Journal</a></li>')
    pied = extraire(gabarit, "<!-- ==================== CONTACT / FOOTER", "</section>\n\n</body>")
    pied = pied.replace("</section>\n\n</body>", "</section>")

    articles = []
    for f in sorted(SOURCE.glob("*.md")):
        a = lire(f)
        a["slug"] = f.stem
        manque = [k for k in ("titre", "description", "resume", "categorie", "date", "lecture")
                  if not a.get(k)]
        if manque:
            sys.exit(f"{f.name} : en-tête incomplet ({', '.join(manque)})")
        articles.append(a)
    articles.sort(key=lambda a: (a["date"], a["titre"]), reverse=True)

    DOSSIER.mkdir(exist_ok=True)
    (DOSSIER / "index.html").write_text(page_index(articles, nav_index, pied), encoding="utf-8")
    for i, a in enumerate(articles):
        autres = [articles[(i + 1) % len(articles)], articles[(i + 2) % len(articles)]]
        (DOSSIER / f"{a['slug']}.html").write_text(
            page_article(a, autres, nav, pied), encoding="utf-8")

    inscrire_au_plan(articles)

    mots = sum(len(a["corps"].split()) for a in articles)
    print(f"journal généré : {len(articles)} articles, {mots} mots")
    for a in articles:
        print(f"   /journal/{a['slug']:38s} {a['categorie']:22s} {len(a['corps'].split()):4d} mots")

if __name__ == "__main__":
    main()
