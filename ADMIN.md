# Back-office, réservations et programmation — mise en service

Le site reste statique. Trois choses viennent s'y greffer :

| Pièce | Rôle | Où |
| --- | --- | --- |
| **Supabase** (gratuit) | base de données + comptes de l'équipe + photos | supabase.com |
| **`/api/reserver`** | reçoit les réservations du site, les enregistre, prévient par courriel | fonction Vercel, déjà dans le dépôt |
| **`/admin`** | réservations, événements, produits | page du site, déjà dans le dépôt |

Compter **vingt minutes**, une seule fois.

## 1. Créer le projet Supabase

1. supabase.com → *New project*. Région **West EU (Paris)**, mot de passe base : gardez-le, il ne servira plus.
2. Menu **SQL Editor** → *New query* → collez tout `supabase/schema.sql` → *Run*.
   ⚠️ **Copiez le fichier en UTF-8**, sinon les accents arrivent abîmés dans la base
   (« à » devient « √† »). En ligne de commande : `LC_ALL=en_US.UTF-8 pbcopy < supabase/schema.sql`.
   Ou ouvrez le fichier dans un éditeur de texte et copiez depuis là.
   Si le mal est fait : `supabase/reparer-accents.sql` corrige les 12 événements sans rien supprimer.
   Ça crée les trois tables, les droits, le rangement des photos, et recopie la programmation de septembre.
3. Menu **Authentication → Sign In / Providers → Email** : décochez **Allow new users to sign up**.
   Sans ça, n'importe qui pourrait se créer un compte depuis l'extérieur et écrire dans la base.
4. Menu **Authentication → Users → Add user** : l'adresse et le mot de passe d'Adrien (et les vôtres).
   Cochez *Auto confirm user*. C'est l'identifiant du back-office.
5. Menu **Project settings → API** : notez trois valeurs.
   - *Project URL* — `https://xxxx.supabase.co`
   - *anon public* — la clé publique
   - *service_role* — la clé secrète. **Jamais dans le code, jamais dans un mail.**

## 2. Brancher le site

- Dans `config.js`, renseignez `supabaseUrl` et `supabaseAnonKey`. Ces deux valeurs sont faites pour être
  vues par le navigateur : la base n'accorde à cette clé que la lecture de ce qui est publié.
- Sur Vercel → *Settings → Environment Variables*, ajoutez :

  | Nom | Valeur |
  | --- | --- |
  | `SUPABASE_URL` | l'URL du projet |
  | `SUPABASE_SERVICE_KEY` | la clé *service_role* |
  | `BREVO_API_KEY` | *facultatif* — une clé Brevo pour recevoir un courriel à chaque réservation |
  | `RESERVATION_EMAIL` | *facultatif* — l'adresse qui reçoit ces courriels (doit être un expéditeur validé chez Brevo) |

- Poussez `config.js` et redéployez. Sans courriel, les réservations restent visibles dans l'onglet
  *Réservations* du back-office, avec une pastille sur le nombre de nouvelles.

## 2 bis. Faire passer le catalogue en base (une seule fois)

Les 254 fiches vivaient dans un fichier du dépôt. Pour qu'Adrien puisse les corriger lui-même :

1. **SQL Editor** → collez `supabase/migration-produits.sql` → *Run* (ajoute six colonnes manquantes).
2. Dans un terminal, à la racine du site :

   ```
   export SUPABASE_SERVICE_KEY='la-cle-service_role'
   python3 outils/importer_produits.py
   ```

   255 fiches partent en base, avec leurs photos et leurs sources. Rejouable sans créer de doublons.
3. Sur Vercel → *Settings → Git → Deploy Hooks* : créez un hook nommé `back-office` sur la branche `main`,
   copiez son adresse, et ajoutez-la en variable d'environnement `VERCEL_DEPLOY_HOOK`.

À partir de là, le site est **régénéré depuis la base à chaque déploiement**. Si Supabase ne répond pas,
le build retombe sur `data/produits.json` plutôt que d'échouer.

## 3. Ce que fait chaque onglet

- **Réservations** — reçues par le formulaire du site. Statut *nouvelle → confirmée / annulée* ; le client
  n'est pas prévenu automatiquement, c'est l'appel qui confirme (le formulaire le dit).
- **Événements** — la programmation de l'agenda et du bandeau d'accueil. *Brouillon* = invisible ;
  *Publier* = en ligne dans la minute. Les passés disparaissent seuls du site. Plus besoin de toucher
  au tableau `PROGRAMMATION` de `site.js` : il ne sert plus que de repli si la base ne répond pas.
- **Produits** — les 254 fiches du catalogue, cherchables par domaine, appellation ou cépage, plus celles
  qu'Adrien ajoute. Modifier une fiche puis cliquer **Publier sur le site** : le catalogue est reconstruit
  en une minute environ. Ce détour existe parce que les fiches sont écrites dans les pages HTML — c'est ce
  qui les rend lisibles par Google. Les événements et les réservations, eux, sont immédiats. La photo est redimensionnée par le navigateur à l'affichage : une prise de face sur fond clair
  suffit. Le catalogue principal, lui, reste généré depuis les fiches PDF (`data/produits.json`).

## Sécurité, en deux lignes

Le navigateur ne connaît que la clé publique, dont les droits sont écrits dans `schema.sql` : lire les
événements et produits publiés, rien d'autre. Écrire demande un compte ; les réservations n'entrent que
par la fonction serveur, qui vérifie chaque champ (jour d'ouverture, horaires, téléphone) et ignore les
robots grâce à un champ piège.
