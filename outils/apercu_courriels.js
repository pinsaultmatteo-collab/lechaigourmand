// Aperçu hors ligne des courriels : « node outils/apercu_courriels.js »
// écrit les modèles dans /tmp/courriels-chai/ pour les regarder dans un
// navigateur avant de brancher Brevo. N'envoie rien, ne touche à rien.

const fs = require("fs");
const path = require("path");
const { SITE, gabarit, lignesFiche, jourFr, ech, LIEUX } = require("../api/_courriel.js");

const sortie = "/tmp/courriels-chai";
fs.mkdirSync(sortie, { recursive: true });

const resa = {
  lieu: "francazal", date: "2026-09-26", heure: "20:00", couverts: 4,
  nom: "Camille Estève", telephone: "06 12 34 56 78", email: "camille@exemple.fr",
  message: "Une table près de la fenêtre si possible, et un anniversaire à fêter !",
};
const ev = {
  titre: "Soirée vigneron : Domaine du Cros", date: "2026-10-09", heure: "19h30",
  lieu: "annexe", reservation: true,
  description: "Philippe Teulier présente ses marcillacs. Cinq cuvées à la dégustation, planche de charcuterie de l'Aveyron et fromages fermiers.",
};

const { courrielConfirmation, courrielAnnulation } = require("../api/statut-reservation.js").gabarits;
const { annonce } = require("../api/annoncer-evenement.js").gabarits;
const { bienvenue } = require("../api/newsletter.js").gabarits;
const { page } = require("../api/desinscription.js").gabarits;

// L'alerte à la maison est construite dans reserver.js ; on la rejoue ici à
// l'identique pour la voir aussi.
const alerte = gabarit({
  titre: "Nouvelle réservation",
  chapeau: `<strong>${LIEUX[resa.lieu].nom}</strong> — ${jourFr(resa.date)} à 20h00`,
  corps: lignesFiche([
    ["Couverts", resa.couverts], ["Nom", resa.nom],
    ["Téléphone", resa.telephone], ["E-mail", resa.email],
  ]) + `<p style="margin:18px 0 0;padding:14px 16px;background:#f6efe2;border-radius:12px;font-size:15px;line-height:1.6">« ${ech(resa.message)} »</p>`,
  bouton: { texte: "Confirmer dans le back-office", lien: SITE + "/admin" },
  pied: "Répondre à ce message écrit directement au client.",
});

const modeles = {
  "1-alerte-maison.html": alerte,
  "2-confirmation-client.html": courrielConfirmation(resa),
  "3-annulation-client.html": courrielAnnulation(resa),
  "4-bienvenue-newsletter.html": bienvenue(SITE + "/desinscription?jeton=exemple"),
  "5-annonce-evenement.html": annonce(ev).replace(/__DESINSCRIPTION__/g, SITE + "/desinscription?jeton=exemple"),
  "6-desinscription.html": page({
    titre: "Se désinscrire", jeton: "exemple", bouton: "Confirmer",
    texte: "Confirmez que <strong>camille@exemple.fr</strong> ne doit plus recevoir les rendez-vous du Chai.",
  }),
};

Object.entries(modeles).forEach(([nom, html]) => {
  fs.writeFileSync(path.join(sortie, nom), html);
  console.log("  ✓", path.join(sortie, nom));
});

fs.writeFileSync(path.join(sortie, "index.html"),
  `<!DOCTYPE html><html lang="fr"><meta charset="utf-8"><title>Courriels — Le Chai Gourmand</title>
   <style>body{font:15px/1.6 system-ui;margin:0;background:#efe6d6}
     h1{font-size:17px;padding:14px 18px;margin:0;background:#1a0f14;color:#f6efe2}
     .g{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));padding:14px}
     figure{margin:0}figcaption{font-size:12px;padding:6px 2px;color:#5c463c}
     iframe{width:100%;height:620px;border:0;border-radius:12px;background:#fff}</style>
   <h1>Les courriels du Chai Gourmand</h1><div class="g">` +
  Object.keys(modeles).map((n) =>
    `<figure><figcaption>${n.replace(/^\d-|\.html$/g, "").replace(/-/g, " ")}</figcaption><iframe src="${n}"></iframe></figure>`).join("") +
  `</div>`);
console.log("\n  Ouvrir : /tmp/courriels-chai/index.html");
