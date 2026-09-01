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
      // le backdrop-filter du header en ferait un bloc conteneur :
      // l'overlay fixe se limiterait alors à la hauteur du header
      if(nav) nav.classList.toggle("menu-ouvert", ouvert);
      burger.setAttribute("aria-expanded", ouvert);
      burger.setAttribute("aria-label", ouvert ? "Fermer le menu" : "Ouvrir le menu");
    });
    liens.querySelectorAll("a").forEach(function(a){
      a.addEventListener("click", function(){
        liens.classList.remove("ouvert");
        burger.classList.remove("ouvert");
        if(nav) nav.classList.remove("menu-ouvert");
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

  /* ---------- slider des avis (accueil) ---------- */
  const avisPiste = document.getElementById("avisPiste");
  if(avisPiste){
    const fleches = document.querySelectorAll("[data-avis-nav]");
    const pointsEl = document.getElementById("avisPoints");
    const cartes = avisPiste.querySelectorAll(".avis-carte");

    function parVue(){
      // combien de cartes tiennent dans la piste (3, 2 ou 1 selon la largeur)
      const carte = cartes[0];
      if(!carte) return 1;
      return Math.max(1, Math.round(avisPiste.clientWidth / carte.getBoundingClientRect().width));
    }
    function nbPages(){ return Math.max(1, cartes.length - parVue() + 1); }
    function pageCourante(){
      const carte = cartes[0];
      if(!carte) return 0;
      const pas = carte.getBoundingClientRect().width + parseFloat(getComputedStyle(avisPiste).columnGap || 0);
      return Math.round(avisPiste.scrollLeft / pas);
    }
    function majEtat(){
      const p = pageCourante(), max = nbPages() - 1;
      fleches.forEach(function(f){
        f.disabled = (parseInt(f.dataset.avisNav, 10) < 0) ? p <= 0 : p >= max;
      });
      if(pointsEl){
        [...pointsEl.children].forEach(function(pt, i){
          pt.classList.toggle("actif", i === Math.min(p, max));
          pt.setAttribute("aria-selected", i === Math.min(p, max));
        });
      }
    }
    function construirePoints(){
      if(!pointsEl) return;
      pointsEl.innerHTML = "";
      for(let i = 0; i < nbPages(); i++){
        const b = document.createElement("button");
        b.type = "button";
        b.className = "avis-point";
        b.setAttribute("role", "tab");
        b.setAttribute("aria-label", "Voir les avis " + (i + 1));
        b.addEventListener("click", function(){ defiler(i, true); });
        pointsEl.appendChild(b);
      }
      majEtat();
    }
    function defiler(page, absolu){
      const carte = cartes[0];
      if(!carte) return;
      const pas = carte.getBoundingClientRect().width + parseFloat(getComputedStyle(avisPiste).columnGap || 0);
      const cible = absolu ? page : pageCourante() + page;
      avisPiste.scrollTo({left: Math.max(0, cible) * pas, behavior: reduit ? "instant" : "smooth"});
    }
    fleches.forEach(function(f){
      f.addEventListener("click", function(){ defiler(parseInt(f.dataset.avisNav, 10), false); });
    });
    avisPiste.addEventListener("scroll", function(){
      clearTimeout(avisPiste._t);
      avisPiste._t = setTimeout(majEtat, 90);
    }, {passive:true});
    window.addEventListener("resize", construirePoints);
    construirePoints();
  }

  /* ---------- filtres de la cave : pastilles par catégorie ---------- */
  const filtresCave = document.querySelectorAll("[data-cave]");
  const etagereEl = document.getElementById("etagere");
  if(filtresCave.length && etagereEl){
    const bouteilles = etagereEl.querySelectorAll(".bouteille-carte");
    // un message si une catégorie se retrouve vide (utile quand l'étagère évoluera)
    const vide = document.createElement("p");
    vide.className = "cave-vide";
    vide.hidden = true;
    vide.textContent = "Rien sous cette étiquette pour le moment — demandez au caviste, la cave en compte 300 autres.";
    etagereEl.appendChild(vide);
    // chaque pastille a sa propre vitrine de huit bouteilles : une même
    // référence peut donc figurer dans plusieurs, d'où data-vitrine
    const vitrine = function(c, cat){
      const liste = (c.dataset.vitrine || c.dataset.type || "").split(" ");
      return liste.indexOf(cat) !== -1;
    };
    filtresCave.forEach(function(btn){
      btn.addEventListener("click", function(){
        const cat = btn.dataset.cave;
        filtresCave.forEach(function(b){
          b.classList.toggle("actif", b === btn);
          b.setAttribute("aria-pressed", b === btn);
        });
        let visibles = 0;
        bouteilles.forEach(function(c){
          const montre = vitrine(c, cat);
          c.classList.toggle("cache", !montre);
          // les cartes qui n'avaient jamais paru n'ont pas été révélées au scroll
          if(montre){ c.classList.add("visible"); visibles++; }
        });
        vide.hidden = visibles > 0;
      });
    });
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

  /* ---------- bandeau sous le hero : trois dates, aperçu au clic ---------- */
  if(bandeauAgendaEl && evenements.length){
    const apercuEl = document.getElementById("bandeauApercu");
    // une seule entrée par jour : trois dates distinctes plutôt que trois doublons
    const parDate = [];
    evenements.forEach(function(ev){
      if(!parDate.some(function(e){ return cle(e.date) === cle(ev.date); })) parDate.push(ev);
    });
    const teaser = parDate.slice(0, 3);

    bandeauAgendaEl.innerHTML = teaser.map(function(ev, i){
      const mois = fmtMois.format(ev.date).replace(".", "");
      return '<button class="bandeau-chip" type="button" data-i="' + i + '" aria-expanded="false"'
        + ' aria-label="' + fmtDateLongue.format(ev.date) + ' — ' + ev.titre + '">'
        +   '<span class="bev-sem">' + fmtJour.format(ev.date) + '</span>'
        +   '<span class="bev-jour">' + ev.date.getDate() + '</span>'
        +   '<span class="bev-mois">' + mois + '</span>'
        +   '<span class="bev-pastille pastille ' + ev.lieu + '" aria-hidden="true"></span>'
        + '</button>';
    }).join("");

    const chips = bandeauAgendaEl.querySelectorAll(".bandeau-chip");
    let ouvert = -1;
    function afficherApercu(i){
      const ev = teaser[i];
      apercuEl.innerHTML =
          '<span class="apercu-lieu ev-lieu ' + ev.lieu + '"><span class="pastille ' + ev.lieu + '"></span>' + nomsLieux[ev.lieu] + '</span>'
        + '<p class="apercu-titre-ev">' + ev.titre + '</p>'
        + '<p class="apercu-desc">' + ev.desc + '</p>'
        + '<p class="apercu-quand">' + fmtDateLongue.format(ev.date) + ' · ' + ev.heure
        +   (ev.resa ? ' · sur réservation' : '') + '</p>'
        + '<a class="apercu-lien" href="/agenda">Voir tout l\'agenda <span aria-hidden="true">&rarr;</span></a>';
      apercuEl.hidden = false;
    }
    chips.forEach(function(chip, i){
      chip.addEventListener("click", function(){
        const memeChip = (ouvert === i);
        chips.forEach(function(c){ c.classList.remove("actif"); c.setAttribute("aria-expanded", "false"); });
        if(memeChip){                   // deuxième clic : on referme
          apercuEl.hidden = true;
          ouvert = -1;
          return;
        }
        chip.classList.add("actif");
        chip.setAttribute("aria-expanded", "true");
        afficherApercu(i);
        ouvert = i;
      });
    });
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

/* ============================================================
   CATALOGUE — filtres, recherche et volet de détail
   ============================================================ */
(function catalogue() {
  const grille = document.getElementById("refGrille");
  if (!grille) return;

  const cartes = Array.from(grille.querySelectorAll(".ref-carte"));
  const filtres = Array.from(document.querySelectorAll(".ref-filtres .filtre"));
  const champ = document.getElementById("refCherche");
  const compte = document.getElementById("refCompte");
  const vide = document.getElementById("refVide");
  const volet = document.getElementById("refVolet");
  const voletContenu = document.getElementById("refVoletContenu");

  let categorie = "tous";
  let requete = "";

  // 255 fiches d'un coup, c'est 45 000 px de page : le rendu s'effondre, surtout sur
  // mobile. Tout reste dans le HTML (donc indexable), mais on n'en affiche qu'une
  // tranche à la fois, agrandie au clic.
  const PAS = 48;
  let limite = PAS;

  const plus = document.createElement("button");
  plus.type = "button";
  plus.className = "btn ref-plus";
  plus.addEventListener("click", () => {
    limite += PAS;
    appliquer(true);
  });
  grille.insertAdjacentElement("afterend", plus);

  // « Château Lévêque » et « chateau leveque » doivent se trouver
  const sansAccent = (t) =>
    t.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

  function appliquer(garderLaPosition) {
    const avant = window.scrollY;
    let correspondances = 0;
    const mots = requete.split(/\s+/).filter(Boolean);
    cartes.forEach((carte) => {
      const okType = categorie === "tous" || carte.dataset.type === categorie;
      const texte = carte.dataset.cherche || "";
      const okTexte = mots.every((m) => texte.includes(m));
      const correspond = okType && okTexte;
      if (correspond) correspondances++;
      carte.classList.toggle("cache", !correspond || correspondances > limite);
    });
    if (compte) {
      compte.textContent =
        correspondances + (correspondances > 1 ? " références" : " référence");
    }
    if (vide) vide.hidden = correspondances > 0;

    const reste = correspondances - Math.min(limite, correspondances);
    plus.hidden = reste <= 0;
    plus.textContent =
      "Voir " + Math.min(reste, PAS) + " références de plus";
    if (garderLaPosition) window.scrollTo(0, avant);
  }

  function reinitialiser() {
    limite = PAS;
    appliquer();
  }

  filtres.forEach((bouton) => {
    bouton.addEventListener("click", () => {
      filtres.forEach((b) => b.classList.remove("actif"));
      bouton.classList.add("actif");
      categorie = bouton.dataset.ref;
      reinitialiser();
    });
  });

  if (champ) {
    let minuteur;
    champ.addEventListener("input", () => {
      clearTimeout(minuteur);
      minuteur = setTimeout(() => {
        requete = sansAccent(champ.value.trim());
        reinitialiser();
      }, 140);
    });
  }

  // ----- volet de détail -----
  let declencheur = null;

  function ouvrir(carte) {
    if (!volet || !voletContenu) return;
    const visuel = carte.querySelector(".ref-visuel");
    const nom = carte.querySelector(".ref-nom");
    const domaine = carte.querySelector(".ref-domaine");
    const badge = carte.querySelector(".b-type");
    const prix = carte.querySelector(".ref-prix");
    const detail = carte.querySelector(".ref-detail");

    voletContenu.innerHTML =
      '<div class="fdv-tete">' +
        (visuel ? '<div class="fdv-photo">' + visuel.innerHTML + "</div>" : "") +
        "<div>" +
          (badge ? badge.outerHTML : "") +
          (nom ? '<h2 class="fdv-titre" id="refVoletTitre">' + nom.textContent + "</h2>" : "") +
          (domaine ? '<p class="fdv-domaine">' + domaine.textContent + "</p>" : "") +
          (prix ? '<p class="fdv-prix">' + prix.textContent + "</p>" : "") +
        "</div>" +
      "</div>" +
      (detail ? detail.innerHTML : "");

    // la photo du volet n'est plus paresseuse : elle doit s'afficher tout de suite
    const img = voletContenu.querySelector("img");
    if (img) img.loading = "eager";

    volet.hidden = false;
    document.body.style.overflow = "hidden";
    const fermer = volet.querySelector("[data-fermer]");
    if (fermer) fermer.focus();
  }

  function fermerVolet() {
    if (!volet || volet.hidden) return;
    volet.hidden = true;
    voletContenu.innerHTML = "";
    document.body.style.overflow = "";
    if (declencheur) {
      declencheur.focus();
      declencheur = null;
    }
  }

  grille.addEventListener("click", (e) => {
    const bouton = e.target.closest(".ref-ouvrir");
    if (!bouton) return;
    declencheur = bouton;
    ouvrir(bouton.closest(".ref-carte"));
  });

  if (volet) {
    volet.addEventListener("click", (e) => {
      if (e.target.closest("[data-fermer]")) fermerVolet();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") fermerVolet();
    });
  }

  // ?type=rouge (ou #rouge) ouvre une catégorie, ?q=... ouvre une référence :
  // c'est ce que visent les bouteilles de l'étagère, sur l'accueil et la page cave
  const parametres = new URLSearchParams(location.search);
  const depart = parametres.get("type") || location.hash.replace("#", "");
  const cherchee = parametres.get("q");
  const boutonDepart = depart && filtres.find((b) => b.dataset.ref === depart);

  if (cherchee && champ) {
    champ.value = cherchee;
    requete = sansAccent(cherchee.trim());
  }
  if (boutonDepart) {
    boutonDepart.click();
  } else {
    appliquer();
  }
  if (cherchee) {
    const barre = document.getElementById("refBarre");
    if (barre) {
      barre.scrollIntoView({ block: "start" });
      window.scrollBy(0, -90);
    }
  }
})();
