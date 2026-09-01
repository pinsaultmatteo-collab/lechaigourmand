# -*- coding: utf-8 -*-
"""Un rendu Markdown minimal, taillé pour les articles du journal.

Pas de dépendance : on ne gère que ce qu'on écrit — titres, paragraphes,
listes, tableaux, citations, gras, italique et liens. Tout le reste est
échappé, donc un article ne peut pas casser la page.
"""
import html, re

def e(t):
    return html.escape(t or "", quote=True)

def _enligne(t):
    """Gras, italique et liens, une fois le texte échappé.
    Les guillemets ne sont pas échappés : on est dans du texte, pas dans un attribut."""
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t

def _tableau(lignes):
    """| a | b | avec la ligne de tirets pour séparer l'en-tête."""
    cases = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lignes]
    cases = [c for c in cases if not all(re.fullmatch(r":?-{2,}:?", x) for x in c)]
    if not cases:
        return ""
    tete = "".join(f"<th>{_enligne(c)}</th>" for c in cases[0])
    corps = "".join("<tr>" + "".join(f"<td>{_enligne(c)}</td>" for c in ligne) + "</tr>"
                    for ligne in cases[1:])
    return (f'<div class="art-tableau"><table><thead><tr>{tete}</tr></thead>'
            f"<tbody>{corps}</tbody></table></div>")

def rendre(texte):
    sortie, tampon, mode = [], [], None

    def vider():
        nonlocal tampon, mode
        if not tampon:
            mode = None
            return
        if mode == "ul":
            sortie.append("<ul>" + "".join(f"<li>{_enligne(x)}</li>" for x in tampon) + "</ul>")
        elif mode == "ol":
            sortie.append("<ol>" + "".join(f"<li>{_enligne(x)}</li>" for x in tampon) + "</ol>")
        elif mode == "table":
            sortie.append(_tableau(tampon))
        elif mode == "quote":
            sortie.append("<blockquote><p>" + _enligne(" ".join(tampon)) + "</p></blockquote>")
        else:
            sortie.append("<p>" + _enligne(" ".join(tampon)) + "</p>")
        tampon, mode = [], None

    for brute in texte.split("\n"):
        ligne = brute.rstrip()
        if not ligne.strip():
            vider(); continue
        if ligne.startswith("### "):
            vider(); sortie.append(f"<h3>{_enligne(ligne[4:])}</h3>"); continue
        if ligne.startswith("## "):
            vider(); sortie.append(f"<h2>{_enligne(ligne[3:])}</h2>"); continue
        if ligne.startswith("> "):
            if mode != "quote": vider(); mode = "quote"
            tampon.append(ligne[2:]); continue
        if ligne.lstrip().startswith("|"):
            if mode != "table": vider(); mode = "table"
            tampon.append(ligne); continue
        if re.match(r"^\s*[-*] ", ligne):
            if mode != "ul": vider(); mode = "ul"
            tampon.append(re.sub(r"^\s*[-*] ", "", ligne)); continue
        if re.match(r"^\s*\d+\. ", ligne):
            if mode != "ol": vider(); mode = "ol"
            tampon.append(re.sub(r"^\s*\d+\. ", "", ligne)); continue
        if mode in ("ul", "ol", "quote") and ligne.startswith("  "):
            tampon[-1] += " " + ligne.strip(); continue   # suite d'un point de liste
        if mode not in (None, "p"):
            vider()
        mode = "p"; tampon.append(ligne.strip())
    vider()
    return "\n".join(sortie)

def lire(chemin):
    """En-tête « clé: valeur » jusqu'à la ligne ---, puis le corps."""
    brut = open(chemin, encoding="utf-8").read()
    tete, _, corps = brut.partition("\n---\n")
    fiche = {}
    for ligne in tete.split("\n"):
        if ":" in ligne:
            cle, _, val = ligne.partition(":")
            fiche[cle.strip()] = val.strip()
    fiche["corps"] = corps.strip()
    return fiche
