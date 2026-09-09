// Annonce d'un événement aux abonnés de la lettre d'information.
//
// Appelée depuis le back-office, par quelqu'un de connecté. Chaque abonné
// reçoit un courriel individuel (messageVersions de Brevo) : personne ne voit
// l'adresse des autres, et chacun a son propre lien de désinscription.
//
// Un événement en brouillon n'est jamais annoncé : on n'invite pas à une
// soirée qui n'est pas encore sur le site.

const { SITE, LIEUX, base, estConnecte, gabarit, lignesFiche, jourFr, ech,
        envoyerEnNombre } = require("./_courriel.js");


// La base doit avoir reçu supabase/migration-courriels.sql. Tant que ce n'est
// pas fait, PostgREST se plaint d'une colonne ou d'une table qui n'existe pas :
// autant le dire en clair plutôt que de laisser une erreur cryptique.
const MANQUE = /PGRST204|42703|42P01|abonnes|confirmation_envoyee|annulation_envoyee|annonce_envoyee|does not exist/i;
const expliquer = (err) =>
  MANQUE.test(err.message)
    ? "La base n'est pas à jour : lancez supabase/migration-courriels.sql dans Supabase (SQL Editor)."
    : err.message;

function annonce(ev) {
  const lieu = LIEUX[ev.lieu] || { nom: ev.lieu, adresse: "" };
  return gabarit({
    titre: "Un rendez-vous au Chai",
    chapeau: `<strong>${ech(ev.titre)}</strong>`,
    corps:
      lignesFiche([
        ["Quand", jourFr(ev.date) + (ev.heure ? " à " + String(ev.heure).replace(":", "h") : "")],
        ["Où", lieu.nom],
        ["Adresse", lieu.adresse],
        ["Réservation", ev.reservation ? "conseillée" : "libre, dans la limite des places"],
      ]) +
      (ev.description
        ? `<p style="margin:18px 0 0;font-size:15px;line-height:1.6;color:#5c463c">${ech(ev.description)}</p>`
        : ""),
    bouton: { texte: ev.reservation ? "Réserver ma place" : "Voir l'agenda", lien: SITE + "/agenda" },
    pied: `Le Chai Gourmand — Cugnaux, près de Toulouse<br>
      <a href="tel:+33685362265" style="color:#7c2140;text-decoration:none">06 85 36 22 65</a> ·
      <a href="${SITE}" style="color:#7c2140;text-decoration:none">chai-gourmand.fr</a><br>
      <a href="__DESINSCRIPTION__" style="color:#7a6355">Se désinscrire</a>`,
  });
}

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") return res.status(405).json({ erreur: "POST attendu" });
  if (!(await estConnecte(req.headers))) return res.status(401).json({ erreur: "Connectez-vous." });

  let corps = req.body;
  if (typeof corps === "string") { try { corps = JSON.parse(corps); } catch { corps = {}; } }
  corps = corps || {};
  const id = String(corps.id || "");
  const forcer = corps.forcer === true;              // renvoyer malgré un premier envoi
  if (!/^[0-9a-f-]{36}$/i.test(id)) return res.status(400).json({ erreur: "Événement inconnu." });

  try {
    const trouves = await base("evenements?select=*&id=eq." + id);
    if (!trouves.length) return res.status(404).json({ erreur: "Événement introuvable." });
    const ev = trouves[0];

    if (ev.statut !== "publie") {
      return res.status(400).json({ erreur: "Publiez l'événement avant de l'annoncer." });
    }
    if (ev.annonce_envoyee && !forcer) {
      return res.status(409).json({
        erreur: "Déjà annoncé le " + new Date(ev.annonce_envoyee).toLocaleDateString("fr-FR") +
                " à " + (ev.annonce_nombre || 0) + " abonné(s).",
        deja: true,
      });
    }

    const abonnes = await base("abonnes?select=email,jeton&statut=eq.actif&limit=5000");
    if (!abonnes.length) return res.status(200).json({ ok: true, envoyes: 0, message: "Aucun abonné pour l'instant." });

    const { envoyes, raison } = await envoyerEnNombre({
      destinataires: abonnes,
      sujet: ev.titre + " — " + jourFr(ev.date),
      html: annonce(ev),
      lienDesinscription: (d) => SITE + "/desinscription?jeton=" + d.jeton,
    });
    if (!envoyes) return res.status(503).json({ erreur: raison || "Envoi impossible." });

    await base("evenements?id=eq." + id, {
      method: "PATCH",
      headers: { Prefer: "return=minimal" },
      body: JSON.stringify({ annonce_envoyee: new Date().toISOString(), annonce_nombre: envoyes }),
    });
    return res.status(200).json({ ok: true, envoyes });
  } catch (err) {
    console.error(err);
    return res.status(502).json({ erreur: "L'annonce n'est pas partie. " + expliquer(err) });
  }
};

module.exports.gabarits = { annonce };   // aperçu hors ligne
