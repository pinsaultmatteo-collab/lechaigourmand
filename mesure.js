/* Mesure d'audience — Google Analytics 4, propriété chai-gourmand-ga4.
 *
 * Chargé par les quinze pages du site, jamais par /admin : un back-office
 * n'a pas à peupler les statistiques de fréquentation.
 *
 * Le suivi démarre au chargement, sans demander le consentement : choix
 * assumé par le client, qui en porte la responsabilité. Pour revenir à un
 * bandeau d'accord préalable, voir l'historique git — commit 1b1fb0b.
 *
 * Événements maison, en plus des mesures automatiques de GA4 :
 *   reservation             — une table réservée depuis le site
 *   inscription_newsletter  — une adresse ajoutée à la lettre d'information
 * Ils s'envoient par chaiEvenement("nom", {…}), défini plus bas.
 */
(function () {
  "use strict";

  var ID = "G-9T2LYJ61YV";

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = gtag;

  var s = document.createElement("script");
  s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + ID;
  document.head.appendChild(s);

  gtag("js", new Date());
  gtag("config", ID);

  /* Envoie un événement. Ne jette jamais : une mesure ratée — bloqueur de
     publicité, réseau coupé — ne doit pas casser une réservation. */
  window.chaiEvenement = function (nom, parametres) {
    try {
      gtag("event", nom, parametres || {});
    } catch (e) { /* tant pis */ }
  };
})();
