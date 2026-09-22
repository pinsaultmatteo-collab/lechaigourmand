#!/usr/bin/env python3
"""Crée (ou met à jour) le webhook de rebonds chez Brevo, par l'API.

    python3 outils/brancher_webhook.py

Le menu des webhooks se déplace au fil des versions de l'interface Brevo.
L'API, elle, ne bouge pas : une requête, et c'est branché.

Le script demande la clé API Brevo et le jeton partagé au clavier — rien ne
s'affiche pendant la frappe, et rien n'atterrit dans l'historique du terminal.

Options : --lister pour voir les webhooks existants, --supprimer ID.
"""
import getpass
import json
import sys
import urllib.error
import urllib.request

API = "https://api.brevo.com/v3/webhooks"
ADRESSE = "https://chai-gourmand.fr/api/rebond-courriel"

# Les événements sur lesquels la route agit vraiment. Inutile de s'abonner aux
# retards passagers : ils sont ignorés à l'arrivée, autant ne pas les recevoir.
EVENEMENTS = ["hardBounce", "blocked", "spam", "invalid", "unsubscribed"]


def appeler(chemin, cle, methode="GET", corps=None):
    req = urllib.request.Request(
        chemin, method=methode,
        data=json.dumps(corps).encode("utf-8") if corps is not None else None,
        headers={"api-key": cle, "accept": "application/json",
                 "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            brut = r.read().decode("utf-8")
            return r.status, (json.loads(brut) if brut.strip() else None)
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")[:300]


def main():
    cle = getpass.getpass("  Clé API Brevo (rien ne s'affiche) : ").strip()
    if not cle:
        print("  ✗ Pas de clé, pas de webhook.")
        sys.exit(1)

    code, liste = appeler(API + "?type=transactional", cle)
    if code == 401:
        print("  ✗ Clé refusée par Brevo. Reprenez-la dans SMTP & API → API Keys.")
        sys.exit(1)

    if code < 400:
        existants = (liste or {}).get("webhooks", [])
    elif "document_not_found" in str(liste):
        # Brevo répond 400 « Webhook record does not exist » quand il n'y en a
        # aucun, au lieu de rendre une liste vide. Ce n'est pas une panne :
        # c'est précisément le cas où l'on vient en créer un.
        existants = []
    else:
        print(f"  ✗ Brevo répond {code} : {liste}")
        sys.exit(1)
    if "--lister" in sys.argv:
        if not existants:
            print("  Aucun webhook transactionnel pour l'instant.")
        for w in existants:
            print(f"  #{w['id']}  {w['url']}\n      {', '.join(w.get('events', []))}")
        return

    if "--supprimer" in sys.argv:
        ident = sys.argv[sys.argv.index("--supprimer") + 1]
        code, rep = appeler(f"{API}/{ident}", cle, "DELETE")
        print(f"  {'✓ supprimé' if code < 300 else '✗ ' + str(rep)}")
        return

    jeton = getpass.getpass("  Jeton partagé, celui posé sur Vercel (rien ne s'affiche) : ").strip()
    if not jeton:
        print("  ✗ Sans jeton, la route refuserait tous les appels.")
        sys.exit(1)

    cible = f"{ADRESSE}?jeton={jeton}"
    deja = next((w for w in existants if w["url"].split("?")[0] == ADRESSE), None)
    charge = {"url": cible, "description": "Rebonds — Le Chai Gourmand",
              "type": "transactional", "events": EVENEMENTS}

    if deja:
        code, rep = appeler(f"{API}/{deja['id']}", cle, "PUT",
                            {k: charge[k] for k in ("url", "description", "events")})
        action = f"mis à jour (#{deja['id']})"
    else:
        code, rep = appeler(API, cle, "POST", charge)
        action = f"créé (#{(rep or {}).get('id', '?')})" if isinstance(rep, dict) else "créé"

    if code >= 400:
        print(f"  ✗ Brevo répond {code} : {rep}")
        sys.exit(1)

    print(f"\n  ✓ Webhook {action}")
    print(f"    {ADRESSE}?jeton=…")
    print(f"    événements : {', '.join(EVENEMENTS)}")
    print("\n  Vérifiez que BREVO_WEBHOOK_JETON porte la même valeur sur Vercel,")
    print("  et que le site a été redéployé depuis.")


if __name__ == "__main__":
    main()
