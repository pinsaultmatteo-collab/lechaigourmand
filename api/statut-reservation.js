// Changement de statut d'une réservation depuis le back-office, et courriel
// au client dans la foulée : confirmation ou annulation.
//
// Réservée à quelqu'un de connecté : le navigateur envoie son jeton Supabase
// dans l'en-tête Authorization, qu'on fait vérifier par Supabase lui-même.
//
// L'envoi n'a lieu qu'une fois par statut (colonnes confirmation_envoyee /
// annulation_envoyee) : rebasculer deux fois le menu ne renvoie rien.

const { SITE, TELEPHONE, LIEUX, base, estConnecte, gabarit, lignesFiche,
        jourFr, envoyer } = require("./_courriel.js");

const STATUTS = ["nouvelle", "confirmee", "annulee"];

// La base doit avoir reçu supabase/migration-courriels.sql. Tant que ce n'est
// pas fait, PostgREST se plaint d'une colonne ou d'une table qui n'existe pas :
// autant le dire en clair plutôt que de laisser une erreur cryptique.
const MANQUE = /PGRST204|42703|42P01|abonnes|confirmation_envoyee|annulation_envoyee|annonce_envoyee|does not exist/i;
const expliquer = (err) =>
  MANQUE.test(err.message)
    ? "La base n'est pas à jour : lancez supabase/migration-courriels.sql dans Supabase (SQL Editor)."
    : err.message;


function fiche(r) {
  const lieu = LIEUX[r.lieu] || { nom: r.lieu, adresse: "" };
  return lignesFiche([
    ["Établissement", lieu.nom],
    ["Adresse", lieu.adresse],
    ["Date", jourFr(r.date)],
    ["Heure", String(r.heure).slice(0, 5).replace(":", "h")],
    ["Couverts", r.couverts],
    ["Au nom de", r.nom],
  ]);
}

function courrielConfirmation(r) {
  return gabarit({
    titre: "Votre table est réservée",
    chapeau: `Bonjour ${r.nom.split(" ")[0]}, c'est confirmé — nous vous attendons.`,
    corps: fiche(r) + `<p style="margin:20px 0 0;font-size:15px;line-height:1.6;color:#5c463c">
      Un empêchement, un retard, un couvert de plus ? Un mot au
      <a href="tel:+33685362265" style="color:#7c2140">${TELEPHONE}</a> et c'est réglé.</p>`,
    bouton: { texte: "Voir l'adresse", lien: SITE + "/nos-adresses" },
  });
}

function courrielAnnulation(r) {
  return gabarit({
    titre: "Réservation annulée",
    chapeau: `Bonjour ${r.nom.split(" ")[0]}, votre réservation a bien été annulée.`,
    corps: fiche(r) + `<p style="margin:20px 0 0;font-size:15px;line-height:1.6;color:#5c463c">
      Si l'annulation vient de nous, pardon pour le contretemps — appelez-nous au
      <a href="tel:+33685362265" style="color:#7c2140">${TELEPHONE}</a>, nous trouverons
      une autre date avec plaisir.</p>`,
    bouton: { texte: "Réserver une autre fois", lien: SITE + "/nos-adresses" },
  });
}

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") return res.status(405).json({ erreur: "POST attendu" });
  if (!(await estConnecte(req.headers))) return res.status(401).json({ erreur: "Connectez-vous." });

  let corps = req.body;
  if (typeof corps === "string") { try { corps = JSON.parse(corps); } catch { corps = {}; } }
  corps = corps || {};
  const id = String(corps.id || "").slice(0, 40);
  const statut = String(corps.statut || "");
  if (!/^[0-9a-f-]{36}$/i.test(id)) return res.status(400).json({ erreur: "Réservation inconnue." });
  if (!STATUTS.includes(statut)) return res.status(400).json({ erreur: "Statut inattendu." });

  try {
    const trouvees = await base("reservations?select=*&id=eq." + id);
    if (!trouvees.length) return res.status(404).json({ erreur: "Réservation introuvable." });
    const r = trouvees[0];

    const maj = { statut };
    // On repart à zéro sur l'autre courriel : une réservation annulée puis
    // reconfirmée doit pouvoir prévenir le client à nouveau.
    if (statut === "confirmee") maj.annulation_envoyee = null;
    if (statut === "annulee") maj.confirmation_envoyee = null;

    let courriel = "aucun";
    const dejaEnvoye = statut === "confirmee" ? r.confirmation_envoyee
                     : statut === "annulee"   ? r.annulation_envoyee : true;

    if (statut !== "nouvelle" && !dejaEnvoye) {
      if (!r.email) {
        courriel = "sans adresse";
      } else {
        const envoi = await envoyer({
          a: r.email,
          sujet: statut === "confirmee"
            ? `Réservation confirmée — ${jourFr(r.date)} à ${String(r.heure).slice(0, 5).replace(":", "h")}`
            : `Réservation annulée — ${jourFr(r.date)}`,
          html: statut === "confirmee" ? courrielConfirmation(r) : courrielAnnulation(r),
        });
        if (envoi.envoye) {
          courriel = "envoye";
          maj[statut === "confirmee" ? "confirmation_envoyee" : "annulation_envoyee"] = new Date().toISOString();
        } else {
          courriel = "non configure";
        }
      }
    } else if (dejaEnvoye && statut !== "nouvelle") {
      courriel = "deja envoye";
    }

    await base("reservations?id=eq." + id, {
      method: "PATCH", headers: { Prefer: "return=minimal" }, body: JSON.stringify(maj),
    });
    return res.status(200).json({ ok: true, courriel });
  } catch (err) {
    console.error(err);
    return res.status(502).json({ erreur: "Le statut n'a pas pu être enregistré. " + expliquer(err) });
  }
};

module.exports.gabarits = { courrielConfirmation, courrielAnnulation };   // aperçu hors ligne
