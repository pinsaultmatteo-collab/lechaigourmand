// Webhook Brevo : ce qui n'est pas arrivé à destination.
//
// Brevo appelle cette route à chaque incident d'envoi. Deux réactions, selon
// ce que portait le message (voir les étiquettes posées à l'envoi) :
//
// · une confirmation de réservation qui rebondit → Adrien reçoit une alerte
//   avec le numéro de téléphone du client. C'est tout l'objet de la route :
//   une table confirmée dont le client ne sait rien est un couvert perdu ;
// · une adresse de la lettre d'information qui rebondit → elle sort de la
//   liste. Continuer d'arroser une adresse morte abîme la réputation de
//   l'expéditeur, et ce sont les messages aux adresses valides qui finissent
//   en indésirables.
//
// Variable d'environnement :
//   BREVO_WEBHOOK_JETON   un secret partagé, que Brevo renvoie à chaque appel
//
// La route est publique : sans ce jeton, n'importe qui pourrait déclarer
// morte l'adresse de n'importe qui.

const { SITE, TELEPHONE, LIEUX, base, gabarit, lignesFiche, jourFr, ech,
        envoyer } = require("./_courriel.js");

// Brevo écrit ses événements de deux façons selon l'endroit : « hardBounce »
// quand on s'abonne, « hard_bounce » dans la charge reçue. On aplatit les deux
// avant de comparer, plutôt que de parier sur l'orthographe du jour.
const aplatir = (e) => String(e || "").toLowerCase().replace(/[^a-z]/g, "");

// Les pannes définitives. Un retard — soft bounce, deferred — n'en est pas
// une : Brevo réessaie tout seul, et prévenir à chaque fois serait du bruit.
const PERDUS = new Set(["hardbounce", "blocked", "invalidemail", "invalid", "spam", "error"]
  .map(aplatir));

const RESERVATION = new Set(["reservation-confirmation", "reservation-annulation"]);
const LETTRE = new Set(["newsletter-bienvenue", "newsletter-annonce"]);

function autorise(req) {
  const attendu = process.env.BREVO_WEBHOOK_JETON;
  if (!attendu) return null;                       // pas configuré : on refuse
  const recu = String(req.headers["x-chai-jeton"] || (req.query && req.query.jeton) || "");
  // comparaison de longueur constante : on ne laisse pas deviner le jeton
  if (recu.length !== attendu.length) return false;
  let ecart = 0;
  for (let i = 0; i < attendu.length; i++) ecart |= recu.charCodeAt(i) ^ attendu.charCodeAt(i);
  return ecart === 0;
}

function alerte(r, motif, evenement) {
  const lieu = LIEUX[r.lieu] || { nom: r.lieu, adresse: "" };
  return gabarit({
    titre: "Un client n’a pas reçu sa confirmation",
    chapeau: `Le message envoyé à <strong>${ech(r.email)}</strong> n’est pas arrivé. ` +
             "Un appel s’impose : le client ignore que sa table est confirmée.",
    corps: lignesFiche([
      ["Téléphone", r.telephone],
      ["Au nom de", r.nom],
      ["Établissement", lieu.nom],
      ["Date", jourFr(r.date)],
      ["Heure", String(r.heure).slice(0, 5).replace(":", "h")],
      ["Couverts", r.couverts],
      ["Motif du rejet", motif || evenement],
    ]),
    bouton: { texte: "Appeler le client", lien: "tel:" + String(r.telephone).replace(/[^\d+]/g, "") },
    pied: `Signalé par Brevo (${ech(evenement)}).<br>` +
          `<a href="${SITE}/admin" style="color:#7c2140;text-decoration:none">Ouvrir le back-office</a>`,
  });
}

async function traiter(e) {
  const evenement = String(e.event || "");
  const genre = aplatir(evenement);
  const email = String(e.email || "").trim().toLowerCase();
  const motif = String(e.reason || e.message || "").slice(0, 300);
  const etiquettes = [].concat(e.tags || e.tag || []).map(String);
  if (!email) return "sans adresse";

  // Une désinscription faite depuis le pied de page de Brevo doit se refléter
  // chez nous, sans quoi la personne recevrait la prochaine annonce.
  if (genre === "unsubscribed") {
    await base("abonnes?email=eq." + encodeURIComponent(email), {
      method: "PATCH", headers: { Prefer: "return=minimal" },
      body: JSON.stringify({ statut: "desinscrit", desinscrit_le: new Date().toISOString() }),
    });
    return "désinscrit";
  }

  if (!PERDUS.has(genre)) return "ignoré (" + evenement + ")";

  const versLettre = etiquettes.some((t) => LETTRE.has(t));
  const versReservation = etiquettes.some((t) => RESERVATION.has(t));

  let fait = [];

  // ---------- la lettre d'information ----------
  if (versLettre || !etiquettes.length) {
    const connus = await base("abonnes?select=id,statut&email=eq." + encodeURIComponent(email));
    if (connus.length && connus[0].statut === "actif") {
      await base("abonnes?id=eq." + connus[0].id, {
        method: "PATCH", headers: { Prefer: "return=minimal" },
        body: JSON.stringify({ statut: "rebond", rebond_le: new Date().toISOString(),
                               rebond_motif: motif || evenement }),
      });
      fait.push("abonné retiré");
    }
  }

  // ---------- les réservations ----------
  if (versReservation || !etiquettes.length) {
    // La plus récente à venir : c'est celle dont la confirmation vient de partir.
    const jour = new Date().toISOString().slice(0, 10);
    const trouvees = await base(
      "reservations?select=*&email=eq." + encodeURIComponent(email) +
      "&date=gte." + jour + "&order=date.asc&limit=1");
    if (trouvees.length) {
      const r = trouvees[0];
      await base("reservations?id=eq." + r.id, {
        method: "PATCH", headers: { Prefer: "return=minimal" },
        body: JSON.stringify({ courriel_rebond: new Date().toISOString(),
                               courriel_rebond_motif: motif || evenement }),
      });
      // L'alerte ne part qu'une fois par réservation.
      if (!r.courriel_rebond) {
        await envoyer({
          a: process.env.COURRIEL_MAISON || process.env.RESERVATION_EMAIL,
          sujet: `⚠ Confirmation non reçue — ${r.nom} le ${jourFr(r.date)}`,
          html: alerte(r, motif, evenement),
          etiquette: "alerte-rebond",
        }).catch((err) => console.error("alerte rebond non envoyée", err));
        fait.push("maison prévenue");
      } else {
        fait.push("déjà signalé");
      }
    }
  }

  return fait.length ? fait.join(" + ") : "rien à faire";
}

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") return res.status(405).json({ erreur: "POST attendu" });

  const droit = autorise(req);
  if (droit === null) return res.status(503).json({ erreur: "Webhook non configuré." });
  if (!droit) return res.status(401).json({ erreur: "Jeton invalide." });

  let corps = req.body;
  if (typeof corps === "string") { try { corps = JSON.parse(corps); } catch { corps = null; } }
  const evenements = Array.isArray(corps) ? corps : corps ? [corps] : [];
  if (!evenements.length) return res.status(400).json({ erreur: "Corps vide." });

  const bilan = [];
  for (const e of evenements.slice(0, 50)) {
    try {
      bilan.push(await traiter(e));
    } catch (err) {
      console.error("rebond non traité", err);
      bilan.push("erreur");
    }
  }
  // Toujours 200 quand on a lu le lot : un échec ferait réessayer Brevo en
  // boucle, et il finirait par couper le webhook.
  return res.status(200).json({ ok: true, traites: bilan });
};

module.exports.gabarits = { alerte };   // aperçu hors ligne
