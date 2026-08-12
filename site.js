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

  /* ============================================================
     AGENDA — génération dynamique
     · L'Annexe : brunch chaque samedi midi + œnologie un jeudi sur deux
     · Francazal : événements ponctuels
     Les dates sont calculées à partir d'aujourd'hui : l'agenda
     reste toujours à jour.
     Usage :
       <div id="agendaListe">                → liste complète + filtres
       <div id="agendaListe" data-limite="3"> → teaser (3 prochains)
       data-schema="1"                        → injecte le JSON-LD Event
     ============================================================ */
  const listeEl = document.getElementById("agendaListe");
  if(!listeEl) return;

  const aujourdHui = new Date();
  aujourdHui.setHours(0,0,0,0);

  function prochainJour(depuis, jourSemaine){ // 0 = dimanche … 6 = samedi
    const d = new Date(depuis);
    const delta = (jourSemaine - d.getDay() + 7) % 7 || 7;
    d.setDate(d.getDate() + delta);
    return d;
  }
  function ajouterJours(d, n){ const r = new Date(d); r.setDate(r.getDate() + n); return r; }

  const evenements = [];

  // — Brunch de l'Annexe : les 3 prochains samedis
  let samedi = (aujourdHui.getDay() === 6) ? new Date(aujourdHui) : prochainJour(aujourdHui, 6);
  for(let i = 0; i < 3; i++){
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
  while(bonnesSemaines.length < 2){
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

  const limite = parseInt(listeEl.dataset.limite || "0", 10);
  const affiches = limite > 0 ? evenements.slice(0, limite) : evenements;

  const fmtJour = new Intl.DateTimeFormat("fr-FR", {weekday:"long"});
  const fmtMois = new Intl.DateTimeFormat("fr-FR", {month:"short"});
  const nomsLieux = {francazal:"Le Chai — Francazal", annexe:"L'Annexe"};

  let html = "";
  affiches.forEach(function(ev, i){
    const semaine = fmtJour.format(ev.date);
    const mois = fmtMois.format(ev.date).replace(".", "");
    html += '<article class="evenement" data-lieu="' + ev.lieu + '" style="--d:' + (i * 0.06) + 's">'
      + '<div class="ev-date" aria-hidden="true">'
      +   '<div class="ev-jour">' + ev.date.getDate() + '</div>'
      +   '<span class="ev-mois">' + mois + '</span>'
      +   '<span class="ev-semaine">' + semaine.slice(0,3) + '.</span>'
      + '</div>'
      + '<div class="ev-corps">'
      +   '<span class="ev-lieu ' + ev.lieu + '"><span class="pastille ' + ev.lieu + '"></span>' + nomsLieux[ev.lieu] + '</span>'
      +   '<h3 class="ev-titre">' + ev.titre + '</h3>'
      +   '<p class="ev-desc">' + ev.desc + '</p>'
      +   '<div class="ev-meta">'
      +     '<span>' + semaine + ' · ' + ev.heure + '</span>'
      +     (ev.recurrence ? '<span class="recur">↻ ' + ev.recurrence + '</span>' : '')
      +     (ev.resa ? '<span>Sur réservation</span>' : '')
      +   '</div>'
      + '</div>'
      + '</article>';
  });
  listeEl.innerHTML = html;

  /* ---------- filtres agenda (page agenda uniquement) ---------- */
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

  /* ---------- SEO : JSON-LD Event injecté (page agenda) ---------- */
  if(listeEl.dataset.schema === "1"){
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
