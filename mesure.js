/* Mesure d'audience — Google Analytics 4, propriété chai-gourmand-ga4.
 *
 * En France, la CNIL n'autorise aucun dépôt ni lecture de cookie de mesure
 * avant le consentement : le script de Google n'est donc pas chargé tant que
 * le visiteur n'a pas accepté. Refuser ne charge rien du tout — pas même un
 * appel « sans cookie ».
 *
 * Le choix est gardé dans localStorage, pas dans un cookie : rien ne part
 * vers le serveur, et le visiteur le change quand il veut par le lien
 * « Mesure d'audience » en bas de page. Refuser doit être aussi simple
 * qu'accepter, et se retirer aussi simple que consentir.
 *
 * Événements maison, en plus des mesures automatiques de GA4 :
 *   reservation             — une table réservée depuis le site
 *   inscription_newsletter  — une adresse ajoutée à la lettre d'information
 * Ils s'envoient par chaiEvenement("nom", {…}), défini plus bas.
 */
(function () {
  "use strict";

  var ID = "G-9T2LYJ61YV";
  var CLE = "chai-mesure";                 // "oui" | "non"
  var charge = false;
  var refuse = false;                      // le visiteur a dit non
  var attente = [];                        // ce qui arrive avant le choix

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = gtag;

  // Consent Mode v2. Tout est refusé au départ ; seule la mesure d'audience
  // pourra passer à « granted ». Le Chai ne fait pas de publicité en ligne :
  // les trois consentements publicitaires restent fermés pour de bon.
  gtag("consent", "default", {
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
    analytics_storage: "denied",
    functionality_storage: "granted",
    security_storage: "granted",
    wait_for_update: 500
  });

  function lire() { try { return localStorage.getItem(CLE); } catch (e) { return null; } }
  function ecrire(v) { try { localStorage.setItem(CLE, v); } catch (e) { /* navigation privée */ } }

  // Le signal « Global Privacy Control » du navigateur vaut refus : on ne
  // demande rien à quelqu'un qui a déjà répondu à l'échelle de son navigateur.
  function refusAutomatique() {
    return navigator.globalPrivacyControl === true;
  }

  function demarrer() {
    if (charge) return;
    charge = true;
    gtag("consent", "update", { analytics_storage: "granted" });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + ID;
    document.head.appendChild(s);
    gtag("js", new Date());
    gtag("config", ID);
    // Ce qui s'est passé avant le clic sur « Accepter » n'est pas perdu.
    while (attente.length) {
      var e = attente.shift();
      gtag("event", e[0], e[1]);
    }
  }

  /* Envoie un événement, ou le met de côté tant que le choix n'est pas fait.
     Après un refus, rien n'est gardé : quelqu'un qui a dit non puis change
     d'avis plus tard ne doit pas voir partir ce qu'il a fait entre-temps.
     Ne jette jamais : une mesure ratée ne doit pas casser une réservation. */
  window.chaiEvenement = function (nom, parametres) {
    try {
      if (refuse) return;
      if (charge) gtag("event", nom, parametres || {});
      else if (attente.length < 20) attente.push([nom, parametres || {}]);
    } catch (e) { /* tant pis */ }
  };

  /* ---------- le bandeau ---------- */
  function bandeau() {
    var b = document.createElement("div");
    b.className = "cookies";
    b.setAttribute("role", "dialog");
    b.setAttribute("aria-label", "Mesure d’audience");
    b.innerHTML =
      '<p class="cookies-mot">Nous aimerions mesurer la fréquentation du site avec Google ' +
      'Analytics, pour savoir ce qui vous intéresse. Rien de publicitaire, et vous pouvez ' +
      'refuser sans que le site change d’un iota.</p>' +
      '<div class="cookies-choix">' +
        '<button type="button" class="btn btn-plein" data-oui>Accepter</button>' +
        '<button type="button" class="btn ref-plus" data-non>Refuser</button>' +
      "</div>";
    document.body.appendChild(b);
    // Un minuteur, pas requestAnimationFrame : dans un onglet d'arrière-plan
    // rAF ne se déclenche pas, et le bandeau resterait hors de l'écran.
    setTimeout(function () { b.classList.add("visible"); }, 30);

    function repondre(valeur) {
      ecrire(valeur);
      b.classList.remove("visible");
      setTimeout(function () { b.remove(); }, 320);
      if (valeur === "oui") { refuse = false; demarrer(); }
      else { refuse = true; attente.length = 0; }
    }
    b.querySelector("[data-oui]").addEventListener("click", function () { repondre("oui"); });
    b.querySelector("[data-non]").addEventListener("click", function () { repondre("non"); });
  }

  /* Rouvrir le choix — appelé par le lien du pied de page. */
  window.chaiRouvrirMesure = function () {
    if (document.querySelector(".cookies")) return;
    bandeau();
  };

  function demarrage() {
    var choix = lire();
    if (choix === "oui") { demarrer(); return; }
    if (choix === "non" || refusAutomatique()) { refuse = true; return; }
    bandeau();
  }

  // Le lien du pied de page rouvre le choix, sur n'importe quelle page.
  function brancherLiens() {
    document.querySelectorAll("[data-mesure]").forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        window.chaiRouvrirMesure();
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { demarrage(); brancherLiens(); });
  } else {
    demarrage();
    brancherLiens();
  }
})();
