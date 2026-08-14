/* ============================================================
   LE CHAI GOURMAND — interactions partagées (toutes pages)
   ============================================================ */
(function(){
  "use strict";
  const reduit = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- année du footer ---------- */
  const annee = document.getElementById("annee");
  if(annee) annee.textContent = new Date().getFullYear();

  /* ---------- nav : fond au scroll + jauge + parallaxe hero ---------- */
  const nav = document.getElementById("nav");
  const jauge = document.querySelector(".jauge");
  const scene = document.getElementById("sceneVerre");
  function surScroll(){
    const y = window.scrollY;
    if(nav) nav.classList.toggle("plein", y > 40);
    if(jauge){
      const h = document.documentElement.scrollHeight - window.innerHeight;
      jauge.style.width = (h > 0 ? (y / h) * 100 : 0) + "%";
    }
    if(scene && !reduit && window.innerWidth > 1000){
      scene.style.transform = "translateY(" + (y * 0.08) + "px)";
    }
  }
  window.addEventListener("scroll", surScroll, {passive:true});
  surScroll();

  /* ---------- menu mobile ---------- */
  const burger = document.getElementById("burger");
  const liens = document.getElementById("navLiens");
  if(burger && liens){
    burger.addEventListener("click", function(){
      const ouvert = liens.classList.toggle("ouvert");
      burger.classList.toggle("ouvert", ouvert);
      burger.setAttribute("aria-expanded", ouvert);
      burger.setAttribute("aria-label", ouvert ? "Fermer le menu" : "Ouvrir le menu");
    });
    liens.querySelectorAll("a").forEach(function(a){
      a.addEventListener("click", function(){
        liens.classList.remove("ouvert");
        burger.classList.remove("ouvert");
        burger.setAttribute("aria-expanded","false");
      });
    });
  }

  /* ---------- bandeau : dupliquer pour boucle parfaite ---------- */
  const piste = document.getElementById("bandeauPiste");
  if(piste) piste.innerHTML += piste.innerHTML;

  /* ---------- révélations au scroll ---------- */
  const io = new IntersectionObserver(function(entrees){
    entrees.forEach(function(e){
      if(e.isIntersecting){
        e.target.classList.add("visible");
        io.unobserve(e.target);
      }
    });
  }, {threshold:.15, rootMargin:"0px 0px -40px 0px"});
  document.querySelectorAll(".rv").forEach(function(el){ io.observe(el); });

  /* ---------- compteurs ---------- */
  const compteurs = document.querySelectorAll(".compteur");
  if(compteurs.length){
    const ioCompteur = new IntersectionObserver(function(entrees){
      entrees.forEach(function(e){
        if(!e.isIntersecting) return;
        const el = e.target;
        ioCompteur.unobserve(el);
        const cible = parseInt(el.dataset.cible, 10);
        if(reduit){ el.textContent = cible; return; }
        const duree = 1600, debut = performance.now();
        function pas(t){
          const p = Math.min((t - debut) / duree, 1);
          const eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(cible * eased);
          if(p < 1) requestAnimationFrame(pas);
        }
        requestAnimationFrame(pas);
      });
    }, {threshold:.6});
    compteurs.forEach(function(el){ ioCompteur.observe(el); });
  }

  /* ---------- newsletter ----------
     Le formulaire est prêt côté interface. Pour collecter réellement les
     adresses, renseigner NEWSLETTER_ENDPOINT avec l'URL d'un service
     (Brevo, Mailchimp, Formspree…) — en attendant, l'adresse est gardée
     localement et un message de confirmation s'affiche. */
  const NEWSLETTER_ENDPOINT = "";
  const formNl = document.getElementById("formNewsletter");
  if(formNl){
    formNl.addEventListener("submit", function(e){
      e.preventDefault();
      const champ = formNl.querySelector('input[type="email"]');
      const msg = formNl.parentElement.querySelector(".newsletter-msg");
      const email = (champ.value || "").trim();
      if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){
        if(msg) msg.textContent = "Hmm, cette adresse ne semble pas valide — on réessaie ?";
        return;
      }
      function merci(){
        if(msg) msg.textContent = "Merci ! Vous serez prévenu·e des prochains rendez-vous du Chai.";
        champ.value = "";
      }
      if(NEWSLETTER_ENDPOINT){
        fetch(NEWSLETTER_ENDPOINT, {
          method: "POST",
          headers: {"Content-Type": "application/json", "Accept": "application/json"},
          body: JSON.stringify({email: email})
        }).then(merci).catch(function(){
          if(msg) msg.textContent = "Oups, petit souci technique — réessayez dans un instant.";
        });
      }else{
        try{
          const attente = JSON.parse(localStorage.getItem("chai-newsletter") || "[]");
          if(attente.indexOf(email) === -1) attente.push(email);
          localStorage.setItem("chai-newsletter", JSON.stringify(attente));
        }catch(err){ /* stockage indisponible : le message suffit */ }
        merci();
      }
    });
  }

  /* ============================================================
     AGENDA — génération dynamique
     · L'Annexe : brunch chaque samedi midi + œnologie un jeudi sur deux
     · Francazal : événements ponctuels
     Les dates sont calculées à partir d'aujourd'hui : l'agenda
     reste toujours à jour.
     Composants (chacun optionnel selon la page) :
       #agendaListe                 → liste d'événements (+ data-limite, + data-schema)
       #prochainRdv                 → carte "prochain rendez-vous"
       #calendrier + #apercuJour    → calendrier interactif + aperçu du jour
     ============================================================ */
  const listeEl = document.getElementById("agendaListe");
  const prochainEl = document.getElementById("prochainRdv");
  const calEl = document.getElementById("calendrier");
  const apercuEl = document.getElementById("apercuJour");
  if(!listeEl && !prochainEl && !calEl) return;

  const aujourdHui = new Date();
  aujourdHui.setHours(0,0,0,0);

  function prochainJour(depuis, jourSemaine){ // 0 = dimanche … 6 = samedi
    const d = new Date(depuis);
    const delta = (jourSemaine - d.getDay() + 7) % 7 || 7;
    d.setDate(d.getDate() + delta);
    return d;
  }
  function ajouterJours(d, n){ const r = new Date(d); r.setDate(r.getDate() + n); return r; }
  function cle(d){ return d.getFullYear() + "-" + d.getMonth() + "-" + d.getDate(); }

  const evenements = [];

  // — Brunch de l'Annexe : les 6 prochains samedis
  let samedi = (aujourdHui.getDay() === 6) ? new Date(aujourdHui) : prochainJour(aujourdHui, 6);
  for(let i = 0; i < 6; i++){
    evenements.push({
      date: new Date(samedi),
      lieu: "annexe",
      titre: "Le Brunch de l'Annexe",
      desc: "En terrasse : formule complète à 25 € — du jus artisanal à la brioche perdue.",
      heure: "le midi · 25 €",
      recurrence: "Tous les samedis",
      resa: true
    });
    samedi = ajouterJours(samedi, 7);
  }

  // — Soirée dégustation œnologique : un jeudi sur deux (ancrage : jeudi 8 janvier 2026)
  const ancrage = new Date(2026, 0, 8);
  let jeudi = (aujourdHui.getDay() === 4) ? new Date(aujourdHui) : prochainJour(aujourdHui, 4);
  const bonnesSemaines = [];
  while(bonnesSemaines.length < 3){
    const semaines = Math.round((jeudi - ancrage) / (7 * 864e5));
    if(semaines % 2 === 0) bonnesSemaines.push(new Date(jeudi));
    jeudi = ajouterJours(jeudi, 7);
  }
  bonnesSemaines.forEach(function(d){
    evenements.push({
      date: d,
      lieu: "annexe",
      titre: "Soirée dégustation œnologique",
      desc: "Six vins, un thème, un caviste bavard. Adrien vous emmène là où les étiquettes ne suffisent plus.",
      heure: "19h30",
      recurrence: "Un jeudi sur deux",
      resa: true
    });
  });

  // — Événements ponctuels à Francazal (dates d'exemple, à remplacer par la vraie programmation)
  evenements.push({
    date: prochainJour(ajouterJours(aujourdHui, 8), 5),
    lieu: "francazal",
    titre: "Vigneron invité : la Négrette en majesté",
    desc: "Un domaine de Fronton au comptoir, ses cuvées dans les verres, ses histoires en prime.",
    heure: "19h00",
    resa: true
  });
  evenements.push({
    date: prochainJour(ajouterJours(aujourdHui, 15), 3),
    lieu: "francazal",
    titre: "Accords d'été : tapas & vins frais",
    desc: "Cinq tapas, cinq verres, un seul mot d'ordre : la fraîcheur. Le duo cuisine-cave en démonstration.",
    heure: "19h30",
    resa: true
  });
  evenements.push({
    date: prochainJour(ajouterJours(aujourdHui, 23), 6),
    lieu: "francazal",
    titre: "Cave ouverte : les nouveaux arrivages",
    desc: "Dégustation libre des dernières trouvailles d'Adrien, tarif boutique toute la journée.",
    heure: "10h00 – 19h00"
  });

  evenements.sort(function(a, b){ return a.date - b.date; });

  // index par jour pour le calendrier
  const parJour = {};
  evenements.forEach(function(ev){
    const k = cle(ev.date);
    (parJour[k] = parJour[k] || []).push(ev);
  });

  const fmtJour = new Intl.DateTimeFormat("fr-FR", {weekday:"long"});
  const fmtMois = new Intl.DateTimeFormat("fr-FR", {month:"short"});
  const fmtMoisLong = new Intl.DateTimeFormat("fr-FR", {month:"long", year:"numeric"});
  const fmtDateLongue = new Intl.DateTimeFormat("fr-FR", {weekday:"long", day:"numeric", month:"long"});
  const nomsLieux = {francazal:"Le Chai — Francazal", annexe:"L'Annexe"};

  function badgeLieu(ev){
    return '<span class="ev-lieu ' + ev.lieu + '"><span class="pastille ' + ev.lieu + '"></span>' + nomsLieux[ev.lieu] + '</span>';
  }
  function metaEv(ev){
    return '<div class="ev-meta">'
      + '<span>' + fmtJour.format(ev.date) + ' · ' + ev.heure + '</span>'
      + (ev.recurrence ? '<span class="recur">↻ ' + ev.recurrence + '</span>' : '')
      + (ev.resa ? '<span>Sur réservation</span>' : '')
      + '</div>';
  }

  /* ---------- liste d'événements ---------- */
  if(listeEl){
    const limite = parseInt(listeEl.dataset.limite || "0", 10);
    const affiches = limite > 0 ? evenements.slice(0, limite) : evenements;
    let html = "";
    affiches.forEach(function(ev, i){
      const mois = fmtMois.format(ev.date).replace(".", "");
      html += '<article class="evenement" data-lieu="' + ev.lieu + '" style="--d:' + (i * 0.06) + 's">'
        + '<div class="ev-date" aria-hidden="true">'
        +   '<div class="ev-jour">' + ev.date.getDate() + '</div>'
        +   '<span class="ev-mois">' + mois + '</span>'
        +   '<span class="ev-semaine">' + fmtJour.format(ev.date).slice(0,3) + '.</span>'
        + '</div>'
        + '<div class="ev-corps">'
        +   badgeLieu(ev)
        +   '<h3 class="ev-titre">' + ev.titre + '</h3>'
        +   '<p class="ev-desc">' + ev.desc + '</p>'
        +   metaEv(ev)
        + '</div>'
        + '</article>';
    });
    listeEl.innerHTML = html;

    /* filtres par établissement */
    const filtres = document.querySelectorAll(".filtre");
    filtres.forEach(function(btn){
      btn.addEventListener("click", function(){
        filtres.forEach(function(b){ b.classList.remove("actif"); });
        btn.classList.add("actif");
        const lieu = btn.dataset.lieu;
        listeEl.querySelectorAll(".evenement").forEach(function(carte){
          carte.classList.toggle("cache", lieu !== "tous" && carte.dataset.lieu !== lieu);
        });
      });
    });
  }

  /* ---------- prochain rendez-vous (chronologique) ---------- */
  if(prochainEl && evenements.length){
    const ev = evenements[0];
    const mois = fmtMois.format(ev.date).replace(".", "");
    prochainEl.innerHTML =
      '<div class="prdv-date" aria-hidden="true">'
      +   '<div class="ev-jour">' + ev.date.getDate() + '</div>'
      +   '<span class="ev-mois">' + mois + '</span>'
      +   '<span class="ev-semaine">' + fmtJour.format(ev.date).slice(0,3) + '.</span>'
      + '</div>'
      + '<div class="prdv-corps">'
      +   '<span class="prdv-tag">✦ Le prochain rendez-vous</span>'
      +   '<h3>' + ev.titre + '</h3>'
      +   '<p>' + ev.desc + '</p>'
      +   '<div class="prdv-meta">'
      +     '<span>' + fmtDateLongue.format(ev.date) + ' · ' + ev.heure + '</span>'
      +     '<span>' + nomsLieux[ev.lieu] + '</span>'
      +   '</div>'
      + '</div>'
      + '<div class="prdv-cta"><a class="btn btn-ligne" href="https://www.instagram.com/le_chai_gourmand/" target="_blank" rel="noopener">Réserver</a></div>';
  }

  /* ---------- calendrier interactif + aperçu du jour ---------- */
  if(calEl && apercuEl){
    const moisMin = new Date(aujourdHui.getFullYear(), aujourdHui.getMonth(), 1);
    const dernierEv = evenements[evenements.length - 1].date;
    const moisMax = new Date(dernierEv.getFullYear(), dernierEv.getMonth(), 1);
    let moisAffiche = new Date(moisMin);
    let selection = evenements.length ? new Date(evenements[0].date) : new Date(aujourdHui);
    moisAffiche = new Date(selection.getFullYear(), selection.getMonth(), 1);

    function memeMois(a, b){ return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth(); }

    function rendreApercu(){
      const evs = parJour[cle(selection)] || [];
      let html = '<p class="apercu-titre">Au programme</p>'
        + '<p class="apercu-date">' + fmtDateLongue.format(selection) + '</p>';
      if(evs.length){
        evs.forEach(function(ev){
          html += '<div class="apercu-ev">'
            + badgeLieu(ev)
            + '<h3 class="ev-titre">' + ev.titre + '</h3>'
            + '<p class="ev-desc">' + ev.desc + '</p>'
            + metaEv(ev)
            + '</div>';
        });
        html += '<div class="apercu-cta"><a class="btn btn-plein" href="https://www.instagram.com/le_chai_gourmand/" target="_blank" rel="noopener">Réserver ma place</a></div>';
      }else{
        html += '<p class="apercu-vide">Rien de programmé ce jour-là… mais le comptoir, lui, est ouvert du mardi au samedi. Passez donc dire bonjour.</p>'
          + '<div class="apercu-cta"><a class="btn btn-plein" href="/nos-adresses">Voir les horaires</a></div>';
      }
      apercuEl.innerHTML = html;
    }

    function rendreCalendrier(){
      const an = moisAffiche.getFullYear(), mois = moisAffiche.getMonth();
      const premier = new Date(an, mois, 1);
      const nbJours = new Date(an, mois + 1, 0).getDate();
      const decalage = (premier.getDay() + 6) % 7; // semaine qui commence lundi
      let html = '<div class="cal-tete">'
        + '<span class="cal-mois" aria-live="polite">' + fmtMoisLong.format(moisAffiche) + '</span>'
        + '<div class="cal-fleches">'
        + '<button class="cal-fleche" type="button" data-nav="-1" aria-label="Mois précédent"' + (memeMois(moisAffiche, moisMin) ? " disabled" : "") + '>←</button>'
        + '<button class="cal-fleche" type="button" data-nav="1" aria-label="Mois suivant"' + (memeMois(moisAffiche, moisMax) ? " disabled" : "") + '>→</button>'
        + '</div></div>';
      html += '<div class="cal-grille">';
      ["lun","mar","mer","jeu","ven","sam","dim"].forEach(function(n){
        html += '<span class="cal-nom-jour" aria-hidden="true">' + n + '</span>';
      });
      for(let i = 0; i < decalage; i++) html += '<span class="cal-jour hors-mois" aria-hidden="true"></span>';
      for(let j = 1; j <= nbJours; j++){
        const d = new Date(an, mois, j);
        const evs = parJour[cle(d)] || [];
        const passe = d < aujourdHui;
        const classes = ["cal-jour"];
        if(passe) classes.push("passe");
        if(cle(d) === cle(aujourdHui)) classes.push("aujourdhui");
        if(evs.length) classes.push("a-events");
        if(cle(d) === cle(selection)) classes.push("selectionne");
        let etiquette = fmtDateLongue.format(d);
        if(evs.length) etiquette += " — " + evs.length + (evs.length > 1 ? " événements" : " événement : " + evs[0].titre);
        const lieux = [];
        evs.forEach(function(ev){ if(lieux.indexOf(ev.lieu) === -1) lieux.push(ev.lieu); });
        html += '<button type="button" class="' + classes.join(" ") + '"'
          + (passe ? " disabled" : ' data-jour="' + j + '"')
          + ' aria-label="' + etiquette + '"'
          + (cle(d) === cle(selection) ? ' aria-pressed="true"' : ' aria-pressed="false"')
          + '>' + j
          + (lieux.length ? '<span class="cal-points" aria-hidden="true">' + lieux.map(function(l){ return '<span class="cal-point ' + l + '"></span>'; }).join("") + '</span>' : "")
          + '</button>';
      }
      html += '</div>';
      html += '<div class="cal-legende" aria-hidden="true">'
        + '<span><span class="cal-point francazal"></span>Le Chai — Francazal</span>'
        + '<span><span class="cal-point annexe"></span>L’Annexe</span>'
        + '</div>';
      calEl.innerHTML = html;

      calEl.querySelectorAll(".cal-fleche").forEach(function(btn){
        btn.addEventListener("click", function(){
          moisAffiche = new Date(moisAffiche.getFullYear(), moisAffiche.getMonth() + parseInt(btn.dataset.nav, 10), 1);
          rendreCalendrier();
        });
      });
      calEl.querySelectorAll(".cal-jour[data-jour]").forEach(function(btn){
        btn.addEventListener("click", function(){
          selection = new Date(an, mois, parseInt(btn.dataset.jour, 10));
          rendreCalendrier();
          rendreApercu();
        });
      });
    }

    rendreCalendrier();
    rendreApercu();
  }

  /* ---------- SEO : JSON-LD Event injecté (page agenda) ---------- */
  if(listeEl && listeEl.dataset.schema === "1"){
    const adresses = {
      francazal: {
        nom: "Le Chai Gourmand — Francazal",
        rue: "9 rue Alfred Sauvy"
      },
      annexe: {
        nom: "L'Annexe du Chai Gourmand",
        rue: "14 rue de Cezerou"
      }
    };
    function iso(d){
      return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
    }
    const schema = {
      "@context": "https://schema.org",
      "@graph": evenements.map(function(ev){
        const lieu = adresses[ev.lieu];
        return {
          "@type": "Event",
          "name": ev.titre,
          "description": ev.desc,
          "startDate": iso(ev.date),
          "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
          "eventStatus": "https://schema.org/EventScheduled",
          "location": {
            "@type": "Place",
            "name": lieu.nom,
            "address": {
              "@type": "PostalAddress",
              "streetAddress": lieu.rue,
              "addressLocality": "Cugnaux",
              "postalCode": "31270",
              "addressCountry": "FR"
            }
          },
          "organizer": {
            "@type": "Organization",
            "name": "Le Chai Gourmand",
            "url": "https://lechaigourmand.vercel.app/"
          }
        };
      })
    };
    const s = document.createElement("script");
    s.type = "application/ld+json";
    s.textContent = JSON.stringify(schema);
    document.head.appendChild(s);
  }
})();
