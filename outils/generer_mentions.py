#!/usr/bin/env python3
"""Fabrique /mentions-legales — « python3 outils/generer_mentions.py ».

La navigation et le pied de page sont repris du gabarit, comme pour le
catalogue et le journal : une page légale qui dériverait du reste du site
donnerait l'impression d'avoir été oubliée.

Les champs que seul le gérant connaît — raison sociale, SIRET, capital —
sont rassemblés dans IDENTITE ci-dessous. Tant qu'une valeur vaut None, la
page affiche « à compléter » en évidence plutôt que d'inventer.
"""
import datetime
import io
import os

GABARIT = "cave-a-vin.html"
SORTIE = "mentions-legales.html"
SITE = "https://chai-gourmand.fr"

# ---------------------------------------------------------------------------
# À COMPLÉTER PAR LE CLIENT — demandez-lui son extrait Kbis, tout y figure.
# ---------------------------------------------------------------------------
# Relevé sur le registre national des entreprises (SIREN 990 748 394), le
# 02/10/2026. Le directeur de la publication est, de par la loi, le
# représentant légal : pour une SAS, son président.
IDENTITE = {
    "raison_sociale":      "Le Chai Gourmand",
    "forme_juridique":     "SAS (société par actions simplifiée) au capital de 500 €",
    "siege":               "14 rue de Cezerou, 31270 Cugnaux",
    "siret":               "990 748 394 00014",
    "rcs":                 "990 748 394 R.C.S. Toulouse",
    "tva":                 "FR03990748394",
    "directeur":           "Dylan Galliez, président",
    "licence":             None,   # ex. « Licence IV n° … » — absente du registre
}

# Champs que la page tait plutôt que de les afficher vides : la licence n'est
# pas au registre, elle se trouve sur le permis délivré par la mairie.
FACULTATIFS = {"licence"}

TELEPHONE = "06 85 36 22 65"
TELEPHONE_LIEN = "+33685362265"
COURRIEL = "bonjour@chai-gourmand.fr"

ADRESSES = [
    ("Le Chai — Francazal", "9 rue Alfred Sauvy, 31270 Cugnaux"),
    ("L'Annexe — Cézerou", "14 rue de Cezerou, 31270 Cugnaux"),
]


def e(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def valeur(cle, intitule):
    """Une ligne de la fiche d'identité, ou la mention qu'il manque."""
    v = IDENTITE.get(cle)
    if not v and cle in FACULTATIFS:
        return ""
    contenu = (e(v) if v else
               '<span class="ml-manque">à compléter</span>')
    return f'<div class="ml-ligne"><dt>{e(intitule)}</dt><dd>{contenu}</dd></div>'


def extraire(source, debut, fin):
    i = source.index(debut)
    j = source.index(fin, i) + len(fin)
    return source[i:j]


def page(nav, pied):
    maj = datetime.date.today().strftime("%d/%m/%Y")
    adresses = "".join(
        f'<div class="ml-ligne"><dt>{e(nom)}</dt><dd>{e(adr)}</dd></div>'
        for nom, adr in ADRESSES)

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mentions légales — Le Chai Gourmand, Cugnaux</title>
<meta name="description" content="Mentions légales du site du Chai Gourmand : éditeur, hébergeur, propriété intellectuelle, données personnelles et mesure d’audience.">
<link rel="canonical" href="{SITE}/mentions-legales">
<meta name="robots" content="index, follow">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Le Chai Gourmand">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="Mentions légales — Le Chai Gourmand">
<meta property="og:description" content="Éditeur, hébergeur, données personnelles et mesure d’audience du site du Chai Gourmand.">
<meta property="og:url" content="{SITE}/mentions-legales">
<meta property="og:image" content="{SITE}/images/og-le-chai-gourmand.jpg">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600&family=Pinyon+Script&family=Jost:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css">
<script src="/config.js"></script>
<script src="/mesure.js" defer></script>
<script src="/site.js" defer></script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "Mentions légales",
  "url": "{SITE}/mentions-legales",
  "inLanguage": "fr-FR",
  "isPartOf": {{"@id": "{SITE}/#website"}},
  "dateModified": "{datetime.date.today().isoformat()}"
}}
</script>
</head>
<body>
<div class="grain" aria-hidden="true"></div>

{nav}

<main class="section s-creme ml-page">
  <div class="contenu ml-contenu">

    <nav class="fil" aria-label="Fil d’Ariane">
      <a href="/">Accueil</a> <span aria-hidden="true">→</span> <span>Mentions légales</span>
    </nav>

    <h1 class="ml-titre">Mentions légales</h1>
    <p class="ml-chapeau">Les informations que la loi impose de publier, et ce que devient ce que
      vous nous confiez. Dernière mise à jour le {maj}.</p>

    <section class="ml-bloc">
      <h2>Éditeur du site</h2>
      <dl class="ml-fiche">
        {valeur("raison_sociale", "Raison sociale")}
        {valeur("forme_juridique", "Forme juridique")}
        {valeur("siege", "Siège social")}
        {valeur("siret", "SIRET")}
        {valeur("rcs", "RCS")}
        {valeur("tva", "TVA intracommunautaire")}
        {valeur("directeur", "Directeur de la publication")}
        {valeur("licence", "Licence de débit de boissons")}
        <div class="ml-ligne"><dt>Téléphone</dt><dd><a href="tel:{TELEPHONE_LIEN}">{TELEPHONE}</a></dd></div>
        <div class="ml-ligne"><dt>Courriel</dt><dd><a href="mailto:{COURRIEL}">{COURRIEL}</a></dd></div>
      </dl>
    </section>

    <section class="ml-bloc">
      <h2>Établissements</h2>
      <dl class="ml-fiche">{adresses}</dl>
    </section>

    <section class="ml-bloc">
      <h2>Hébergement</h2>
      <p>Le site est hébergé par <strong>Vercel Inc.</strong>, 440 N Barranca Avenue #4133,
        Covina, CA 91723, États-Unis —
        <a href="https://vercel.com" target="_blank" rel="noopener">vercel.com</a>.</p>
    </section>

    <section class="ml-bloc">
      <h2>Conception</h2>
      <p>Site conçu et réalisé par
        <a href="https://www.agence-pmc-marketing.com/" target="_blank" rel="noopener">PMC Marketing</a>,
        agence digitale à Toulouse.</p>
    </section>

    <section class="ml-bloc">
      <h2>Propriété intellectuelle</h2>
      <p>Les textes, la charte graphique et les photographies de ce site appartiennent au Chai
        Gourmand ou à leurs auteurs respectifs. Toute reproduction, même partielle, est soumise
        à autorisation préalable. Les noms des domaines, maisons et marques cités dans le
        catalogue restent la propriété de leurs titulaires ; ils sont mentionnés à titre
        d’information sur les produits proposés à la vente en boutique.</p>
    </section>

    <section class="ml-bloc" id="donnees">
      <h2>Données personnelles</h2>
      <p>Le responsable du traitement est l’éditeur du site, identifié ci-dessus. Trois formulaires
        collectent des informations, et rien d’autre n’est demandé :</p>

      <dl class="ml-fiche">
        <div class="ml-ligne">
          <dt>Réservation</dt>
          <dd>Nom, téléphone, adresse e-mail et, s’il y en a un, le message laissé. Ces données
            servent uniquement à tenir la table et à vous envoyer la confirmation ou l’annulation.
            Elles sont conservées douze mois, puis effacées.</dd>
        </div>
        <div class="ml-ligne">
          <dt>Lettre d’information</dt>
          <dd>Votre adresse e-mail, avec votre accord, pour vous annoncer les rendez-vous de la
            maison. Chaque envoi porte un lien de désinscription ; l’adresse est conservée jusqu’à
            ce que vous vous retiriez.</dd>
        </div>
        <div class="ml-ligne">
          <dt>Mesure d’audience</dt>
          <dd>Des statistiques de fréquentation anonymes — pages vues, provenance, appareil —
            pour savoir ce qui vous intéresse. Voir la section suivante pour vous y opposer.</dd>
        </div>
      </dl>

      <p>Ces informations ne sont ni vendues ni cédées. Elles sont traitées par les prestataires
        strictement nécessaires au fonctionnement du site : <strong>Vercel</strong> (hébergement),
        <strong>Supabase</strong> (base de données), <strong>Brevo</strong> (envoi des courriels)
        et <strong>Google</strong> (mesure d’audience). Certains sont établis hors de l’Union
        européenne ; les transferts correspondants s’appuient sur les clauses contractuelles types
        de la Commission européenne.</p>

      <p>Conformément au règlement européen sur la protection des données, vous disposez d’un droit
        d’accès, de rectification, d’effacement, d’opposition, de limitation et de portabilité.
        Pour l’exercer, écrivez à <a href="mailto:{COURRIEL}">{COURRIEL}</a> ou appelez le
        <a href="tel:{TELEPHONE_LIEN}">{TELEPHONE}</a>. Si la réponse ne vous satisfait pas, vous
        pouvez saisir la <a href="https://www.cnil.fr/fr/plaintes" target="_blank" rel="noopener">CNIL</a>.</p>
    </section>

    <section class="ml-bloc" id="cookies">
      <h2>Cookies et mesure d’audience</h2>
      <p>Ce site utilise <strong>Google Analytics 4</strong> pour mesurer sa fréquentation. Cet outil
        dépose deux cookies (<code>_ga</code> et <code>_ga_…</code>) qui permettent de distinguer les
        visites sans vous identifier. Aucun cookie publicitaire n’est déposé, et aucune donnée n’est
        utilisée à des fins de ciblage.</p>
      <p>Vous pouvez refuser cette mesure à tout moment : votre choix est gardé dans votre navigateur
        et rien n’est envoyé tant qu’il reste actif.</p>
      <p class="ml-choix">
        <button class="btn btn-plein" type="button" data-mesure-refuser>Refuser la mesure d’audience</button>
        <button class="btn ref-plus" type="button" data-mesure-accepter hidden>Réactiver la mesure</button>
        <span class="ml-etat" data-mesure-etat aria-live="polite"></span>
      </p>
    </section>

    <section class="ml-bloc">
      <h2>Responsabilité</h2>
      <p>Les informations publiées — horaires, programmation, disponibilité des références — sont
        tenues à jour avec soin, mais une cuvée peut être épuisée ou une soirée déplacée. En cas de
        doute, un appel au <a href="tel:{TELEPHONE_LIEN}">{TELEPHONE}</a> fait foi. Les liens vers
        des sites tiers n’engagent que leurs éditeurs.</p>
      <p>Aucune vente en ligne n’est proposée sur ce site : les commandes se règlent en boutique.
        La vente d’alcool aux mineurs de moins de dix-huit ans est interdite.
        L’abus d’alcool est dangereux pour la santé, à consommer avec modération.</p>
    </section>

    <section class="ml-bloc">
      <h2>Droit applicable</h2>
      <p>Le présent site est soumis au droit français. Tout litige relève de la compétence des
        tribunaux de Toulouse, à défaut de règlement amiable.</p>
    </section>

  </div>
</main>

{pied}
</body>
</html>
'''


def main():
    racine = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    os.chdir(racine)
    gabarit = io.open(GABARIT, encoding="utf-8").read()
    nav = extraire(gabarit, "<!-- ==================== NAVIGATION", "</header>")
    nav = nav.replace(' aria-current="page"', "")
    pied = extraire(gabarit, "<!-- ==================== CONTACT / FOOTER", "</section>\n\n</body>")
    pied = pied.replace("</section>\n\n</body>", "</section>")

    io.open(SORTIE, "w", encoding="utf-8").write(page(nav, pied))
    manquants = [k for k, v in IDENTITE.items() if not v and k not in FACULTATIFS]
    tus = [k for k, v in IDENTITE.items() if not v and k in FACULTATIFS]
    print(f"  ✓ {SORTIE}")
    if manquants:
        print(f"  ⚠ {len(manquants)} champ(s) à compléter dans outils/generer_mentions.py :")
        for k in manquants:
            print(f"      {k}")
    if tus:
        print(f"  · non affiché(s) faute de valeur : {', '.join(tus)}")


if __name__ == "__main__":
    main()
