// Banc d'essai des courriels : « node outils/essai_courriels.js ».
//
// On remplace fetch : rien ne part chez Brevo, rien ne touche Supabase. On
// vérifie seulement que chaque route décide bien ce qu'elle doit décider.
process.env.SUPABASE_URL = "https://exemple.supabase.co";
process.env.SUPABASE_SERVICE_KEY = "sb_secret_faux";
process.env.BREVO_API_KEY = "faux";
process.env.COURRIEL_EXPEDITEUR = "bonjour@exemple.fr";
process.env.COURRIEL_MAISON = "adrien@exemple.fr";

const journal = [];
let base = {};                      // ce que la « base » répond

global.fetch = async (url, o = {}) => {
  journal.push({ url: String(url), methode: o.method || "GET", corps: o.body ? JSON.parse(o.body) : null });
  const u = String(url);
  if (u.includes("/auth/v1/user")) return rep(200, { id: "u1", email: "adrien@exemple.fr" });
  if (u.includes("api.brevo.com")) return rep(201, { messageId: "<1@brevo>" });
  if ((o.method || "GET") === "POST" && u.endsWith("/rest/v1/abonnes"))
    return rep(201, [{ id: "n1", jeton: "jeton-neuf", ...JSON.parse(o.body) }]);
  for (const [motif, valeur] of Object.entries(base)) if (u.includes(motif)) return rep(200, valeur);
  return rep(200, []);
};
const rep = (s, j) => ({ ok: s < 400, status: s, json: async () => j, text: async () => JSON.stringify(j) });

function reponse() {
  const r = { code: 0, corps: null, entetes: {} };
  r.setHeader = (k, v) => { r.entetes[k] = v; };
  r.status = (c) => { r.code = c; return r; };
  r.json = (j) => { r.corps = j; return r; };
  r.send = (t) => { r.corps = t; return r; };
  return r;
}
const requete = (corps, connecte = true) => ({
  method: "POST", body: corps,
  headers: connecte ? { authorization: "Bearer jeton" } : {},
});

const essais = [];
const verifier = (nom, condition, vu) => essais.push({ nom, ok: !!condition, vu });

(async () => {
  const statut = require("../api/statut-reservation.js");
  const resa = { id: "11111111-2222-3333-4444-555555555555", lieu: "francazal", date: "2026-09-26",
                 heure: "20:00:00", couverts: 4, nom: "Camille Estève", email: "camille@exemple.fr",
                 confirmation_envoyee: null, annulation_envoyee: null };

  // 1. confirmation : le client est prévenu, la date d'envoi est notée
  base = { "reservations?select=*": [resa] };
  journal.length = 0;
  let r = reponse();
  await statut(requete({ id: resa.id, statut: "confirmee" }), r);
  verifier("confirmation → 200", r.code === 200, r.code);
  verifier("confirmation → courriel envoyé", r.corps.courriel === "envoye", r.corps);
  verifier("confirmation → Brevo appelé", journal.some((a) => a.url.includes("brevo")), null);
  const patch = journal.find((a) => a.methode === "PATCH");
  verifier("confirmation → horodatée", patch && patch.corps.confirmation_envoyee, patch && patch.corps);
  verifier("confirmation → annulation remise à zéro", patch && patch.corps.annulation_envoyee === null, patch && patch.corps);
  const brevo = journal.find((a) => a.url.includes("brevo"));
  verifier("confirmation → au bon destinataire", brevo.corps.to[0].email === "camille@exemple.fr", brevo.corps.to);
  verifier("confirmation → sujet lisible", /26 septembre 2026 à 20h00/.test(brevo.corps.subject), brevo.corps.subject);

  // 2. deux fois de suite : rien ne repart
  base = { "reservations?select=*": [{ ...resa, confirmation_envoyee: "2026-09-09T10:00:00Z" }] };
  journal.length = 0; r = reponse();
  await statut(requete({ id: resa.id, statut: "confirmee" }), r);
  verifier("re-confirmation → pas de second courriel", !journal.some((a) => a.url.includes("brevo")), r.corps);
  verifier("re-confirmation → le dit", r.corps.courriel === "deja envoye", r.corps);

  // 3. sans adresse : on le signale
  base = { "reservations?select=*": [{ ...resa, email: null }] };
  journal.length = 0; r = reponse();
  await statut(requete({ id: resa.id, statut: "annulee" }), r);
  verifier("sans adresse → prévenir par téléphone", r.corps.courriel === "sans adresse", r.corps);

  // 4. non connecté : refusé
  r = reponse();
  await statut(requete({ id: resa.id, statut: "confirmee" }, false), r);
  verifier("non connecté → 401", r.code === 401, r.code);

  // 5. annonce d'un brouillon : refusée
  const annoncer = require("../api/annoncer-evenement.js");
  const ev = { id: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", titre: "Soirée vigneron", date: "2026-10-09",
               heure: "19h30", lieu: "annexe", reservation: true, statut: "brouillon", annonce_envoyee: null };
  base = { "evenements?select=*": [ev] };
  r = reponse();
  await annoncer(requete({ id: ev.id }), r);
  verifier("brouillon → refus d'annoncer", r.code === 400, r.corps);

  // 6. annonce d'un événement publié : un envoi par abonné
  base = { "evenements?select=*": [{ ...ev, statut: "publie" }],
           "abonnes?select=email,jeton": [{ email: "a@x.fr", jeton: "aa" }, { email: "b@x.fr", jeton: "bb" }] };
  journal.length = 0; r = reponse();
  await annoncer(requete({ id: ev.id }), r);
  verifier("annonce → 2 destinataires", r.corps.envoyes === 2, r.corps);
  const envoi = journal.find((a) => a.url.includes("brevo"));
  verifier("annonce → une version par abonné", envoi.corps.messageVersions.length === 2, null);
  verifier("annonce → lien de désinscription personnel",
    envoi.corps.messageVersions[0].htmlContent.includes("jeton=aa") &&
    envoi.corps.messageVersions[1].htmlContent.includes("jeton=bb"), null);
  verifier("annonce → plus de repère à remplacer",
    !envoi.corps.messageVersions[0].htmlContent.includes("__DESINSCRIPTION__"), null);

  // 7. déjà annoncé : on prévient au lieu de renvoyer
  base["evenements?select=*"] = [{ ...ev, statut: "publie", annonce_envoyee: "2026-09-08T09:00:00Z", annonce_nombre: 12 }];
  journal.length = 0; r = reponse();
  await annoncer(requete({ id: ev.id }), r);
  verifier("déjà annoncé → 409", r.code === 409, r.corps);
  journal.length = 0; r = reponse();
  await annoncer(requete({ id: ev.id, forcer: true }), r);
  verifier("déjà annoncé + forcer → part quand même", r.corps.envoyes === 2, r.corps);

  // 8. inscription : l'adresse entre, le mot de bienvenue part
  const news = require("../api/newsletter.js");
  base = { "abonnes?select=id,statut,jeton": [] };
  journal.length = 0; r = reponse();
  await news({ method: "POST", headers: {}, body: { email: "Camille@Exemple.FR ", source: "accueil" } }, r);
  const insertion = journal.find((a) => a.methode === "POST" && a.url.includes("/rest/v1/abonnes"));
  verifier("inscription → adresse en minuscules", insertion && insertion.corps.email === "camille@exemple.fr", insertion && insertion.corps);
  verifier("inscription → 200", r.code === 200, r.corps);
  const accueil = journal.find((a) => a.url.includes("brevo"));
  verifier("inscription → mot de bienvenue", accueil && accueil.corps.to[0].email === "camille@exemple.fr", accueil && accueil.corps.to);
  verifier("inscription → lien de désinscription dedans",
    accueil && accueil.corps.htmlContent.includes("desinscription?jeton=jeton-neuf"), null);

  // 8 bis. adresse déjà connue et toujours inscrite : rien ne repart
  base = { "abonnes?select=id,statut,jeton": [{ id: "1", statut: "actif", jeton: "aa" }] };
  journal.length = 0; r = reponse();
  await news({ method: "POST", headers: {}, body: { email: "camille@exemple.fr" } }, r);
  verifier("déjà inscrit → pas de second bonjour", !journal.some((a) => a.url.includes("brevo")), null);
  verifier("déjà inscrit → remercié quand même", r.code === 200 && r.corps.ok, r.corps);

  // 8 ter. adresse revenue après une désinscription : on redit bonjour
  base = { "abonnes?select=id,statut,jeton": [{ id: "1", statut: "desinscrit", jeton: "aa" }] };
  journal.length = 0; r = reponse();
  await news({ method: "POST", headers: {}, body: { email: "camille@exemple.fr" } }, r);
  const reprise = journal.find((a) => a.methode === "PATCH");
  verifier("réinscription → statut réactivé", reprise && reprise.corps.statut === "actif", reprise && reprise.corps);
  verifier("réinscription → nouveau bonjour", journal.some((a) => a.url.includes("brevo")), null);

  // 9. pot de miel : silence radio
  journal.length = 0; r = reponse();
  await news({ method: "POST", headers: {}, body: { email: "spam@x.fr", site_web: "http://spam" } }, r);
  verifier("pot de miel → rien n'est écrit", journal.length === 0, journal.length);
  verifier("pot de miel → réponse anodine", r.code === 200 && r.corps.ok, r.corps);

  // 10. désinscription : GET demande confirmation, POST agit
  const desinscrire = require("../api/desinscription.js");
  base = { "abonnes?select=id,email,statut": [{ id: "1", email: "camille@exemple.fr", statut: "actif" }] };
  journal.length = 0; r = reponse();
  await desinscrire({ method: "GET", query: { jeton: "abc123" }, headers: {} }, r);
  verifier("désinscription GET → demande confirmation", /Confirmer/.test(r.corps), r.code);
  verifier("désinscription GET → n'écrit rien", !journal.some((a) => a.methode === "PATCH"), null);
  journal.length = 0; r = reponse();
  await desinscrire({ method: "POST", body: "jeton=abc123", headers: {} }, r);
  const sortie = journal.find((a) => a.methode === "PATCH");
  verifier("désinscription POST → statut changé", sortie && sortie.corps.statut === "desinscrit", sortie && sortie.corps);
  verifier("désinscription POST → page de fin", /C.est fait/.test(r.corps), r.code);

  // 11. réservation reçue : elle entre en base et Adrien est prévenu
  const reserver = require("../api/reserver.js");
  const demain = new Date(Date.now() + 7 * 864e5).toISOString().slice(0, 10);
  const jeudi = (() => { const d = new Date(demain); while (d.getDay() !== 4) d.setDate(d.getDate() + 1);
                         return d.toISOString().slice(0, 10); })();
  global.fetch = async (url, o = {}) => {
    journal.push({ url: String(url), methode: o.method || "GET", corps: o.body ? JSON.parse(o.body) : null });
    if (String(url).includes("brevo")) return rep(201, {});
    return rep(201, [{ id: "r1" }]);
  };
  journal.length = 0; r = reponse();
  await reserver({ method: "POST", headers: {}, body: {
    lieu: "francazal", date: jeudi, heure: "20:00", couverts: "4",
    nom: "Camille Estève", telephone: "06 12 34 56 78", email: "camille@exemple.fr",
    message: "Une table près de la fenêtre." } }, r);
  verifier("réservation → 201", r.code === 201, r.corps);
  const alerte = journal.find((a) => a.url.includes("brevo"));
  verifier("réservation → alerte à la maison", alerte && alerte.corps.to[0].email === "adrien@exemple.fr", alerte && alerte.corps.to);
  verifier("réservation → répondre écrit au client",
    alerte && alerte.corps.replyTo.email === "camille@exemple.fr", alerte && alerte.corps.replyTo);
  verifier("réservation → le message est dans l'alerte",
    alerte && alerte.corps.htmlContent.includes("près de la fenêtre"), null);

  journal.length = 0; r = reponse();
  await reserver({ method: "POST", headers: {}, body: {
    lieu: "francazal", date: jeudi, heure: "20:00", couverts: "4", nom: "Robot",
    telephone: "0612345678", site_web: "http://spam" } }, r);
  verifier("réservation piégée → rien n'est écrit", journal.length === 0, journal.length);
  verifier("réservation piégée → réponse anodine", r.code === 200 && r.corps.ok, r.corps);

  const rates = essais.filter((e) => !e.ok);
  essais.forEach((e) => console.log((e.ok ? "  ✓ " : "  ✗ ") + e.nom + (e.ok ? "" : "   → " + JSON.stringify(e.vu))));
  console.log("\n" + (essais.length - rates.length) + "/" + essais.length + " essais passés");
  process.exit(rates.length ? 1 : 0);
})();
