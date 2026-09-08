// Régénère le site depuis la base, à la demande du back-office.
//
// Les fiches produits sont écrites dans les pages HTML pour que Google les
// lise ; les modifier en base ne suffit donc pas, il faut reconstruire. Ce
// point d'entrée déclenche un déploiement Vercel — mais seulement pour
// quelqu'un de connecté au back-office.
//
// Variable d'environnement à ajouter sur Vercel :
//   VERCEL_DEPLOY_HOOK   Settings → Git → Deploy Hooks → créer « back-office »

const MINIMUM_ENTRE_DEUX = 30 * 1000;      // pas plus d'un déploiement toutes les 30 s
let dernier = 0;

async function estConnecte(jeton) {
  if (!jeton || !process.env.SUPABASE_URL) return false;
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

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "POST") return res.status(405).json({ erreur: "POST attendu" });
  if (!process.env.VERCEL_DEPLOY_HOOK) {
    return res.status(503).json({ erreur: "La publication n'est pas configurée (VERCEL_DEPLOY_HOOK manquante)." });
  }

  const jeton = (req.headers.authorization || "").replace(/^Bearer\s+/i, "");
  if (!(await estConnecte(jeton))) {
    return res.status(401).json({ erreur: "Reconnectez-vous pour publier." });
  }

  const maintenant = Date.now();
  if (maintenant - dernier < MINIMUM_ENTRE_DEUX) {
    return res.status(429).json({ erreur: "Une publication vient d'être lancée, laissez-la finir." });
  }

  try {
    const r = await fetch(process.env.VERCEL_DEPLOY_HOOK, { method: "POST" });
    if (!r.ok) throw new Error("hook " + r.status);
    dernier = maintenant;
    return res.status(202).json({ ok: true });
  } catch (err) {
    console.error(err);
    return res.status(502).json({ erreur: "Vercel n'a pas répondu, réessayez dans un instant." });
  }
};
