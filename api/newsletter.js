// Inscription à la lettre d'information.
//
// Publique : le formulaire du site poste ici. On enregistre l'adresse dans
// la table « abonnes » avec la clé de service, et on envoie un mot de
// bienvenue qui porte déjà le lien de désinscription (obligation légale).
//
// Une adresse déjà connue n'est jamais une erreur : si elle s'était
// désinscrite, on la réactive ; sinon on remercie sans rien changer.

const { SITE, base, gabarit, envoyer } = require("./_courriel.js");

const propre = (v, max) => String(v == null ? "" : v).replace(/\s+/g, " ").trim().slice(0, max);
const valide = (e) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e) && e.length <= 120;

function bienvenue(lien) {
  return gabarit({
    titre: "Bienvenue au Chai",
    chapeau: "Merci de votre inscription. Vous recevrez désormais nos rendez-vous : dégustations, soirées vigneron, brunchs et rencontres à Cugnaux.",
    corps: `<p style="margin:0 0 16px;font-size:16px;line-height:1.55">
      Quelques courriels par saison, pas davantage — juste ce qu'il faut pour ne rien manquer.</p>`,
    bouton: { texte: "Voir l'agenda", lien: SITE + "/agenda" },
    pied: `Vous recevez ce message parce que vous vous êtes inscrit·e sur notre site.<br>
      <a href="${lien}" style="color:#7a6355">Se désinscrire</a>`,
  });
}

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") return res.status(405).json({ erreur: "POST attendu" });
  if (!process.env.SUPABASE_URL || !process.env.SUPABASE_SERVICE_KEY) {
    return res.status(503).json({ erreur: "L'inscription n'est pas encore configurée." });
  }

  let corps = req.body;
  if (typeof corps === "string") { try { corps = JSON.parse(corps); } catch { corps = {}; } }
  corps = corps || {};

  if (propre(corps.site_web, 50)) return res.status(200).json({ ok: true });   // pot de miel
  const email = propre(corps.email, 120).toLowerCase();
  const source = propre(corps.source, 40) || "site";
  if (!valide(email)) return res.status(400).json({ erreur: "Cette adresse ne semble pas valide." });

  try {
    const connus = await base("abonnes?select=id,statut,jeton&email=eq." + encodeURIComponent(email));
    let jeton, nouveau = false;

    if (connus.length) {
      jeton = connus[0].jeton;
      if (connus[0].statut !== "actif") {
        await base("abonnes?id=eq." + connus[0].id, {
          method: "PATCH",
          headers: { Prefer: "return=minimal" },
          body: JSON.stringify({ statut: "actif", desinscrit_le: null, source }),
        });
        nouveau = true;                       // réinscription : on redit bonjour
      }
    } else {
      try {
        const [ligne] = await base("abonnes", {
          method: "POST",
          headers: { Prefer: "return=representation" },
          body: JSON.stringify({ email, source }),
        });
        // Si la base n'a pas renvoyé la ligne, on la relit plutôt que d'échouer.
        jeton = (ligne && ligne.jeton) ||
          (await base("abonnes?select=jeton&email=eq." + encodeURIComponent(email)))[0].jeton;
        nouveau = true;
      } catch (err) {
        // Deux envois du formulaire en même temps : l'index unique refuse le
        // second. L'adresse est enregistrée, c'est tout ce qui compte.
        if (!/23505|duplicate/i.test(err.message)) throw err;
        return res.status(200).json({ ok: true });
      }
    }

    if (nouveau) {
      await envoyer({
        a: email,
        sujet: "Bienvenue au Chai Gourmand",
        html: bienvenue(SITE + "/desinscription?jeton=" + jeton),
      }).catch((err) => console.error("bienvenue non envoyée", err));   // jamais bloquant
    }
    return res.status(200).json({ ok: true });
  } catch (err) {
    console.error(err);
    return res.status(502).json({ erreur: "Petit souci technique — réessayez dans un instant." });
  }
};

module.exports.gabarits = { bienvenue };   // aperçu hors ligne
