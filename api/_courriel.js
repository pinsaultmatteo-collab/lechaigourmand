// Envoi des courriels, et accès à la base côté serveur.
// Le fichier commence par « _ » : Vercel ne l'expose donc pas comme route.
//
// Variables d'environnement (Vercel → Settings → Environment Variables) :
//   SUPABASE_URL, SUPABASE_SERVICE_KEY   déjà en place
//   BREVO_API_KEY                        clé API Brevo (v3)
//   COURRIEL_EXPEDITEUR                  adresse d'envoi, validée chez Brevo
//   COURRIEL_MAISON                      adresse qui reçoit les alertes (Adrien)

const SITE = "https://chai-gourmand.fr";
const MAISON = "Le Chai Gourmand";
const TELEPHONE = "06 85 36 22 65";

const LIEUX = {
  francazal: { nom: "Le Chai — Francazal", adresse: "9 rue Alfred Sauvy, 31270 Cugnaux" },
  annexe: { nom: "L'Annexe — Cézerou", adresse: "14 rue de Cezerou, 31270 Cugnaux" },
};

const ech = (t) =>
  String(t == null ? "" : t).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const jourFr = (iso) => {
  const [a, m, j] = iso.split("-");
  const mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
                "août", "septembre", "octobre", "novembre", "décembre"];
  return `${Number(j)} ${mois[Number(m) - 1]} ${a}`;
};

// ---------- base ----------
async function base(chemin, options = {}) {
  const r = await fetch(process.env.SUPABASE_URL + "/rest/v1/" + chemin, {
    ...options,
    headers: {
      apikey: process.env.SUPABASE_SERVICE_KEY,
      Authorization: "Bearer " + process.env.SUPABASE_SERVICE_KEY,
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!r.ok) throw new Error("base " + r.status + " " + (await r.text()).slice(0, 200));
  return r.status === 204 ? null : r.json();
}

// ---------- qui appelle ? ----------
// Les routes du back-office n'acceptent que quelqu'un de connecté.
async function estConnecte(entetes) {
  const jeton = String(entetes.authorization || "").replace(/^Bearer\s+/i, "");
  if (!jeton) return false;
  try {
    const r = await fetch(process.env.SUPABASE_URL + "/auth/v1/user", {
      headers: { apikey: process.env.SUPABASE_SERVICE_KEY, Authorization: "Bearer " + jeton },
    });
    if (!r.ok) return false;
    const u = await r.json();
    return Boolean(u && u.id);
  } catch {
    return false;
  }
}

// ---------- gabarit ----------
// Un courriel sobre, aux couleurs de la maison, lisible partout.
function gabarit({ titre, chapeau, corps, bouton, pied }) {
  return `<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f6efe2;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:#33241f">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f6efe2;padding:28px 12px">
<tr><td align="center">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#fdf9f0;border-radius:18px;overflow:hidden;box-shadow:0 12px 30px -18px rgba(51,36,31,.35)">
    <tr><td style="background:#1a0f14;padding:22px 28px">
      <div style="color:#c9a876;font-size:11px;letter-spacing:3px;text-transform:uppercase">${ech(MAISON)}</div>
      <div style="color:#f6efe2;font-size:21px;margin-top:5px">${ech(titre)}</div>
    </td></tr>
    <tr><td style="padding:26px 28px 8px">
      ${chapeau ? `<p style="margin:0 0 16px;font-size:16px;line-height:1.55">${chapeau}</p>` : ""}
      ${corps}
      ${bouton ? `<p style="margin:24px 0 8px"><a href="${bouton.lien}" style="display:inline-block;background:#7c2140;color:#f6efe2;text-decoration:none;padding:13px 26px;border-radius:99px;font-size:13px;letter-spacing:1.6px;text-transform:uppercase">${ech(bouton.texte)}</a></p>` : ""}
    </td></tr>
    <tr><td style="padding:18px 28px 26px;border-top:1px solid rgba(122,99,85,.2);color:#7a6355;font-size:13px;line-height:1.6">
      ${pied || `${ech(MAISON)} — Cugnaux, près de Toulouse<br>
        <a href="tel:+33685362265" style="color:#7c2140;text-decoration:none">${TELEPHONE}</a> ·
        <a href="${SITE}" style="color:#7c2140;text-decoration:none">chai-gourmand.fr</a>`}
    </td></tr>
  </table>
  <div style="max-width:560px;margin-top:14px;color:#7a6355;font-size:11px;line-height:1.5">
    L'abus d'alcool est dangereux pour la santé. À consommer avec modération.
  </div>
</td></tr></table></body></html>`;
}

const lignesFiche = (paires) =>
  `<table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;font-size:15px">` +
  paires.filter(([, v]) => v).map(([k, v]) =>
    `<tr><td style="padding:7px 0;color:#7a6355;width:38%;vertical-align:top">${ech(k)}</td>
         <td style="padding:7px 0;font-weight:600">${ech(v)}</td></tr>`).join("") +
  `</table>`;

// ---------- envoi ----------
function config() {
  return {
    cle: process.env.BREVO_API_KEY,
    expediteur: process.env.COURRIEL_EXPEDITEUR || process.env.RESERVATION_EMAIL,
    maison: process.env.COURRIEL_MAISON || process.env.RESERVATION_EMAIL,
  };
}

// Rend null si Brevo n'est pas configuré : le site continue de fonctionner,
// simplement sans courriel — jamais d'échec bloquant pour le visiteur.
async function envoyer({ a, sujet, html, repondreA }) {
  const c = config();
  if (!c.cle || !c.expediteur) return { envoye: false, raison: "Brevo non configuré" };
  const r = await fetch("https://api.brevo.com/v3/smtp/email", {
    method: "POST",
    headers: { "api-key": c.cle, "Content-Type": "application/json", accept: "application/json" },
    body: JSON.stringify({
      sender: { name: MAISON, email: c.expediteur },
      to: [{ email: a }],
      // Par défaut on répond à l'adresse de la maison, jamais à la boîte
      // personnelle : elle est redirigée vers elle de toute façon.
      replyTo: repondreA ? { email: repondreA } : { email: c.expediteur },
      subject: sujet,
      htmlContent: html,
    }),
  });
  if (!r.ok) throw new Error("brevo " + r.status + " " + (await r.text()).slice(0, 200));
  return { envoye: true };
}

// Un envoi individuel par destinataire : personne ne voit l'adresse des
// autres, et chacun reçoit son propre lien de désinscription.
//
// Brevo sait faire ça en une requête (« messageVersions »), ce qui tient
// largement dans le temps d'exécution d'une fonction Vercel. Si l'API refuse
// ce format, on retombe sur des envois un par un, par petits paquets.
async function envoyerEnNombre({ destinataires, sujet, html, lienDesinscription }) {
  const c = config();
  if (!c.cle || !c.expediteur) return { envoyes: 0, raison: "Brevo non configuré" };
  const entetes = { "api-key": c.cle, "Content-Type": "application/json", accept: "application/json" };
  const expediteur = { name: MAISON, email: c.expediteur };
  const pourUn = (d) => html.replace(/__DESINSCRIPTION__/g, lienDesinscription(d));

  async function unParUn(lot) {
    // huit en parallèle : assez rapide, assez doux pour l'API
    for (let i = 0; i < lot.length; i += 8) {
      await Promise.all(lot.slice(i, i + 8).map((d) =>
        fetch("https://api.brevo.com/v3/smtp/email", {
          method: "POST", headers: entetes,
          body: JSON.stringify({ sender: expediteur, to: [{ email: d.email }], subject: sujet, htmlContent: pourUn(d) }),
        }).then((r) => { if (!r.ok) throw new Error("brevo " + r.status); })
      ));
    }
  }

  let envoyes = 0;
  for (let i = 0; i < destinataires.length; i += 50) {
    const lot = destinataires.slice(i, i + 50);
    const r = await fetch("https://api.brevo.com/v3/smtp/email", {
      method: "POST", headers: entetes,
      body: JSON.stringify({
        sender: expediteur,
        subject: sujet,
        htmlContent: html,
        messageVersions: lot.map((d) => ({ to: [{ email: d.email }], htmlContent: pourUn(d) })),
      }),
    });
    if (!r.ok) {
      const detail = (await r.text()).slice(0, 200);
      if (r.status >= 500) throw new Error("brevo " + r.status + " " + detail);
      await unParUn(lot);                       // format refusé : on fait à la main
    }
    envoyes += lot.length;
  }
  return { envoyes };
}

module.exports = { SITE, MAISON, TELEPHONE, LIEUX, ech, jourFr, base, estConnecte,
                   gabarit, lignesFiche, envoyer, envoyerEnNombre };
