/* ============================================================
   LE CHAI GOURMAND — interactions partagées (toutes pages)
   ============================================================ */
(function(){
  "use strict";
  const reduit = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- année du footer ---------- */
  const annee = document.getElementById("annee");
  if(annee) annee.textContent = new Date().getFullYear();

  /* ---------- nav : fond au scroll + jauge + verre de la cave ---------- */
  const nav = document.getElementById("nav");
  const jauge = document.querySelector(".jauge");
  const vinScroll = document.getElementById("vinScroll");
  const verreSante = document.getElementById("verreSante");
  const verreWrap = document.getElementById("verreScroll");
  const traineePath = document.getElementById("traineePath");
  const traineeHalo = document.querySelector(".trainee-halo");
  const traineeComete = document.getElementById("traineeComete");
  const etincelles = document.querySelectorAll(".etincelle");
  const traineeLongueur = traineePath ? traineePath.getTotalLength() : 0;
  const sectionEsprit = document.getElementById("esprit");
  function surScroll(){
    const y = window.scrollY;
    const vh = window.innerHeight;
    if(nav) nav.classList.toggle("plein", y > 40);
    if(jauge){
      const h = document.documentElement.scrollHeight - vh;
      jauge.style.width = (h > 0 ? (y / h) * 100 : 0) + "%";
    }
    /* le verre se remplit pendant qu'on le croise à l'écran */
    if(vinScroll && verreWrap){
      const r = verreWrap.getBoundingClientRect();
      let p = (vh - r.top) / (vh * 0.75);
      p = Math.max(0, Math.min(1, p));
      if(reduit) p = 1;
      vinScroll.style.transform = "translateY(" + Math.round((1 - p) * 138) + "px)";
      if(verreSante) verreSante.classList.toggle("visible", p >= 0.99);
    }
    /* la traînée dorée se dessine en travers de la section esprit
       (cadence calée sur le scroll : tracé complet après ~60 % du bloc) */
    if(traineePath && sectionEsprit){
      const r = sectionEsprit.getBoundingClientRect();
      let p = (vh * 0.9 - r.top) / (r.height * 0.6);
      p = Math.max(0, Math.min(1, p));
      if(reduit) p = 1;
      traineePath.style.strokeDashoffset = 1 - p;
      if(traineeHalo) traineeHalo.style.strokeDashoffset = 1 - p;
      if(traineeComete){
        const pt = traineePath.getPointAtLength(p * traineeLongueur);
        traineeComete.setAttribute("cx", pt.x);
        traineeComete.setAttribute("cy", pt.y);
        traineeComete.style.opacity = (!reduit && p > 0.02 && p < 0.98) ? 1 : 0;
      }
      etincelles.forEach(function(e){
        e.classList.toggle("visible", p >= parseFloat(e.dataset.seuil));
      });
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

  /* ---------- billet du comptoir : statut du jour des deux établissements ---------- */
  const statutEl = document.getElementById("comptoirStatut");
  if(statutEl){
    // horaires réels (0 = dimanche … 6 = samedi ; null = fermé)
    const lieuxComptoir = [
      {nom: "Le Chai — Francazal", horaires: {0:null, 1:null, 2:[10,21], 3:[10,21], 4:[10,23], 5:[10,23], 6:[10,23]}},
      {nom: "L'Annexe — Cézerou",  horaires: {0:null, 1:null, 2:[16,20], 3:[16,20], 4:[16,22], 5:[16,22], 6:[10,22]}}
    ];
    const maintenant = new Date();
    const jour = maintenant.getDay();
    const heure = maintenant.getHours() + maintenant.getMinutes() / 60;
    function fmtH(n){ return n + "h00"; }
    function etatDuJour(horaires){
      const duJour = horaires[jour];
      if(duJour && heure >= duJour[0] && heure < duJour[1]){
        return {point: "ouvert", texte: "ouvert · jusqu'à " + fmtH(duJour[1])};
      }
      if(duJour && heure < duJour[0]){
        return {point: "bientot", texte: "ouvre à " + fmtH(duJour[0])};
      }
      return {point: "ferme", texte: duJour ? "fermé ce soir" : "fermé aujourd'hui"};
    }
    statutEl.innerHTML = lieuxComptoir.map(function(l){
      const e = etatDuJour(l.horaires);
      return '<span class="statut-ligne"><span class="point-statut ' + e.point + '" aria-hidden="true"></span>'
        + l.nom + ' · ' + e.texte + '</span>';
    }).join("");
  }

  /* ---------- l'accord du moment : rotation en fondu ---------- */
  const accordEl = document.getElementById("accordFondu");
  if(accordEl){
    const accords = [
      ["Planche mixte", "un Fronton rouge"],
      ["Camembert rôti", "un Jurançon moelleux"],
      ["Escargots à la bourguignonne", "un Bourgogne blanc"],
      ["Tartine chèvre & miel", "un Gaillac blanc"],
      ["Crevettes grillées au chorizo", "un rosé de caractère"],
      ["Saucisse de Toulouse", "un Cahors charpenté"]
    ];
    let iAccord = 0;
    function afficherAccord(){
      accordEl.innerHTML = accords[iAccord][0]
        + ' <span class="etoile-accord">✦</span> '
        + accords[iAccord][1];
    }
    setInterval(function(){
      iAccord = (iAccord + 1) % accords.length;
      if(reduit){ afficherAccord(); return; }
      accordEl.style.opacity = "0";
      setTimeout(function(){ afficherAccord(); accordEl.style.opacity = "1"; }, 600);
    }, 5000);
  }

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
  const comptoirRdvEl = document.getElementById("comptoirRdv");
  const bandeauAgendaEl = document.getElementById("bandeauAgenda");
  if(!listeEl && !prochainEl && !calEl && !comptoirRdvEl && !bandeauAgendaEl) return;

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

  /* ====== PROGRAMMATION DATÉE — pour mettre à jour le planning,
     modifier simplement ce tableau (source : document client).
     Format de date : "AAAA-MM-JJ". Les événements passés
     disparaissent automatiquement du site. ====== */
  const PROGRAMMATION = [
    // — Septembre 2026 · Le Chai — Francazal
    {date: "2026-09-03", lieu: "francazal", titre: "Afterwork Latino",
     desc: "Le comptoir passe à l'heure latine — tapas, verres et rythmes qui réchauffent.", heure: "dès 17h"},
    {date: "2026-09-04", lieu: "francazal", titre: "Afterwork French Party + Quizz Culture Générale",
     desc: "Chanson française à l'apéro, puis quizz spécial rentrée scolaire pour départager les tablées.", heure: "dès 17h · quizz à 21h"},
    {date: "2026-09-05", lieu: "francazal", titre: "Concert — David Soul",
     desc: "Concert live au Chai, un verre à la main.", heure: "21h"},
    {date: "2026-09-10", lieu: "francazal", titre: "Afterwork Soirée années 2000",
     desc: "La bande-son de vos années lycée, les planches en plus.", heure: "dès 17h"},
    {date: "2026-09-11", lieu: "francazal", titre: "Afterwork House + Blind Test",
     desc: "House à l'apéro, blind test à 21h — venez en équipe.", heure: "dès 17h · blind test à 21h"},
    {date: "2026-09-12", lieu: "francazal", titre: "Concert de saxophone & Soirée Blanche",
     desc: "Sax en live et dress code blanc pour finir l'été en beauté.", heure: "dès 21h"},
    {date: "2026-09-17", lieu: "francazal", titre: "Afterwork Rap & RnB US",
     desc: "Le comptoir en mode US — planches, verres et classiques du genre.", heure: "dès 17h"},
    {date: "2026-09-18", lieu: "francazal", titre: "DJ Nana",
     desc: "DJ set au Chai jusqu'au bout de la nuit.", heure: "21h – 1h"},
    {date: "2026-09-24", lieu: "francazal", titre: "Afterwork Disco / Funk",
     desc: "Paillettes sonores et verres bien accordés.", heure: "dès 17h"},
    {date: "2026-09-25", lieu: "francazal", titre: "Afterwork Rock + Concert Free O'Clock",
     desc: "Apéro rock puis concert live de Free O'Clock.", heure: "dès 17h · concert à 20h"},
    // — Septembre 2026 · L'Annexe
    {date: "2026-09-10", lieu: "annexe", titre: "Initiation à la dégustation — vins d'Espagne",
     desc: "Soirée accords mets & vins autour des vins d'Espagne, guidée par le caviste.", heure: "en soirée", resa: true},
    {date: "2026-09-24", lieu: "annexe", titre: "Initiation à la dégustation — vins de Bourgogne",
     desc: "Soirée accords mets & vins autour des vins de Bourgogne, guidée par le caviste.", heure: "en soirée", resa: true}
    // NB : samedis 19 et 26 septembre en cours de préparation — masqués à la demande du client.
  ];
  PROGRAMMATION.forEach(function(ev){
    const p = ev.date.split("-");
    const d = new Date(+p[0], +p[1] - 1, +p[2]);
    if(d >= aujourdHui){
      evenements.push({date: d, lieu: ev.lieu, titre: ev.titre, desc: ev.desc, heure: ev.heure, resa: !!ev.resa});
    }
  });

  /* ====== RÉCURRENTS (générés automatiquement chaque semaine) ====== */
  // — Brunch de l'Annexe : tous les samedis
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
  // — Dégustation de vins, bières & spiritueux : tous les samedis,
  //   en dehors des horaires de service, dans les deux établissements
  let samediDegust = (aujourdHui.getDay() === 6) ? new Date(aujourdHui) : prochainJour(aujourdHui, 6);
  for(let i = 0; i < 4; i++){
    ["francazal", "annexe"].forEach(function(lieu){
      evenements.push({
        date: new Date(samediDegust),
        lieu: lieu,
        titre: "Dégustation de vins, bières & spiritueux",
        desc: "Sur place, en dehors des horaires de service — on ouvre les bouteilles, vous goûtez.",
        heure: "hors horaires de service",
        recurrence: "Tous les samedis"
      });
    });
    samediDegust = ajouterJours(samediDegust, 7);
  }

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
  const nomsLieux = {francazal:"Le Chai — Francazal", annexe:"L'Annexe — Cézerou"};

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

  /* ---------- bandeau sous le hero : les 3 prochains rendez-vous ---------- */
  if(bandeauAgendaEl && evenements.length){
    // un seul exemplaire par intitulé : le bandeau montre trois rendez-vous
    // différents plutôt que le même récurrent dans les deux établissements
    const vus = {};
    const teaser = evenements.filter(function(ev){
      if(vus[ev.titre]) return false;
      vus[ev.titre] = true;
      return true;
    }).slice(0, 3);
    bandeauAgendaEl.innerHTML = teaser.map(function(ev){
      const mois = fmtMois.format(ev.date).replace(".", "");
      return '<a class="bandeau-ev" href="/agenda">'
        + '<span class="bandeau-ev-date">'
        +   '<span class="bev-sem">' + fmtJour.format(ev.date) + '</span>'
        +   '<span class="bev-jour">' + ev.date.getDate() + '</span>'
        +   '<span class="bev-mois">' + mois + '</span>'
        + '</span>'
        + '<span class="bandeau-ev-corps">'
        +   '<span class="bandeau-ev-titre">' + ev.titre + '</span>'
        +   '<span class="bandeau-ev-heure">' + ev.heure + '</span>'
        +   '<span class="bandeau-ev-lieu"><span class="pastille ' + ev.lieu + '"></span>' + nomsLieux[ev.lieu] + '</span>'
        + '</span>'
        + '</a>';
    }).join("");
  }

  /* ---------- billet du comptoir : prochain rendez-vous ---------- */
  if(comptoirRdvEl && evenements.length){
    const ev = evenements[0];
    comptoirRdvEl.innerHTML = 'Prochain rendez-vous : <a href="/agenda">'
      + ev.titre + ' — ' + fmtDateLongue.format(ev.date) + '</a>';
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
