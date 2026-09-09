// Réception des réservations du site.
//
// Le formulaire poste ici ; on vérifie, on enregistre dans Supabase avec la
// clé de service (jamais exposée au navigateur), et si une clé Brevo est
// présente on prévient la maison par courriel. Aucune dépendance : le
// runtime Node de Vercel fournit fetch.
//
// Variables d'environnement à renseigner sur Vercel :
//   SUPABASE_URL          https://xxxx.supabase.co
//   SUPABASE_SERVICE_KEY  clé « service_role » (Project settings → API)
//   BREVO_API_KEY         facultatif : envoie un courriel à chaque réservation
//   COURRIEL_EXPEDITEUR   adresse d'envoi, validée chez Brevo
//   COURRIEL_MAISON       adresse qui reçoit l'alerte (à défaut RESERVATION_EMAIL)

const { SITE, ech, jourFr, gabarit, lignesFiche, envoyer } = require("./_courriel.js");

const LIEUX = {
  francazal: { nom: "Le Chai — Francazal", horaires: { 2: [10, 21], 3: [10, 21], 4: [10, 23], 5: [10, 23], 6: [10, 23] } },
  annexe:    { nom: "L'Annexe — Cézerou",  horaires: { 2: [16, 20], 3: [16, 20], 4: [16, 22], 5: [16, 22], 6: [10, 22] } },
};

function propre(v, max) {
  return String(v == null ? "" : v).replace(/\s+/g, " ").trim().slice(0, max);
}

// Renvoie un message d'erreur, ou null si tout est bon.
function verifier(d) {
  if (d.site_web) return "spam";                              // pot de miel : un humain ne le remplit pas
  if (!LIEUX[d.lieu]) return "Choisissez un établissement.";
  if (!/^\d{4}-\d{2}-\d{2}$/.test(d.date)) return "La date est incomplète.";
  const [a, m, j] = d.date.split("-").map(Number);
  const date = new Date(a, m - 1, j);
  const aujourdHui = new Date(); aujourdHui.setHours(0, 0, 0, 0);
  if (isNaN(date) || date < aujourdHui) return "La date est déjà passée.";
  const plage = LIEUX[d.lieu].horaires[date.getDay()];
  if (!plage) return "L'établissement est fermé ce jour-là.";
  if (!/^\d{2}:\d{2}$/.test(d.heure)) return "L'heure est incomplète.";
  const h = Number(d.heure.slice(0, 2)) + Number(d.heure.slice(3)) / 60;
  if (h < plage[0] || h > plage[1] - 0.5) return "Cette heure est en dehors des horaires d'ouverture.";
  const couverts = Number(d.couverts);
  if (!Number.isInteger(couverts) || couverts < 1 || couverts > 40) return "Le nombre de couverts n'est pas valide.";
  if (d.nom.length < 2) return "Indiquez un nom.";
  if (!/^\+?[\d\s.()-]{9,20}$/.test(d.telephone)) return "Le numéro de téléphone semble incorrect.";
  if (d.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(d.email)) return "L'adresse e-mail semble incorrecte.";
  return null;
}

async function enregistrer(d) {
  const r = await fetch(process.env.SUPABASE_URL + "/rest/v1/reservations", {
    method: "POST",
    headers: {
      apikey: process.env.SUPABASE_SERVICE_KEY,
      Authorization: "Bearer " + process.env.SUPABASE_SERVICE_KEY,
      "Content-Type": "application/json",
      Prefer: "return=representation",
    },
    body: JSON.stringify({
      lieu: d.lieu, date: d.date, heure: d.heure, couverts: Number(d.couverts),
      nom: d.nom, telephone: d.telephone, email: d.email || null, message: d.message || null,
    }),
  });
  if (!r.ok) throw new Error("supabase " + r.status + " " + (await r.text()).slice(0, 200));
  return (await r.json())[0];
}

// Alerte à la maison. Confort, jamais bloquant : si Brevo répond mal, la
// réservation est déjà enregistrée et visible dans le back-office.
async function prevenir(d) {
  const heure = d.heure.replace(":", "h");
  const html = gabarit({
    titre: "Nouvelle réservation",
    chapeau: `<strong>${LIEUX[d.lieu].nom}</strong> — ${jourFr(d.date)} à ${heure}`,
    corps:
      lignesFiche([
        ["Couverts", d.couverts],
        ["Nom", d.nom],
        ["Téléphone", d.telephone],
        ["E-mail", d.email || "— non communiqué"],
      ]) +
      (d.message
        ? `<p style="margin:18px 0 0;padding:14px 16px;background:#f6efe2;border-radius:12px;font-size:15px;line-height:1.6">« ${ech(d.message)} »</p>`
        : ""),
    bouton: { texte: "Confirmer dans le back-office", lien: SITE + "/admin" },
    pied: d.email
      ? "Répondre à ce message écrit directement au client."
      : "Le client n'a pas laissé d'adresse : rappelez-le au téléphone.",
  });
  const [a, m, j] = d.date.split("-");
  await envoyer({
    a: process.env.COURRIEL_MAISON || process.env.RESERVATION_EMAIL,
    sujet: `Réservation ${j}/${m} ${heure} — ${d.nom} (${d.couverts} couv.)`,
    html,
    repondreA: d.email || undefined,
  }).catch((err) => console.error("alerte réservation non envoyée", err));
}

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") return res.status(405).json({ erreur: "POST attendu" });
  if (!process.env.SUPABASE_URL || !process.env.SUPABASE_SERVICE_KEY) {
    return res.status(503).json({ erreur: "Le module de réservation n'est pas encore configuré." });
  }
  let corps = req.body;
  if (typeof corps === "string") { try { corps = JSON.parse(corps); } catch { corps = {}; } }
  corps = corps || {};
  const d = {
    site_web: propre(corps.site_web, 50),
    lieu: propre(corps.lieu, 20), date: propre(corps.date, 10), heure: propre(corps.heure, 5),
    couverts: propre(corps.couverts, 3), nom: propre(corps.nom, 80),
    telephone: propre(corps.telephone, 20), email: propre(corps.email, 120).toLowerCase(),
    message: propre(corps.message, 600),
  };
  const probleme = verifier(d);
  if (probleme === "spam") return res.status(200).json({ ok: true });     // on ne renseigne pas les robots
  if (probleme) return res.status(400).json({ erreur: probleme });
  try {
    const ligne = await enregistrer(d);
    if (process.env.COURRIEL_MAISON || process.env.RESERVATION_EMAIL) await prevenir(d);
    return res.status(201).json({ ok: true, id: ligne.id });
  } catch (err) {
    console.error(err);
    return res.status(502).json({ erreur: "La réservation n'a pas pu être enregistrée. Appelez-nous au 06 85 36 22 65." });
  }
};

module.exports.verifier = verifier;    // pour les tests
