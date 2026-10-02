/* Mesure d'audience — Google Analytics 4, propriété chai-gourmand-ga4.
 *
 * Chargé par les quinze pages du site, jamais par /admin : un back-office
 * n'a pas à peupler les statistiques de fréquentation.
 *
 * Le suivi démarre au chargement, sans demander le consentement : choix
 * assumé par le client, qui en porte la responsabilité. Pour revenir à un
 * bandeau d'accord préalable, voir l'historique git — commit 1b1fb0b.
 *
 * Reste une porte de sortie, promise par les mentions légales et sans quoi
 * elles mentiraient : qui a refusé une fois n'est plus suivi, et le script de
 * Google n'est même pas chargé. Le refus se pose depuis /mentions-legales.
 *
 * Événements maison, en plus des mesures automatiques de GA4 :
 *   reservation             — une table réservée depuis le site
 *   inscription_newsletter  — une adresse ajoutée à la lettre d'information
 * Ils s'envoient par chaiEvenement("nom", {…}), défini plus bas.
 */
(function () {
  "use strict";

  var ID = "G-9T2LYJ61YV";
  var CLE = "chai-mesure";                 // "non" = ne pas suivre

  function refuse() {
    try { return localStorage.getItem(CLE) === "non"; } catch (e) { return false; }
  }

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = gtag;

  if (!refuse()) {
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + ID;
    document.head.appendChild(s);
    gtag("js", new Date());
    gtag("config", ID);
  }

  /* Envoie un événement. Ne jette jamais : une mesure ratée — bloqueur de
     publicité, réseau coupé — ne doit pas casser une réservation. */
  window.chaiEvenement = function (nom, parametres) {
    try {
      if (refuse()) return;
      gtag("event", nom, parametres || {});
    } catch (e) { /* tant pis */ }
  };

  /* ---------- les deux boutons des mentions légales ---------- */
  function etat() {
    var dit = document.querySelector("[data-mesure-etat]");
    var non = refuse();
    var refuser = document.querySelector("[data-mesure-refuser]");
    var accepter = document.querySelector("[data-mesure-accepter]");
    if (refuser) refuser.hidden = non;
    if (accepter) accepter.hidden = !non;
    if (dit) dit.textContent = non
      ? "C’est noté : vos visites ne sont plus comptées."
      : "";
  }

  function brancher() {
    var refuser = document.querySelector("[data-mesure-refuser]");
    var accepter = document.querySelector("[data-mesure-accepter]");
    if (!refuser && !accepter) return;
    if (refuser) refuser.addEventListener("click", function () {
      try { localStorage.setItem(CLE, "non"); } catch (e) {}
      etat();
      // La page courante a déjà été comptée ; le reste de la visite ne l'est plus.
    });
    if (accepter) accepter.addEventListener("click", function () {
      try { localStorage.removeItem(CLE); } catch (e) {}
      etat();
      location.reload();
    });
    etat();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", brancher);
  else brancher();
})();
