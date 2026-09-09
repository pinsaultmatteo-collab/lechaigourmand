// Désinscription de la lettre d'information — obligation légale, sans compte
// ni mot de passe : le jeton contenu dans le lien suffit.
//
// GET  → une page qui demande confirmation. Les antivirus des messageries
//        visitent les liens des courriels ; sans ce clic, ils désinscriraient
//        les gens à leur place.
// POST → la désinscription elle-même.

const { SITE, base, ech } = require("./_courriel.js");

function page({ titre, texte, jeton, bouton }) {
  return `<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>${ech(titre)} — Le Chai Gourmand</title>
<style>
  :root{color-scheme:light}
  body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;
       background:#f6efe2;color:#33241f;
       font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}
  .carte{max-width:460px;width:100%;background:#fdf9f0;border-radius:20px;padding:34px 30px;
         box-shadow:0 18px 40px -24px rgba(51,36,31,.4);text-align:center}
  .marque{color:#c9a876;font-size:11px;letter-spacing:3px;text-transform:uppercase}
  h1{font-size:23px;margin:10px 0 14px;font-weight:600}
  p{margin:0 0 18px;line-height:1.6;color:#5c463c}
  button,a.lien{display:inline-block;border:0;cursor:pointer;font:inherit;font-size:13px;
    letter-spacing:1.6px;text-transform:uppercase;padding:13px 26px;border-radius:99px;
    background:#7c2140;color:#f6efe2;text-decoration:none}
  a.retour{display:block;margin-top:18px;color:#7a6355;font-size:13px}
</style></head><body>
<main class="carte">
  <div class="marque">Le Chai Gourmand</div>
  <h1>${ech(titre)}</h1>
  <p>${texte}</p>
  ${bouton ? `<form method="post" action="/desinscription">
      <input type="hidden" name="jeton" value="${ech(jeton)}">
      <button type="submit">${ech(bouton)}</button>
    </form>` : ""}
  <a class="retour" href="${SITE}/">Retour au site</a>
</main></body></html>`;
}

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("Content-Type", "text/html; charset=utf-8");

  let jeton = "";
  if (req.method === "GET") {
    jeton = String((req.query && req.query.jeton) || "");
  } else if (req.method === "POST") {
    let corps = req.body;
    if (typeof corps === "string") {
      try { corps = JSON.parse(corps); }
      catch { corps = Object.fromEntries(new URLSearchParams(corps)); }
    }
    jeton = String((corps && corps.jeton) || "");
  } else {
    return res.status(405).send(page({ titre: "Méthode inattendue", texte: "Revenez au site." }));
  }

  jeton = jeton.replace(/[^a-f0-9]/gi, "").slice(0, 64);
  if (!jeton) {
    return res.status(400).send(page({
      titre: "Lien incomplet",
      texte: "Ce lien de désinscription n'est pas valide. Écrivez-nous et nous nous en chargeons.",
    }));
  }

  try {
    const trouves = await base("abonnes?select=id,email,statut&jeton=eq." + jeton);
    if (!trouves.length) {
      return res.status(404).send(page({
        titre: "Adresse inconnue",
        texte: "Cette adresse ne figure plus dans notre liste : vous ne recevrez rien de notre part.",
      }));
    }
    const abonne = trouves[0];

    if (req.method === "GET") {
      if (abonne.statut !== "actif") {
        return res.status(200).send(page({
          titre: "C'est déjà fait",
          texte: `<strong>${ech(abonne.email)}</strong> ne reçoit plus nos rendez-vous.`,
        }));
      }
      return res.status(200).send(page({
        titre: "Se désinscrire",
        texte: `Confirmez que <strong>${ech(abonne.email)}</strong> ne doit plus recevoir les rendez-vous du Chai.`,
        jeton,
        bouton: "Confirmer",
      }));
    }

    await base("abonnes?id=eq." + abonne.id, {
      method: "PATCH",
      headers: { Prefer: "return=minimal" },
      body: JSON.stringify({ statut: "desinscrit", desinscrit_le: new Date().toISOString() }),
    });
    return res.status(200).send(page({
      titre: "C'est fait",
      texte: `<strong>${ech(abonne.email)}</strong> ne recevra plus nos courriels. Vous restez évidemment le bienvenu au comptoir.`,
    }));
  } catch (err) {
    console.error(err);
    return res.status(502).send(page({
      titre: "Souci technique",
      texte: "La désinscription n'a pas pu être enregistrée. Réessayez dans un instant.",
    }));
  }
};

module.exports.gabarits = { page };   // aperçu hors ligne
